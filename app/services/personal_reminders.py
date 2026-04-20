"""
personal_reminders.py — thin helper consumed by the scheduler.

Queries jarvis_personal_reminders for records whose next_occurrence is <=
now, marks them as fired, and returns the list so the scheduler can push
Pushover notifications.

Default reminders (eat / hydrate / exercise / check-in) are seeded on first
call if the table is empty, so the system works out-of-the-box.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any

LOGGER = logging.getLogger("backend.services.personal_reminders")

# ── Default reminders seeded if none exist ──────────────────────────────────

_DEFAULT_REMINDERS: list[dict[str, Any]] = [
    {
        "title": "Eat something",
        "message": "Hey — have you eaten in the last few hours? Fuel up.",
        "recurrence": "interval_hours",
        "recurrence_value": 4,
        "priority": 0,
        "is_active": True,
    },
    {
        "title": "Hydrate",
        "message": "Drink a glass of water right now.",
        "recurrence": "interval_hours",
        "recurrence_value": 2,
        "priority": 0,
        "is_active": True,
    },
    {
        "title": "Move your body",
        "message": "Time to move — a 10-minute walk counts. You've got this.",
        "recurrence": "interval_hours",
        "recurrence_value": 6,
        "priority": 0,
        "is_active": True,
    },
    {
        "title": "Daily check-in",
        "message": "Quick check-in: how are you actually feeling? One sentence.",
        "recurrence": "daily",
        "recurrence_value": 20,  # 8pm
        "priority": 0,
        "is_active": True,
    },
]


def _get_client():
    """Return a Supabase service-role client (lazy import to avoid circular deps)."""
    from supabase import create_client
    url = os.getenv("JARVISCORE_SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    key = os.getenv("JARVISCORE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)


def _seed_defaults(client) -> None:
    """Insert default reminders if the table is empty."""
    try:
        result = client.table("jarvis_personal_reminders").select("id", count="exact").execute()
        if result.count and result.count > 0:
            return
        now_iso = datetime.utcnow().isoformat()
        rows = [
            {
                **r,
                "next_occurrence": now_iso,
                "created_at": now_iso,
            }
            for r in _DEFAULT_REMINDERS
        ]
        client.table("jarvis_personal_reminders").insert(rows).execute()
        LOGGER.info("[Reminders] Seeded %d default reminders", len(rows))
    except Exception as exc:
        LOGGER.warning("[Reminders] Could not seed defaults: %s", exc)


def _advance_next_occurrence(reminder: dict[str, Any]) -> str:
    """Calculate the next_occurrence timestamp after a reminder fires."""
    recurrence = reminder.get("recurrence", "interval_hours")
    value = int(reminder.get("recurrence_value") or 4)
    now = datetime.utcnow()

    if recurrence == "interval_hours":
        return (now + timedelta(hours=value)).isoformat()
    if recurrence == "interval_minutes":
        return (now + timedelta(minutes=value)).isoformat()
    if recurrence == "daily":
        # next day at the same hour
        tomorrow = (now + timedelta(days=1)).replace(hour=value, minute=0, second=0, microsecond=0)
        return tomorrow.isoformat()
    if recurrence == "weekly":
        return (now + timedelta(weeks=1)).isoformat()
    # fallback: 4 hours
    return (now + timedelta(hours=4)).isoformat()


def get_due_reminders() -> list[dict[str, Any]]:
    """
    Return all active reminders whose next_occurrence <= now.
    Advances each fired reminder's next_occurrence so it won't re-fire
    until the configured interval has elapsed.

    Returns a list of dicts with at least: title, message, priority.
    Falls back to an empty list if Supabase is unavailable.
    """
    client = _get_client()
    if client is None:
        LOGGER.debug("[Reminders] No Supabase client — skipping")
        return []

    try:
        _seed_defaults(client)

        now_iso = datetime.utcnow().isoformat()
        result = (
            client.table("jarvis_personal_reminders")
            .select("id, title, message, recurrence, recurrence_value, priority")
            .eq("is_active", True)
            .lte("next_occurrence", now_iso)
            .execute()
        )
        due = result.data or []

        # Advance each fired reminder
        for reminder in due:
            next_occ = _advance_next_occurrence(reminder)
            try:
                client.table("jarvis_personal_reminders").update(
                    {"next_occurrence": next_occ, "last_fired_at": now_iso}
                ).eq("id", reminder["id"]).execute()
            except Exception as exc:
                LOGGER.warning("[Reminders] Failed to advance %s: %s", reminder.get("id"), exc)

        LOGGER.info("[Reminders] %d reminders due", len(due))
        return [
            {
                "title": r.get("title", "Reminder"),
                "message": r.get("message", r.get("title", "Time to check in.")),
                "priority": r.get("priority", 0),
            }
            for r in due
        ]

    except Exception as exc:
        LOGGER.error("[Reminders] get_due_reminders failed: %s", exc)
        return []
