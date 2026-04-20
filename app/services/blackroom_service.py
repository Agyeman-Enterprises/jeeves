"""
BlackRoom Service — Read-only access to strategic decisions and briefs.

BlackRoom is an isolated strategic management product for ideation in a silo.
JARVIS has read-only access to fetch decisions and briefs as context for
high-level strategic queries. JARVIS never writes to BlackRoom.

Supabase project: nkbejqkvdizbxxsapdtw
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

_SUPABASE_URL = os.getenv("BLACKROOM_SUPABASE_URL", "https://nkbejqkvdizbxxsapdtw.supabase.co")
_SERVICE_KEY = os.getenv("BLACKROOM_SERVICE_ROLE_KEY", "")


class BlackroomService:
    """
    Read-only Supabase client for BlackRoom strategic decisions.
    Used by JARVIS to pull context for CEO-level briefings.
    """

    def __init__(self) -> None:
        self.base_url = _SUPABASE_URL.rstrip("/")
        self.service_key = _SERVICE_KEY
        self.timeout = 10.0

    @property
    def _headers(self) -> Dict[str, str]:
        if not self.service_key:
            raise RuntimeError("BLACKROOM_SERVICE_ROLE_KEY not configured")
        return {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
        }

    def _get(self, table: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        url = f"{self.base_url}/rest/v1/{table}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, headers=self._headers, params=params or {})
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            LOGGER.error("BlackRoom read error (%s): %s", table, e)
            return []

    # ── Decisions ─────────────────────────────────────────────────────────────

    def get_decisions(self, limit: int = 10, status: Optional[str] = None) -> List[Dict]:
        """Fetch recent strategic decisions."""
        params: Dict[str, Any] = {
            "order": "created_at.desc",
            "limit": limit,
            "select": "id,title,status,created_at",
        }
        if status:
            params["status"] = f"eq.{status}"
        return self._get("decisions", params)

    def get_decision(self, decision_id: str) -> Optional[Dict]:
        """Fetch a single decision with full detail."""
        params = {
            "id": f"eq.{decision_id}",
            "select": "id,title,description,status,created_at",
        }
        rows = self._get("decisions", params)
        return rows[0] if rows else None

    def get_decision_brief(self, decision_id: str) -> Optional[str]:
        """Fetch the executive brief for a decision."""
        # BlackRoom generates briefs via /api/decisions/[id]/brief
        # Here we read the underlying brief text if stored in DB
        params = {
            "decision_id": f"eq.{decision_id}",
            "select": "brief_text,created_at",
            "order": "created_at.desc",
            "limit": 1,
        }
        rows = self._get("decision_briefs", params)
        return rows[0].get("brief_text") if rows else None

    def get_active_decisions_summary(self) -> str:
        """Return a plain-text summary of open/active decisions for JARVIS briefings."""
        decisions = self.get_decisions(limit=5, status="active")
        if not decisions:
            return "No active strategic decisions in BlackRoom."
        lines = ["Active BlackRoom decisions:"]
        for d in decisions:
            lines.append(f"  • {d.get('title', 'Untitled')} [{d.get('status', '?')}]")
        return "\n".join(lines)

    # ── Health ────────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Returns True if BlackRoom Supabase is reachable."""
        rows = self._get("decisions", {"limit": 1, "select": "id"})
        return isinstance(rows, list)
