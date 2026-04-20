"""
competing_priorities.py — JARVIS Personal Life Layer

Aggregates all competing demands across:
  - Calendar events (today / tomorrow)
  - Personal reminders due
  - Enterprise alerts from NEXUS
  - Urgent emails

Returns a structured "here's your situation" summary that JARVIS surfaces to the
user with: "You have X and Y competing right now — what do you want to focus on?"

Called by:
  - The orchestrator when intent = "priorities" | "focus" | "what should I do"
  - The morning briefing
  - Direct API: GET /api/jarvis/priorities
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx

LOGGER = logging.getLogger("backend.services.competing_priorities")


@dataclass
class Priority:
    category: str            # "calendar", "reminder", "enterprise", "email"
    urgency: str             # "critical" | "high" | "medium" | "low"
    title: str
    detail: str
    source: str              # app/service name
    due_at: str | None = None


@dataclass
class PrioritiesReport:
    priorities: list[Priority] = field(default_factory=list)
    summary: str = ""
    decision_prompt: str = ""
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Helpers ──────────────────────────────────────────────────────────────────

def _nexus_get(path: str, timeout: int = 12) -> dict[str, Any]:
    nexus_url = os.getenv("NEXUS_URL", "http://localhost:3001")
    key = os.getenv("NEXUS_INTERNAL_KEY", "nexus_internal_key_change_me")
    try:
        resp = httpx.get(
            f"{nexus_url}{path}",
            headers={"Authorization": f"Bearer {key}"},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        LOGGER.debug("[Priorities] NEXUS get %s failed: %s", path, exc)
    return {}


def _nexus_post(path: str, payload: dict, timeout: int = 12) -> dict[str, Any]:
    nexus_url = os.getenv("NEXUS_URL", "http://localhost:3001")
    key = os.getenv("NEXUS_INTERNAL_KEY", "nexus_internal_key_change_me")
    try:
        resp = httpx.post(
            f"{nexus_url}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        LOGGER.debug("[Priorities] NEXUS post %s failed: %s", path, exc)
    return {}


# ── Collectors ────────────────────────────────────────────────────────────────

def _collect_calendar(tz_name: str) -> list[Priority]:
    """Pull today's calendar events from the calendar integration."""
    priorities: list[Priority] = []
    try:
        from app.services.calendar_integrations import CalendarIntegrationManager
        mgr = CalendarIntegrationManager()
        now = datetime.now()
        end = now + timedelta(hours=24)
        events = mgr.get_events(start=now, end=end, max_results=10)
        for evt in events or []:
            title = evt.get("summary") or evt.get("title") or "Untitled event"
            start_str = (evt.get("start") or {}).get("dateTime") or (evt.get("start") or {}).get("date") or ""
            urgency = "high" if start_str and start_str < (now + timedelta(hours=2)).isoformat() else "medium"
            priorities.append(Priority(
                category="calendar",
                urgency=urgency,
                title=title,
                detail=start_str,
                source="Google Calendar",
                due_at=start_str,
            ))
    except Exception as exc:
        LOGGER.debug("[Priorities] Calendar collect failed: %s", exc)
    return priorities


def _collect_enterprise_alerts() -> list[Priority]:
    """Pull critical alerts from NEXUS enterprise briefing."""
    priorities: list[Priority] = []
    try:
        data = _nexus_get("/api/enterprise/briefing")
        alerts = data.get("allAlerts", [])
        for alert in alerts[:5]:
            priorities.append(Priority(
                category="enterprise",
                urgency="high",
                title=str(alert),
                detail="From enterprise briefing",
                source="NEXUS",
            ))
    except Exception as exc:
        LOGGER.debug("[Priorities] Enterprise alerts failed: %s", exc)
    return priorities


def _collect_reminders() -> list[Priority]:
    """Get personal reminders that are due."""
    priorities: list[Priority] = []
    try:
        from app.services.personal_reminders import get_due_reminders
        for r in get_due_reminders():
            priorities.append(Priority(
                category="reminder",
                urgency="medium" if r.get("priority", 0) <= 0 else "high",
                title=r.get("title", "Reminder"),
                detail=r.get("message", ""),
                source="JARVIS",
            ))
    except Exception as exc:
        LOGGER.debug("[Priorities] Reminders collect failed: %s", exc)
    return priorities


def _collect_sentinel_risks() -> list[Priority]:
    """Pull active critical/high Sentinel FinOps risks as priorities."""
    priorities: list[Priority] = []
    try:
        from app.services.jarviscore_client import get_supabase_client
        sb = get_supabase_client(use_service_key=True)
        result = (
            sb.table("sentinel_risk_events")
            .select("id, entity_id, metric_key, severity, risk_type, zscore_at_detection")
            .in_("severity", ["critical", "high"])
            .eq("dismissed", False)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        rows = result.data or []
        entity_ids = list({r["entity_id"] for r in rows if r.get("entity_id")})
        entity_names: dict[str, str] = {}
        if entity_ids:
            ent_result = sb.table("entities").select("id, name").in_("id", entity_ids).execute()
            entity_names = {e["id"]: e["name"] for e in (ent_result.data or [])}
        for row in rows:
            entity_name = entity_names.get(row.get("entity_id", ""), "Unknown entity")
            metric = row.get("metric_key", "metric").replace("_", " ").title()
            zscore = row.get("zscore_at_detection")
            z_str = f" ({zscore:.1f}σ)" if zscore else ""
            priorities.append(Priority(
                category="sentinel",
                urgency="critical" if row.get("severity") == "critical" else "high",
                title=f"{entity_name}: {metric} anomaly{z_str}",
                detail=f"Risk type: {row.get('risk_type', 'anomaly')} — Sentinel FinOps",
                source="Sentinel",
            ))
    except Exception as exc:
        LOGGER.debug("[Priorities] Sentinel risks collect failed: %s", exc)
    return priorities


def _collect_email_actions() -> list[Priority]:
    """Pull urgent email action items via JARVIS email service."""
    priorities: list[Priority] = []
    try:
        from app.services.email_integrations import EmailIntegrationManager
        mgr = EmailIntegrationManager()
        urgent_query = 'subject:("action required" OR "urgent" OR "deadline" OR "overdue") is:unread newer_than:2d'
        messages = mgr.search_emails(query=urgent_query, max_results=5)
        for msg in messages or []:
            subject = msg.get("subject") or "Urgent email"
            from_ = msg.get("from") or "Unknown sender"
            priorities.append(Priority(
                category="email",
                urgency="high",
                title=subject,
                detail=f"From: {from_}",
                source="Gmail/Outlook",
            ))
    except Exception as exc:
        LOGGER.debug("[Priorities] Email actions failed: %s", exc)
    return priorities


# ── Main API ──────────────────────────────────────────────────────────────────

_URGENCY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def get_competing_priorities(tz_name: str = "Pacific/Guam") -> PrioritiesReport:
    """
    Aggregate all competing demands and return a structured report.

    The report includes a natural-language decision_prompt that JARVIS
    can speak/display verbatim: "Here's what's competing for your attention..."
    """
    all_priorities: list[Priority] = []
    all_priorities.extend(_collect_sentinel_risks())   # FinOps first — highest signal
    all_priorities.extend(_collect_calendar(tz_name))
    all_priorities.extend(_collect_enterprise_alerts())
    all_priorities.extend(_collect_reminders())
    all_priorities.extend(_collect_email_actions())

    # Sort: critical > high > medium > low, then by category
    all_priorities.sort(key=lambda p: (_URGENCY_ORDER.get(p.urgency, 3), p.category))

    report = PrioritiesReport(priorities=all_priorities)

    if not all_priorities:
        report.summary = "All clear — no competing priorities right now."
        report.decision_prompt = "Your slate is clear. What would you like to work on?"
        return report

    # Build human-readable summary
    category_counts: dict[str, int] = {}
    for p in all_priorities:
        category_counts[p.category] = category_counts.get(p.category, 0) + 1

    parts = []
    if category_counts.get("sentinel"):
        parts.append(f"{category_counts['sentinel']} FinOps risk(s) detected")
    if category_counts.get("calendar"):
        parts.append(f"{category_counts['calendar']} calendar event(s) today")
    if category_counts.get("enterprise"):
        parts.append(f"{category_counts['enterprise']} enterprise alert(s)")
    if category_counts.get("email"):
        parts.append(f"{category_counts['email']} urgent email(s)")
    if category_counts.get("reminder"):
        parts.append(f"{category_counts['reminder']} personal reminder(s)")

    report.summary = "Competing priorities: " + ", ".join(parts) + "."

    # Build the decision prompt JARVIS speaks
    top = all_priorities[:3]
    items_text = "\n".join(f"  • [{p.urgency.upper()}] {p.title} ({p.source})" for p in top)
    more = len(all_priorities) - 3
    more_text = f"\n  ...and {more} more." if more > 0 else ""

    report.decision_prompt = (
        f"Here's what's competing for your attention right now:\n"
        f"{items_text}{more_text}\n\n"
        f"What do you want to tackle first?"
    )

    return report


def priorities_to_dict(report: PrioritiesReport) -> dict[str, Any]:
    """Serialize PrioritiesReport to JSON-safe dict."""
    return {
        "summary": report.summary,
        "decision_prompt": report.decision_prompt,
        "generated_at": report.generated_at,
        "total": len(report.priorities),
        "priorities": [
            {
                "category": p.category,
                "urgency": p.urgency,
                "title": p.title,
                "detail": p.detail,
                "source": p.source,
                "due_at": p.due_at,
            }
            for p in report.priorities
        ],
    }
