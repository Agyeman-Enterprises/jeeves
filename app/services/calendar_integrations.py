from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover - optional dependency
    Request = None  # type: ignore
    Credentials = None  # type: ignore
    build = None  # type: ignore

try:
    import msal
except ImportError:  # pragma: no cover - optional dependency
    msal = None  # type: ignore

LOGGER = logging.getLogger(__name__)

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
]

GRAPH_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_CALENDAR_URL = "https://graph.microsoft.com/v1.0/me/calendar"


class CalendarProviderError(RuntimeError):
    pass


@dataclass
class CalendarEvent:
    id: str
    title: str
    start: datetime
    end: datetime
    location: str
    description: str
    account: str
    provider: str
    calendar: str
    attendees: List[str]
    is_all_day: bool

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "description": self.description,
            "account": self.account,
            "provider": self.provider,
            "calendar": self.calendar,
            "attendees": ",".join(self.attendees),
            "is_all_day": str(self.is_all_day),
        }

    def overlaps_with(self, other: CalendarEvent) -> bool:
        """Check if this event overlaps with another event."""
        if self.is_all_day or other.is_all_day:
            return False  # All-day events don't conflict
        return self.start < other.end and self.end > other.start


@dataclass
class OAuthCredentials:
    address: str
    client_id: str
    client_secret: str
    refresh_token: str


class BaseCalendarProvider:
    name = "calendar"
    _permanently_failed = False  # set True after first unrecoverable error

    def __init__(self, credentials: OAuthCredentials) -> None:
        self.credentials = credentials

    def get_events(
        self, start_date: date, end_date: date
    ) -> List[CalendarEvent]:
        raise NotImplementedError

    def get_todays_events(self) -> List[CalendarEvent]:
        today = date.today()
        return self.get_events(today, today)

    def search_events(self, query: str, days_ahead: int = 30) -> List[CalendarEvent]:
        end_date = date.today() + timedelta(days=days_ahead)
        events = self.get_events(date.today(), end_date)
        query_lower = query.lower()
        return [
            event
            for event in events
            if query_lower in event.title.lower()
            or query_lower in event.description.lower()
            or query_lower in event.location.lower()
        ]

    def get_free_busy(
        self, start: datetime, end: datetime
    ) -> List[tuple[datetime, datetime]]:
        """Return list of (start, end) tuples for busy periods."""
        events = self.get_events(start.date(), end.date())
        busy = []
        for event in events:
            if not event.is_all_day and event.start >= start and event.end <= end:
                busy.append((event.start, event.end))
        return busy


class GoogleCalendarProvider(BaseCalendarProvider):
    name = "google_calendar"

    def __init__(self, credentials: OAuthCredentials) -> None:
        super().__init__(credentials)
        self._service = None

    def _service_client(self):
        if self._service:
            return self._service
        if not Credentials or not Request or not build:
            raise CalendarProviderError(
                "google-api-python-client and google-auth libraries are required. "
                "Install with: pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib"
            )
        if not self.credentials.client_secret:
            raise CalendarProviderError(
                "Google Calendar: GOOGLE_DRIVE_CLIENT_SECRET not set. "
                "Run scripts/google_auth.py to authorize, or add the secret to .env. "
                "See config/OAUTH_SETUP.md for instructions."
            )
        creds = Credentials(
            token=None,
            refresh_token=self.credentials.refresh_token,
            client_id=self.credentials.client_id,
            client_secret=self.credentials.client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=CALENDAR_SCOPES,
        )
        creds.refresh(Request())
        self._service = build("calendar", "v3", credentials=creds)
        return self._service

    def get_events(
        self, start_date: date, end_date: date
    ) -> List[CalendarEvent]:
        try:
            service = self._service_client()
            time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
            time_max = (
                datetime.combine(end_date, datetime.max.time()).isoformat() + "Z"
            )
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=250,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            result = []
            for event in events:
                start_data = event.get("start", {})
                end_data = event.get("end", {})
                start_str = start_data.get("dateTime") or start_data.get("date")
                end_str = end_data.get("dateTime") or end_data.get("date")
                is_all_day = "date" in start_data
                if is_all_day:
                    start_dt = datetime.fromisoformat(start_str).replace(
                        tzinfo=timezone.utc
                    )
                    end_dt = datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc)
                else:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                attendees = [
                    attendee.get("email", "")
                    for attendee in event.get("attendees", [])
                ]
                result.append(
                    CalendarEvent(
                        id=event.get("id", ""),
                        title=event.get("summary", "No Title"),
                        start=start_dt,
                        end=end_dt,
                        location=event.get("location", ""),
                        description=event.get("description", ""),
                        account=self.credentials.address,
                        provider="google",
                        calendar="primary",
                        attendees=attendees,
                        is_all_day=is_all_day,
                    )
                )
            return result
        except Exception as exc:
            LOGGER.exception("Failed to fetch Google Calendar events: %s", exc)
            raise CalendarProviderError(f"Google Calendar API error: {exc}") from exc


class OutlookCalendarProvider(BaseCalendarProvider):
    name = "outlook_calendar"

    def __init__(self, credentials: OAuthCredentials) -> None:
        super().__init__(credentials)
        self._access_token = None
        self._token_expires = None

    def _get_access_token(self) -> str:
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token
        if not msal:
            raise CalendarProviderError(
                "msal library is required. Install with: pip install msal"
            )
        app = msal.ConfidentialClientApplication(
            client_id=self.credentials.client_id,
            client_credential=self.credentials.client_secret,
            authority="https://login.microsoftonline.com/common",
        )
        result = app.acquire_token_by_refresh_token(
            refresh_token=self.credentials.refresh_token,
            scopes=["https://graph.microsoft.com/Calendars.Read"],
        )
        if "access_token" not in result:
            raise CalendarProviderError(
                f"Failed to refresh Outlook token: {result.get('error_description', 'Unknown error')}"
            )
        self._access_token = result["access_token"]
        expires_in = result.get("expires_in", 3600)
        self._token_expires = datetime.now() + timedelta(seconds=expires_in - 300)
        return self._access_token

    def get_events(
        self, start_date: date, end_date: date
    ) -> List[CalendarEvent]:
        try:
            import requests

            token = self._get_access_token()
            time_min = start_date.isoformat() + "T00:00:00Z"
            time_max = end_date.isoformat() + "T23:59:59Z"
            url = f"{GRAPH_CALENDAR_URL}/events"
            params = {
                "$filter": f"start/dateTime ge '{time_min}' and end/dateTime le '{time_max}'",
                "$orderby": "start/dateTime",
                "$top": 250,
            }
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            events = data.get("value", [])
            result = []
            for event in events:
                start_str = event.get("start", {}).get("dateTime", "")
                end_str = event.get("end", {}).get("dateTime", "")
                is_all_day = event.get("isAllDay", False)
                if not start_str or not end_str:
                    continue
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                attendees = [
                    attendee.get("emailAddress", {}).get("address", "")
                    for attendee in event.get("attendees", [])
                ]
                result.append(
                    CalendarEvent(
                        id=event.get("id", ""),
                        title=event.get("subject", "No Title"),
                        start=start_dt,
                        end=end_dt,
                        location=event.get("location", {}).get("displayName", ""),
                        description=event.get("bodyPreview", ""),
                        account=self.credentials.address,
                        provider="outlook",
                        calendar="primary",
                        attendees=attendees,
                        is_all_day=is_all_day,
                    )
                )
            return result
        except Exception as exc:
            LOGGER.exception("Failed to fetch Outlook Calendar events: %s", exc)
            raise CalendarProviderError(f"Outlook Calendar API error: {exc}") from exc


class CalendarIntegrationManager:
    """Manages multiple calendar providers and merges their events."""

    def __init__(self) -> None:
        self.providers: List[BaseCalendarProvider] = []
        self._load_from_env()

    @staticmethod
    def _real(value: Optional[str]) -> bool:
        """Return True only if value is a real credential (non-empty, not an inline .env comment)."""
        return bool(value) and not value.startswith("#")

    def _load_from_env(self) -> None:
        """Auto-enable providers based on .env credentials."""
        # Load Gmail/Google Calendar accounts (GMAIL_1_*, GMAIL_2_*, etc.)
        idx = 1
        while True:
            address = os.getenv(f"GMAIL_{idx}_ADDRESS")
            if not address or address.startswith("#"):
                break
            client_id = os.getenv(f"GMAIL_{idx}_CLIENT_ID")
            client_secret = os.getenv(f"GMAIL_{idx}_CLIENT_SECRET")
            refresh_token = os.getenv(f"GMAIL_{idx}_REFRESH_TOKEN")
            if self._real(client_id) and self._real(client_secret) and self._real(refresh_token):
                try:
                    creds = OAuthCredentials(
                        address=address,
                        client_id=client_id,
                        client_secret=client_secret,
                        refresh_token=refresh_token,
                    )
                    provider = GoogleCalendarProvider(creds)
                    self.providers.append(provider)
                    LOGGER.info("Enabled Google Calendar for %s", address)
                except Exception as exc:
                    LOGGER.warning("Failed to enable Google Calendar for %s: %s", address, exc)
            idx += 1

        # Also try loading from the token file (google_drive_tokens.json has calendar.readonly scope)
        self._try_load_from_token_file()

        # Load Outlook accounts (OUTLOOK_1_*, OUTLOOK_2_*, etc.)
        idx = 1
        while True:
            address = os.getenv(f"OUTLOOK_{idx}_ADDRESS")
            if not address or address.startswith("#"):
                break
            client_id = os.getenv(f"OUTLOOK_{idx}_CLIENT_ID")
            client_secret = os.getenv(f"OUTLOOK_{idx}_CLIENT_SECRET")
            refresh_token = os.getenv(f"OUTLOOK_{idx}_REFRESH_TOKEN")
            if self._real(client_id) and self._real(client_secret) and self._real(refresh_token):
                try:
                    creds = OAuthCredentials(
                        address=address,
                        client_id=client_id,
                        client_secret=client_secret,
                        refresh_token=refresh_token,
                    )
                    provider = OutlookCalendarProvider(creds)
                    self.providers.append(provider)
                    LOGGER.info("Enabled Outlook Calendar for %s", address)
                except Exception as exc:
                    LOGGER.warning("Failed to enable Outlook Calendar for %s: %s", address, exc)
            idx += 1

    def _try_load_from_token_file(self) -> None:
        """Load Google Calendar from the shared token file if it has calendar.readonly scope.

        This works alongside the GMAIL_1_* env var pattern, using the token file created
        when Google Drive / Gmail OAuth was set up. Requires GOOGLE_DRIVE_CLIENT_SECRET for
        auto-refresh (the token file's access_token expires hourly; the refresh_token is permanent).
        """
        tokens_path = Path(
            os.getenv("GOOGLE_DRIVE_TOKENS_PATH", "config/google_drive_tokens.json")
        )
        client_id = os.getenv("GOOGLE_DRIVE_CLIENT_ID") or os.getenv("GMAIL_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET") or os.getenv("GMAIL_CLIENT_SECRET")

        if not tokens_path.exists() or not client_id:
            return

        try:
            with tokens_path.open(encoding="utf-8") as f:
                token_data = json.load(f)

            scopes = token_data.get("scope", "")
            if "calendar.readonly" not in scopes:
                return

            refresh_token = token_data.get("refresh_token", "")
            if not refresh_token:
                return

            # Avoid duplicate: skip if this refresh_token is already loaded via GMAIL_1_*
            for p in self.providers:
                if (
                    hasattr(p, "credentials")
                    and getattr(p.credentials, "refresh_token", "") == refresh_token
                ):
                    return

            address = os.getenv("GMAIL_1_ADDRESS", "isaalia@gmail.com")
            creds = OAuthCredentials(
                address=address,
                client_id=client_id,
                client_secret=client_secret or "",
                refresh_token=refresh_token,
            )
            provider = GoogleCalendarProvider(creds)
            self.providers.append(provider)
            LOGGER.info("Google Calendar enabled for %s", address)
        except Exception as exc:
            LOGGER.warning("Google Calendar load error: %s", exc)

    def get_all_events(
        self, start_date: date, end_date: date
    ) -> List[CalendarEvent]:
        """Fetch events from all enabled providers and merge them."""
        all_events = []
        for provider in self.providers:
            if provider._permanently_failed:
                continue
            try:
                events = provider.get_events(start_date, end_date)
                all_events.extend(events)
            except Exception as exc:
                err_str = str(exc)
                if any(k in err_str for k in ("invalid_client", "Unauthorized", "401", "invalid_grant")):
                    provider._permanently_failed = True
                LOGGER.warning("Provider %s failed: %s", provider.name, exc)
        all_events.sort(key=lambda e: e.start)
        return all_events

    def get_todays_events(self) -> List[CalendarEvent]:
        today = date.today()
        return self.get_all_events(today, today)

    def search_events(self, query: str, days_ahead: int = 30) -> List[CalendarEvent]:
        """Search across all calendars."""
        end_date = date.today() + timedelta(days=days_ahead)
        events = self.get_all_events(date.today(), end_date)
        query_lower = query.lower()
        return [
            event
            for event in events
            if query_lower in event.title.lower()
            or query_lower in event.description.lower()
            or query_lower in event.location.lower()
        ]

    def detect_conflicts(self, events: List[CalendarEvent]) -> List[tuple[CalendarEvent, CalendarEvent]]:
        """Detect overlapping events (conflicts)."""
        conflicts = []
        for i, event1 in enumerate(events):
            for event2 in events[i + 1 :]:
                if event1.overlaps_with(event2):
                    conflicts.append((event1, event2))
        return conflicts

    def find_free_slots(
        self, target_date: date, duration_minutes: int = 60, work_start: int = 9, work_end: int = 17
    ) -> List[tuple[datetime, datetime]]:
        """Find available time slots on a given date."""
        events = self.get_all_events(target_date, target_date)
        # Convert to local timezone (PST/PDT = UTC-8 or UTC-7)
        tz_offset = timedelta(hours=-8)  # Simplified - should use proper timezone
        day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc) + timedelta(hours=work_start) + tz_offset
        day_end = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc) + timedelta(hours=work_end) + tz_offset
        busy_periods = [(e.start, e.end) for e in events if not e.is_all_day]
        busy_periods.sort()
        free_slots = []
        current = day_start
        for busy_start, busy_end in busy_periods:
            if current < busy_start:
                slot_end = min(busy_start, current + timedelta(minutes=duration_minutes))
                if (slot_end - current).total_seconds() >= duration_minutes * 60:
                    free_slots.append((current, slot_end))
            current = max(current, busy_end)
        if current < day_end:
            slot_end = min(day_end, current + timedelta(minutes=duration_minutes))
            if (slot_end - current).total_seconds() >= duration_minutes * 60:
                free_slots.append((current, slot_end))
        return free_slots

