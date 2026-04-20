"""
WhoZonCall service for JARVIS.

Direct Supabase connector to WhoZonCall's on-call scheduling database.
Supports reading the current schedule AND creating new periods/shifts.

Tables used (exact column names from schema):
  whozon_shifts          — individual shift assignments
  whozon_schedule_periods — named schedule periods (start_date, end_date, status)
  whozon_service_lines   — service lines (NPP Day, NICU, TelePICU, etc.)
  whozon_shift_types     — shift type definitions (name, code)
  whozon_providers       — provider records (first_name, last_name, initials)
  whozon_provider_display — initials, color, fte_percentage
  whozon_organizations   — organizations (id, name, code)

Required env vars:
  WHOZON_SUPABASE_URL       e.g. https://kszspbkxolbtfoepcqtq.supabase.co
  WHOZON_SERVICE_ROLE_KEY   Supabase service role key (bypasses RLS)
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

WZ_URL = os.getenv("WHOZON_SUPABASE_URL", "").rstrip("/")
WZ_KEY = os.getenv("WHOZON_SERVICE_ROLE_KEY", "")

# GMH organization ID (primary org in WhoZonCall)
GMH_ORG_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


class WhoZonService:
    """Supabase client for WhoZonCall on-call schedule data (read + write)."""

    def __init__(self) -> None:
        self._configured = bool(WZ_URL and WZ_KEY)
        if not self._configured:
            LOGGER.warning(
                "WhoZonCall not configured. "
                "Set WHOZON_SUPABASE_URL and WHOZON_SERVICE_ROLE_KEY in .env"
            )
        self._org_id: Optional[str] = None  # lazily resolved

    def is_configured(self) -> bool:
        return self._configured

    def get_org_id(self) -> str:
        """Return the GMH organization UUID, fetching from DB if needed."""
        if self._org_id:
            return self._org_id
        rows = self._get("whozon_organizations", [
            ("code", "eq.GMH"),
            ("select", "id"),
            ("limit", "1"),
        ])
        self._org_id = rows[0]["id"] if rows else GMH_ORG_ID
        return self._org_id

    # ── HTTP helpers ───────────────────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": WZ_KEY,
            "Authorization": f"Bearer {WZ_KEY}",
            "Content-Type": "application/json",
        }

    def _get(self, table: str, params: List[tuple]) -> List[Dict[str, Any]]:
        if not self._configured:
            return []
        try:
            url = f"{WZ_URL}/rest/v1/{table}"
            with httpx.Client(timeout=10) as client:
                resp = client.get(url, headers=self._headers(), params=params)
                if resp.is_success:
                    return resp.json() or []
                LOGGER.warning("WhoZon query failed %s: %s", resp.status_code, resp.text[:200])
                return []
        except Exception as exc:
            LOGGER.error("WhoZon query error on %s: %s", table, exc)
            return []

    def _post(self, table: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a row and return the created record."""
        if not self._configured:
            return None
        try:
            url = f"{WZ_URL}/rest/v1/{table}"
            headers = {**self._headers(), "Prefer": "return=representation"}
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.is_success:
                    data = resp.json()
                    return data[0] if isinstance(data, list) and data else data
                LOGGER.error("WhoZon POST %s failed %s: %s", table, resp.status_code, resp.text[:300])
                return None
        except Exception as exc:
            LOGGER.error("WhoZon POST %s error: %s", table, exc)
            return None

    def _patch(self, table: str, record_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a row by id and return the updated record."""
        if not self._configured:
            return None
        try:
            url = f"{WZ_URL}/rest/v1/{table}"
            headers = {**self._headers(), "Prefer": "return=representation"}
            with httpx.Client(timeout=10) as client:
                resp = client.patch(url, headers=headers, json=payload, params=[("id", f"eq.{record_id}")])
                if resp.is_success:
                    data = resp.json()
                    return data[0] if isinstance(data, list) and data else data
                LOGGER.error("WhoZon PATCH %s failed %s: %s", table, resp.status_code, resp.text[:300])
                return None
        except Exception as exc:
            LOGGER.error("WhoZon PATCH %s error: %s", table, exc)
            return None

    # ── Schedule periods ───────────────────────────────────────────────────────

    def get_active_period(self) -> Optional[Dict[str, Any]]:
        """Return the currently active schedule period."""
        today = date.today().isoformat()
        rows = self._get("whozon_schedule_periods", [
            ("status", "eq.active"),
            ("start_date", f"lte.{today}"),
            ("end_date", f"gte.{today}"),
            ("order", "start_date.desc"),
            ("limit", "1"),
            ("select", "id,name,start_date,end_date,status,notes"),
        ])
        return rows[0] if rows else None

    def get_all_periods(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent/upcoming schedule periods."""
        return self._get("whozon_schedule_periods", [
            ("order", "start_date.desc"),
            ("limit", str(limit)),
            ("select", "id,name,start_date,end_date,status"),
        ])

    def create_schedule_period(
        self,
        name: str,
        start_date: str,
        end_date: str,
        period_type: str = "month",
        notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new schedule period. start_date/end_date: YYYY-MM-DD."""
        org_id = self.get_org_id()
        payload: Dict[str, Any] = {
            "organization_id": org_id,
            "org_id": org_id,
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "period_type": period_type,
            "status": "draft",
        }
        if notes:
            payload["notes"] = notes
        return self._post("whozon_schedule_periods", payload)

    def publish_schedule_period(self, period_id: str) -> Optional[Dict[str, Any]]:
        """Change a draft schedule period to active."""
        return self._patch("whozon_schedule_periods", period_id, {
            "status": "active",
            "published_at": datetime.now(timezone.utc).isoformat(),
        })

    # ── Shifts ─────────────────────────────────────────────────────────────────

    def get_shifts_on_date(self, target_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Return all shifts on a specific date (filtered by shift_date)."""
        target = (target_date or date.today()).isoformat()
        return self._get("whozon_shifts", [
            ("shift_date", f"eq.{target}"),
            ("order", "start_time.asc"),
            ("limit", "50"),
            ("select", "id,provider_id,service_line_id,shift_type_id,shift_date,start_time,end_time,is_backup,status,notes"),
        ])

    def get_shifts_for_period(self, period_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Return all shifts for a schedule period."""
        return self._get("whozon_shifts", [
            ("schedule_period_id", f"eq.{period_id}"),
            ("order", "shift_date.asc,start_time.asc"),
            ("limit", str(limit)),
            ("select", "id,provider_id,service_line_id,shift_type_id,shift_date,start_time,end_time,is_backup,status,notes"),
        ])

    def create_shift(
        self,
        schedule_period_id: str,
        service_line_id: str,
        shift_date: str,
        shift_type_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        is_backup: bool = False,
        notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a single shift. shift_date: YYYY-MM-DD, times: YYYY-MM-DDTHH:MM:SS."""
        org_id = self.get_org_id()
        payload: Dict[str, Any] = {
            "organization_id": org_id,
            "org_id": org_id,
            "schedule_period_id": schedule_period_id,
            "service_line_id": service_line_id,
            "shift_date": shift_date,
            "status": "scheduled",
            "is_backup": is_backup,
        }
        if shift_type_id:
            payload["shift_type_id"] = shift_type_id
        if provider_id:
            payload["provider_id"] = provider_id
        if start_time:
            payload["start_time"] = start_time
        if end_time:
            payload["end_time"] = end_time
        if notes:
            payload["notes"] = notes
        return self._post("whozon_shifts", payload)

    def assign_provider(self, shift_id: str, provider_id: str) -> Optional[Dict[str, Any]]:
        """Assign a provider to an existing shift."""
        return self._patch("whozon_shifts", shift_id, {"provider_id": provider_id})

    def bulk_create_shifts(self, shifts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple shifts at once. Each dict must have service_line_id and shift_date."""
        created = []
        for s in shifts:
            result = self.create_shift(
                schedule_period_id=s["schedule_period_id"],
                service_line_id=s["service_line_id"],
                shift_date=s["shift_date"],
                shift_type_id=s.get("shift_type_id"),
                provider_id=s.get("provider_id"),
                start_time=s.get("start_time"),
                end_time=s.get("end_time"),
                is_backup=s.get("is_backup", False),
                notes=s.get("notes"),
            )
            if result:
                created.append(result)
        return created

    # ── Reference data ─────────────────────────────────────────────────────────

    def get_service_lines(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Return service lines (NPP Day, NICU, TelePICU, etc.)."""
        params = [
            ("order", "name.asc"),
            ("select", "id,name,code,requires_backup,is_active"),
        ]
        if active_only:
            params.append(("is_active", "eq.true"))
        return self._get("whozon_service_lines", params)

    def get_shift_types(self) -> List[Dict[str, Any]]:
        """Return available shift types (Day 12h, Night 12h, etc.)."""
        return self._get("whozon_shift_types", [
            ("select", "id,name,code,start_time,end_time,is_backup"),
            ("order", "name.asc"),
            ("limit", "50"),
        ])

    def get_providers(self) -> List[Dict[str, Any]]:
        """Return providers with display info from whozon_providers."""
        return self._get("whozon_providers", [
            ("is_active", "eq.true"),
            ("select", "id,initials,color,text_color,fte_percentage"),
            ("limit", "200"),
        ])

    def get_provider_names(self) -> Dict[str, str]:
        """Return {provider_id: display_name} map from whozon_providers."""
        rows = self._get("whozon_providers", [
            ("is_active", "eq.true"),
            ("select", "id,first_name,last_name,initials"),
            ("limit", "200"),
        ])
        return {
            r["id"]: f"{r.get('first_name', '')} {r.get('last_name', '')}".strip() or r.get("initials", "?")
            for r in rows
        }

    def get_providers_list(self) -> List[Dict[str, Any]]:
        """Return full provider list with id, name, initials."""
        return self._get("whozon_providers", [
            ("is_active", "eq.true"),
            ("select", "id,first_name,last_name,initials"),
            ("order", "last_name.asc"),
            ("limit", "200"),
        ])

    def search_providers(self, name: str) -> List[Dict[str, Any]]:
        """Search providers by name (case-insensitive)."""
        name_lower = name.lower()
        all_providers = self.get_providers_list()
        results = []
        for p in all_providers:
            full = f"{p.get('first_name', '')} {p.get('last_name', '')}".lower()
            initials = p.get("initials", "").lower()
            if name_lower in full or name_lower in initials:
                results.append(p)
        return results

    def find_service_line(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a service line by name or code (case-insensitive partial match)."""
        name_lower = name.lower()
        all_lines = self.get_service_lines()
        for line in all_lines:
            line_name = line.get("name", "").lower()
            line_code = line.get("code", "").lower()
            if name_lower in line_name or name_lower in line_code:
                return line
        return None

    def find_shift_type(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a shift type by name or code (case-insensitive)."""
        name_lower = name.lower()
        all_types = self.get_shift_types()
        for st in all_types:
            st_name = st.get("name", "").lower()
            st_code = st.get("code", "").lower()
            if name_lower in st_name or name_lower in st_code:
                return st
        return None

    # ── CEO briefing ───────────────────────────────────────────────────────────

    def get_briefing_summary(self) -> str:
        """On-call schedule snapshot for CEO morning briefing."""
        if not self._configured:
            return "WhoZonCall: not configured."
        try:
            period = self.get_active_period()
            today_shifts = self.get_shifts_on_date()
            provider_names = self.get_provider_names()

            lines = []

            if period:
                lines.append(f"Active schedule: \"{period['name']}\" ({period['start_date']} to {period['end_date']}).")
            else:
                lines.append("No active schedule period.")

            if today_shifts:
                non_backup = [s for s in today_shifts if not s.get("is_backup")]
                backup = [s for s in today_shifts if s.get("is_backup")]
                provider_ids = list({s["provider_id"] for s in non_backup if s.get("provider_id")})
                names = [provider_names.get(pid, pid[:8]) for pid in provider_ids[:5]]
                lines.append(f"On call today: {len(non_backup)} shifts ({', '.join(names) if names else 'unassigned'}).")
                if backup:
                    lines.append(f"Backup coverage: {len(backup)} providers.")
            else:
                lines.append("No shifts recorded for today.")

            return "  WhoZonCall — " + " ".join(lines)
        except Exception as exc:
            LOGGER.error("WhoZon briefing error: %s", exc)
            return "WhoZonCall: error fetching summary."

    def health_check(self) -> bool:
        if not self._configured:
            return False
        rows = self._get("whozon_schedule_periods", [("limit", "1"), ("select", "id")])
        return isinstance(rows, list)


# Singleton
whozon_service = WhoZonService()
