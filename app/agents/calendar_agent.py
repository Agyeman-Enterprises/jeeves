from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent
from app.services.calendar_integrations import (
    CalendarEvent,
    CalendarIntegrationManager,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEZONE = os.getenv("PRIMARY_TIMEZONE", "America/Los_Angeles")
FALLBACK_DATA_PATH = Path("data") / "sample_calendar.json"


@dataclass
class CalendarEventSimple:
    """Simplified event for backward compatibility."""
    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    provider: str = "local"
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location or "",
            "provider": self.provider,
            "description": self.description or "",
        }


class CalendarAgent(BaseAgent):
    """Aggregates schedules across Google Calendar and Outlook Calendar."""

    description = "Shows today's schedule, finds free time, and detects conflicts across all calendars."
    capabilities = [
        "Show today's schedule",
        "Get upcoming events",
        "Find free time slots",
        "Detect conflicts",
        "Search events by keyword",
    ]

    def __init__(self, database=None) -> None:
        super().__init__()
        self.database = database
        self.integration_manager = CalendarIntegrationManager()
        self._load_sample_data()

    def _load_sample_data(self) -> None:
        """Load sample calendar data for fallback."""
        self._sample_events: List[CalendarEvent] = []
        if not FALLBACK_DATA_PATH.exists():
            LOGGER.info("Sample calendar data not found at %s", FALLBACK_DATA_PATH)
            return
        try:
            data = json.loads(FALLBACK_DATA_PATH.read_text(encoding="utf-8"))
            events_data = data.get("events", [])
            for entry in events_data:
                try:
                    start_str = entry.get("start", "")
                    end_str = entry.get("end", "")
                    if not start_str or not end_str:
                        continue
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                    self._sample_events.append(
                        CalendarEvent(
                            id=entry.get("id", ""),
                            title=entry.get("title", "No Title"),
                            start=start_dt,
                            end=end_dt,
                            location=entry.get("location", ""),
                            description=entry.get("description", ""),
                            account=entry.get("account", "sample"),
                            provider=entry.get("provider", "sample"),
                            calendar=entry.get("calendar", "primary"),
                            attendees=entry.get("attendees", []),
                            is_all_day=entry.get("is_all_day", False),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed calendar entry: %s", exc)
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", FALLBACK_DATA_PATH)

    def supports(self, query: str) -> bool:
        lowered = query.lower()
        keywords = [
            "calendar",
            "schedule",
            "meeting",
            "appointment",
            "free",
            "available",
            "busy",
            "conflict",
        ]
        return any(word in lowered for word in keywords)

    def handle(self, query: str, context: Optional[Dict[str, str]] = None) -> AgentResponse:
        lowered = query.lower()
        if "today" in lowered or "schedule" in lowered:
            return self._handle_todays_schedule()
        elif "free" in lowered or "available" in lowered:
            return self._handle_free_slots(query)
        elif "conflict" in lowered:
            return self._handle_conflicts()
        elif "upcoming" in lowered or "week" in lowered:
            days = 7
            if "week" in lowered:
                days = 7
            elif "month" in lowered:
                days = 30
            return self._handle_upcoming(days)
        else:
            return self._handle_todays_schedule()

    def get_todays_schedule(self) -> Dict:
        """Get today's schedule with conflicts and free time."""
        today = date.today()
        events = self._get_events(today, today)
        conflicts = self.integration_manager.detect_conflicts(events)
        free_slots = self.integration_manager.find_free_slots(today)
        return {
            "date": today.isoformat(),
            "total_events": len(events),
            "events": [self._event_to_dict(e) for e in events],
            "conflicts": [
                {"event1": self._event_to_dict(c[0]), "event2": self._event_to_dict(c[1])}
                for c in conflicts
            ],
            "free_time": [
                {"start": s[0].isoformat(), "end": s[1].isoformat()} for s in free_slots
            ],
        }

    def get_upcoming(self, days: int = 7) -> Dict:
        """Get upcoming events summarized by day."""
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        events = self._get_events(start_date, end_date)
        by_day: Dict[str, List[Dict]] = {}
        for event in events:
            day_key = event.start.date().isoformat()
            if day_key not in by_day:
                by_day[day_key] = []
            by_day[day_key].append(self._event_to_dict(event))
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_events": len(events),
            "by_day": by_day,
        }

    def find_free_slots(
        self, target_date: date, duration_minutes: int = 60
    ) -> List[Dict]:
        """Find available time slots on a given date."""
        slots = self.integration_manager.find_free_slots(target_date, duration_minutes)
        return [{"start": s[0].isoformat(), "end": s[1].isoformat()} for s in slots]

    def check_conflicts(self) -> List[Dict]:
        """Check for conflicts across all calendars."""
        today = date.today()
        end_date = today + timedelta(days=7)
        events = self._get_events(today, end_date)
        conflicts = self.integration_manager.detect_conflicts(events)
        return [
            {"event1": self._event_to_dict(c[0]), "event2": self._event_to_dict(c[1])}
            for c in conflicts
        ]

    def search_events(self, query: str, days_ahead: int = 30) -> List[Dict]:
        """Search events by keyword."""
        events = self.integration_manager.search_events(query, days_ahead)
        return [self._event_to_dict(e) for e in events]

    # Internal helpers ---------------------------------------------------------
    def _get_events(self, start_date: date, end_date: date) -> List[CalendarEvent]:
        """Get events from integrations or fallback to sample data."""
        if self.integration_manager.providers:
            try:
                return self.integration_manager.get_all_events(start_date, end_date)
            except Exception as exc:
                LOGGER.warning("Failed to fetch from integrations, using sample data: %s", exc)
        return [
            e
            for e in self._sample_events
            if start_date <= e.start.date() <= end_date
        ]

    def _event_to_dict(self, event: CalendarEvent) -> Dict:
        """Convert CalendarEvent to dict for response."""
        return {
            "id": event.id,
            "title": event.title,
            "start": event.start.isoformat(),
            "end": event.end.isoformat(),
            "location": event.location,
            "description": event.description,
            "account": event.account,
            "provider": event.provider,
            "calendar": event.calendar,
            "attendees": event.attendees,
            "is_all_day": event.is_all_day,
        }

    def _handle_todays_schedule(self) -> AgentResponse:
        """Handle query for today's schedule."""
        schedule = self.get_todays_schedule()
        events = schedule["events"]
        if not events:
            return AgentResponse(
                agent=self.name,
                content="No events scheduled for today.",
                data=schedule,
            )
        lines = []
        for event in events:
            start_dt = datetime.fromisoformat(event["start"])
            end_dt = datetime.fromisoformat(event["end"])
            start_str = start_dt.strftime("%I:%M %p").lstrip("0")
            end_str = end_dt.strftime("%I:%M %p").lstrip("0")
            location = f" @ {event['location']}" if event.get("location") else ""
            lines.append(f"{start_str}-{end_str}: {event['title']}{location}")
        if schedule["conflicts"]:
            lines.append(f"WARNING: {len(schedule['conflicts'])} conflict(s) detected.")
        else:
            lines.append("OK: No conflicts detected today.")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data=schedule,
        )

    def _handle_free_slots(self, query: str) -> AgentResponse:
        """Handle query for free time."""
        target_date = date.today()
        if "tomorrow" in query.lower():
            target_date = date.today() + timedelta(days=1)
        duration = 60
        if "30" in query:
            duration = 30
        elif "15" in query:
            duration = 15
        slots = self.find_free_slots(target_date, duration)
        if not slots:
            return AgentResponse(
                agent=self.name,
                content=f"No free {duration}-minute slots found on {target_date.isoformat()}.",
                data={"slots": []},
            )
        lines = [f"Available {duration}-minute slots on {target_date.isoformat()}:"]
        for slot in slots:
            start_dt = datetime.fromisoformat(slot["start"])
            end_dt = datetime.fromisoformat(slot["end"])
            start_str = start_dt.strftime("%I:%M %p").lstrip("0")
            end_str = end_dt.strftime("%I:%M %p").lstrip("0")
            lines.append(f"  {start_str} - {end_str}")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"slots": slots},
        )

    def _handle_conflicts(self) -> AgentResponse:
        """Handle query for conflicts."""
        conflicts = self.check_conflicts()
        if not conflicts:
            return AgentResponse(
                agent=self.name,
                content="No conflicts detected in the next 7 days.",
                data={"conflicts": []},
            )
        lines = [f"Found {len(conflicts)} conflict(s):"]
        for conflict in conflicts:
            e1 = conflict["event1"]
            e2 = conflict["event2"]
            lines.append(f"  {e1['title']} ↔ {e2['title']}")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"conflicts": conflicts},
        )

    def _handle_upcoming(self, days: int) -> AgentResponse:
        """Handle query for upcoming events."""
        upcoming = self.get_upcoming(days)
        by_day = upcoming["by_day"]
        if not by_day:
            return AgentResponse(
                agent=self.name,
                content=f"No events in the next {days} days.",
                data=upcoming,
            )
        lines = [f"Upcoming events (next {days} days):"]
        for day_key in sorted(by_day.keys()):
            day_events = by_day[day_key]
            day_dt = datetime.fromisoformat(day_key).date()
            day_str = day_dt.strftime("%A, %B %d")
            lines.append(f"\n{day_str} ({len(day_events)} event(s)):")
            for event in day_events:
                start_dt = datetime.fromisoformat(event["start"])
                start_str = start_dt.strftime("%I:%M %p").lstrip("0")
                lines.append(f"  {start_str}: {event['title']}")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data=upcoming,
        )
