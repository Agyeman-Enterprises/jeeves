"""
OneDesk service for JARVIS.

Read-only direct Supabase connector to OneDesk's project management database.
Surfaces tasks, sprints, and project status for CEO briefing.

Required env vars:
  ONEDESK_SUPABASE_URL       e.g. https://wxdupvgopeyjvhxdwdzu.supabase.co
  ONEDESK_SERVICE_ROLE_KEY   Supabase service role key (bypasses RLS)
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

OD_URL = os.getenv("ONEDESK_SUPABASE_URL", "").rstrip("/")
OD_KEY = os.getenv("ONEDESK_SERVICE_ROLE_KEY", "")


class OneDeskService:
    """Read-only Supabase client for OneDesk project management data."""

    def __init__(self) -> None:
        self._configured = bool(OD_URL and OD_KEY)
        if not self._configured:
            LOGGER.warning(
                "OneDesk not configured. "
                "Set ONEDESK_SUPABASE_URL and ONEDESK_SERVICE_ROLE_KEY in .env"
            )

    def is_configured(self) -> bool:
        return self._configured

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": OD_KEY,
            "Authorization": f"Bearer {OD_KEY}",
            "Content-Type": "application/json",
        }

    def _get(self, table: str, params: List[tuple]) -> List[Dict[str, Any]]:
        if not self._configured:
            return []
        try:
            url = f"{OD_URL}/rest/v1/{table}"
            with httpx.Client(timeout=10) as client:
                resp = client.get(url, headers=self._headers(), params=params)
                if resp.is_success:
                    return resp.json() or []
                LOGGER.warning("OneDesk query failed %s: %s", resp.status_code, resp.text[:200])
                return []
        except Exception as exc:
            LOGGER.error("OneDesk query error on %s: %s", table, exc)
            return []

    # ── Task queries ───────────────────────────────────────────────────────────

    def get_in_progress_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Tasks currently in progress."""
        return self._get("tasks", [
            ("status", "eq.in_progress"),
            ("order", "due_date.asc.nullslast"),
            ("limit", str(limit)),
            ("select", "id,title,priority,due_date,project_id,sprint_id"),
        ])

    def get_overdue_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Tasks past due date that aren't done."""
        today = date.today().isoformat()
        return self._get("tasks", [
            ("due_date", f"lt.{today}"),
            ("status", "not.eq.done"),
            ("order", "due_date.asc"),
            ("limit", str(limit)),
            ("select", "id,title,priority,status,due_date,project_id"),
        ])

    def get_urgent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """High and urgent priority tasks not yet done."""
        return self._get("tasks", [
            ("priority", "in.(high,urgent)"),
            ("status", "not.eq.done"),
            ("order", "priority.desc,due_date.asc.nullslast"),
            ("limit", str(limit)),
            ("select", "id,title,priority,status,due_date,project_id"),
        ])

    def get_active_sprints(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Currently active sprints."""
        return self._get("sprints", [
            ("status", "eq.active"),
            ("order", "end_date.asc"),
            ("limit", str(limit)),
            ("select", "id,name,goal,start_date,end_date,project_id"),
        ])

    def get_active_projects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Projects not yet done."""
        return self._get("projects", [
            ("status", "not.eq.done"),
            ("order", "due_date.asc.nullslast"),
            ("limit", str(limit)),
            ("select", "id,name,status,start_date,due_date"),
        ])

    def get_blocked_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Blocked tasks that need attention."""
        return self._get("tasks", [
            ("status", "eq.blocked"),
            ("order", "due_date.asc.nullslast"),
            ("limit", str(limit)),
            ("select", "id,title,priority,due_date,project_id"),
        ])

    # ── CEO briefing summary ───────────────────────────────────────────────────

    def get_briefing_summary(self) -> str:
        """One-paragraph OneDesk snapshot for CEO morning briefing."""
        if not self._configured:
            return "OneDesk: not configured."
        try:
            in_progress = self.get_in_progress_tasks(limit=50)
            overdue = self.get_overdue_tasks(limit=50)
            blocked = self.get_blocked_tasks(limit=50)
            urgent = self.get_urgent_tasks(limit=10)
            sprints = self.get_active_sprints()
            projects = self.get_active_projects()

            lines = []

            # Projects
            if projects:
                proj_names = [p.get("name", "?") for p in projects[:4]]
                lines.append(f"Active projects ({len(projects)}): {', '.join(proj_names)}.")

            # Sprints
            if sprints:
                sprint = sprints[0]
                end = sprint.get("end_date", "?")
                lines.append(f"Active sprint: \"{sprint.get('name','?')}\" ends {end}.")

            # Task health
            parts = [f"{len(in_progress)} in progress"]
            if overdue:
                parts.append(f"{len(overdue)} overdue")
            if blocked:
                parts.append(f"{len(blocked)} blocked")
            lines.append(f"Tasks: {', '.join(parts)}.")

            # Urgent
            if urgent:
                urgent_titles = [t.get("title", "?") for t in urgent[:3]]
                lines.append(f"Urgent: {'; '.join(urgent_titles)}.")

            return "  OneDesk — " + " ".join(lines) if lines else "OneDesk: no active work."
        except Exception as exc:
            LOGGER.error("OneDesk briefing error: %s", exc)
            return "OneDesk: error fetching summary."

    def health_check(self) -> bool:
        """Return True if Supabase is reachable."""
        if not self._configured:
            return False
        rows = self._get("tasks", [("limit", "1"), ("select", "id")])
        return isinstance(rows, list)


# Singleton
onedesk_service = OneDeskService()
