"""
Proactive Agent — Surfaces time-sensitive action items from email and calendar.

Scans Gmail and Google Calendar for:
  - Bills due / invoices / auto-payments
  - License renewals (DEA, medical license, CME credits)
  - Upcoming appointments
  - Subscription renewals
  - Anything tagged "action required" or "deadline"

Used in the daily morning briefing and responds to queries like:
  - "What do I need to take care of today?"
  - "Any bills due this week?"
  - "Do I have any renewals coming up?"
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.agents.base import AgentContext, AgentResponse, BaseAgent
from app.services.calendar_integrations import CalendarIntegrationManager
from app.services.email_integrations import EmailIntegrationManager, EmailMessage

LOGGER = logging.getLogger(__name__)

_KEYWORDS = [
    "proactive", "action", "todo", "to-do", "to do",
    "bill", "bills", "invoice", "payment", "due",
    "renewal", "renew", "license", "dea", "cme",
    "expir", "subscription", "remind", "reminder",
    "deadline", "urgent", "alert", "notify",
    "what do i need", "what should i", "what's coming",
]

# Gmail search queries → category label
_EMAIL_SCAN_QUERIES: List[tuple[str, str]] = [
    (
        'subject:(invoice OR "payment due" OR "amount due" OR "past due" OR "your bill" OR "auto-pay") newer_than:14d',
        "bill",
    ),
    (
        'subject:(renewal OR renew OR expiring OR expired OR "DEA" OR "medical license" OR "CME") newer_than:30d',
        "renewal",
    ),
    (
        'subject:("action required" OR "response required" OR overdue OR deadline) newer_than:14d',
        "urgent",
    ),
    (
        'subject:(appointment OR "your visit" OR "appointment reminder" OR "appointment confirmation") newer_than:7d',
        "appointment",
    ),
]

_RENEWAL_KEYWORDS = ["dea", "medical license", "license renewal", "cme", "cme credit", "expir", "renew"]
_BILL_KEYWORDS = ["invoice", "payment due", "amount due", "past due", "auto-pay", "autopay", "your bill", "statement", "overdue"]
_APPOINTMENT_KEYWORDS = ["appointment", "your visit", "appointment reminder", "appointment confirmation"]
_URGENT_KEYWORDS = ["action required", "urgent", "asap", "response required", "deadline", "overdue"]


def _categorize_message(msg: EmailMessage) -> str:
    text = f"{msg.subject} {msg.snippet}".lower()
    if any(k in text for k in _RENEWAL_KEYWORDS):
        return "renewal"
    if any(k in text for k in _URGENT_KEYWORDS):
        return "urgent"
    if any(k in text for k in _BILL_KEYWORDS):
        return "bill"
    if any(k in text for k in _APPOINTMENT_KEYWORDS):
        return "appointment"
    return "other"


def _fmt_date(d: date) -> str:
    today = date.today()
    delta = (d - today).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "tomorrow"
    if delta < 0:
        return f"{abs(delta)} day(s) ago"
    if delta <= 7:
        return d.strftime("%A")
    return d.strftime("%b %d")


class ProactiveAgent(BaseAgent):
    """Surfaces time-sensitive action items from Gmail and Google Calendar."""

    name = "ProactiveAgent"
    description = (
        "Scans email and calendar for bills due, license renewals, "
        "upcoming appointments, and urgent action items."
    )
    capabilities = [
        "Find bills and invoices due",
        "Surface license and DEA renewal reminders",
        "List upcoming appointments",
        "Flag urgent emails requiring action",
        "Provide daily action briefing",
    ]

    def __init__(self, database=None) -> None:
        super().__init__()
        self.database = database
        self._calendar = CalendarIntegrationManager()
        self._email = EmailIntegrationManager()

    def supports(self, query: str) -> bool:
        q = query.lower()
        return any(kw in q for kw in _KEYWORDS)

    def handle(self, query: str, context: Optional[AgentContext] = None) -> AgentResponse:
        q = query.lower()

        # Route to specific category if query is focused
        if any(kw in q for kw in ["bill", "invoice", "payment", "subscription"]):
            return self._handle_bills()
        if any(kw in q for kw in ["renewal", "renew", "license", "dea", "cme", "expir"]):
            return self._handle_renewals()
        if any(kw in q for kw in ["appointment", "visit", "calendar", "schedule"]):
            return self._handle_appointments()
        if any(kw in q for kw in ["urgent", "action", "deadline", "todo", "to-do"]):
            return self._handle_urgent()

        # Full briefing
        return self._handle_full_briefing()

    # ── Full briefing ────────────────────────────────────────────────────────

    def _handle_full_briefing(self) -> AgentResponse:
        """Build a complete action briefing from all sources."""
        sections: List[str] = []
        all_data: Dict[str, Any] = {}

        # Calendar
        cal_items = self._get_upcoming_appointments(days=14)
        all_data["appointments"] = cal_items
        if cal_items:
            sections.append(f"**Upcoming appointments ({len(cal_items)}):**")
            for item in cal_items[:5]:
                sections.append(f"  • {_fmt_date(item['date'])} — {item['title']}")

        # Email alerts (only if providers configured)
        if self._email.has_providers():
            alerts = self._scan_email_alerts()
            all_data["email_alerts"] = alerts

            bills = [a for a in alerts if a["category"] == "bill"]
            renewals = [a for a in alerts if a["category"] == "renewal"]
            urgent = [a for a in alerts if a["category"] == "urgent"]

            if bills:
                sections.append(f"\n**Bills / payments due ({len(bills)}):**")
                for b in bills[:4]:
                    sections.append(f"  • {b['subject']} — from {b['sender']}")

            if renewals:
                sections.append(f"\n**Renewals / expirations ({len(renewals)}):**")
                for r in renewals[:4]:
                    sections.append(f"  • {r['subject']} — from {r['sender']}")

            if urgent:
                sections.append(f"\n**Action required ({len(urgent)}):**")
                for u in urgent[:3]:
                    sections.append(f"  • {u['subject']} — from {u['sender']}")
        else:
            sections.append(
                "\n_Email alerts not configured. Add GOOGLE_DRIVE_CLIENT_SECRET to .env "
                "to enable Gmail scanning. See config/OAUTH_SETUP.md._"
            )

        if not sections:
            return AgentResponse(
                agent=self.name,
                content=(
                    "No action items found. "
                    "Connect Google Calendar and Gmail for proactive monitoring.\n"
                    "See config/OAUTH_SETUP.md for setup instructions."
                ),
                data=all_data,
                status="warning",
            )

        return AgentResponse(
            agent=self.name,
            content="\n".join(sections),
            data=all_data,
        )

    # ── Category handlers ────────────────────────────────────────────────────

    def _handle_bills(self) -> AgentResponse:
        if not self._email.has_providers():
            return self._not_configured_response("bill scanning")
        alerts = self._scan_email_alerts()
        bills = [a for a in alerts if a["category"] == "bill"]
        if not bills:
            return AgentResponse(agent=self.name, content="No bill or invoice emails found in the last 14 days.", data={"bills": []})
        lines = [f"**Bills / payments due ({len(bills)}):**"]
        for b in bills[:8]:
            lines.append(f"  • {b['subject']}\n    From: {b['sender']}")
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"bills": bills})

    def _handle_renewals(self) -> AgentResponse:
        if not self._email.has_providers():
            return self._not_configured_response("renewal scanning")
        alerts = self._scan_email_alerts()
        renewals = [a for a in alerts if a["category"] == "renewal"]
        if not renewals:
            return AgentResponse(agent=self.name, content="No renewal or expiration emails found in the last 30 days.", data={"renewals": []})
        lines = [f"**Renewals / expirations ({len(renewals)}):**"]
        for r in renewals[:8]:
            lines.append(f"  • {r['subject']}\n    From: {r['sender']}")
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"renewals": renewals})

    def _handle_appointments(self) -> AgentResponse:
        items = self._get_upcoming_appointments(days=14)
        if not items:
            if not self._calendar.providers:
                return self._not_configured_response("calendar")
            return AgentResponse(agent=self.name, content="No upcoming appointments in the next 14 days.", data={"appointments": []})
        lines = [f"**Upcoming appointments ({len(items)}):**"]
        for item in items[:10]:
            loc = f" @ {item['location']}" if item.get("location") else ""
            lines.append(f"  • {_fmt_date(item['date'])} {item.get('time', '')} — {item['title']}{loc}")
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"appointments": items})

    def _handle_urgent(self) -> AgentResponse:
        if not self._email.has_providers():
            return self._not_configured_response("urgent email scanning")
        alerts = self._scan_email_alerts()
        urgent = [a for a in alerts if a["category"] in ("urgent", "renewal", "bill")]
        if not urgent:
            return AgentResponse(agent=self.name, content="No urgent action items found.", data={"urgent": []})
        lines = [f"**Action items ({len(urgent)}):**"]
        for u in urgent[:8]:
            lines.append(f"  • [{u['category'].upper()}] {u['subject']} — {u['sender']}")
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"urgent": urgent})

    # ── Data fetchers ────────────────────────────────────────────────────────

    def _get_upcoming_appointments(self, days: int = 14) -> List[Dict[str, Any]]:
        """Pull upcoming events from all configured calendar providers."""
        if not self._calendar.providers:
            return []
        try:
            today = date.today()
            end = today + timedelta(days=days)
            events = self._calendar.get_all_events(today, end)
            result = []
            for ev in events:
                result.append({
                    "title": ev.title,
                    "date": ev.start.date(),
                    "time": (ev.start.strftime("%I:%M %p").lstrip("0") or "12:00 AM") if not ev.is_all_day else "All day",
                    "location": ev.location,
                    "provider": ev.provider,
                    "account": ev.account,
                })
            return result
        except Exception as exc:
            LOGGER.warning("Failed to fetch calendar events: %s", exc)
            return []

    def _scan_email_alerts(self) -> List[Dict[str, Any]]:
        """Search Gmail for time-sensitive emails across all alert categories."""
        alerts: List[Dict[str, Any]] = []
        if not self._email.has_providers():
            return alerts

        # Search for all alert keywords at once (broad then categorize)
        all_keywords = (
            "invoice OR 'payment due' OR renewal OR 'DEA renewal' OR "
            "'medical license' OR 'action required' OR 'appointment reminder' OR "
            "overdue OR expiring OR 'CME credit'"
        )
        try:
            messages = self._email.search(
                query=f"({all_keywords}) newer_than:30d",
                max_results=30,
            )
            for msg in messages:
                category = _categorize_message(msg)
                alerts.append({
                    "category": category,
                    "subject": msg.subject,
                    "sender": msg.sender,
                    "received": msg.received.isoformat(),
                    "snippet": msg.snippet[:200],
                    "account": msg.account,
                    "id": msg.id,
                })
        except Exception as exc:
            LOGGER.warning("Email alert scan failed: %s", exc)

        return alerts

    def _not_configured_response(self, feature: str) -> AgentResponse:
        return AgentResponse(
            agent=self.name,
            content=(
                f"Google credentials needed for {feature}.\n\n"
                "**To connect:**\n"
                "1. Get your CLIENT_SECRET from Google Cloud Console\n"
                "   → console.cloud.google.com → APIs & Services → Credentials → OAuth 2.0 Client IDs\n"
                "2. Add to JARVIS .env:\n"
                "   GOOGLE_DRIVE_CLIENT_SECRET=your-secret\n"
                "   GMAIL_CLIENT_SECRET=your-secret\n"
                "   GMAIL_1_CLIENT_SECRET=your-secret\n"
                "3. Restart JARVIS — it will auto-refresh from the stored refresh token.\n\n"
                "For full step-by-step instructions: config/OAUTH_SETUP.md"
            ),
            status="warning",
            data={},
        )

    def get_daily_briefing_data(self) -> Dict[str, Any]:
        """Called by the morning briefing scheduler — returns structured action data."""
        appointments = self._get_upcoming_appointments(days=7)
        email_alerts = self._scan_email_alerts() if self._email.has_providers() else []
        return {
            "appointments": appointments,
            "bills": [a for a in email_alerts if a["category"] == "bill"],
            "renewals": [a for a in email_alerts if a["category"] == "renewal"],
            "urgent": [a for a in email_alerts if a["category"] == "urgent"],
            "calendar_configured": bool(self._calendar.providers),
            "email_configured": self._email.has_providers(),
        }
