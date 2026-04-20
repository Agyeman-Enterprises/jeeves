"""
SoloPractice EMR Service
Reads directly from SoloPractice's Supabase database using the service role key.
No external API needed — SoloPractice IS the app at C:/dev/Solopractice-1.

Required env vars:
  SOLOPRACTICE_SUPABASE_URL      e.g. https://wszhbcllrqnyaksbbjgx.supabase.co
  SOLOPRACTICE_SERVICE_ROLE_KEY  Supabase service role key (bypasses RLS)
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

SP_URL = os.getenv("SOLOPRACTICE_SUPABASE_URL", "").rstrip("/")
SP_KEY = os.getenv("SOLOPRACTICE_SERVICE_ROLE_KEY", "")


class SoloPracticeService:
    """Direct Supabase client for SoloPractice EMR data."""

    def __init__(self) -> None:
        self._configured = bool(SP_URL and SP_KEY)
        if not self._configured:
            LOGGER.warning(
                "SoloPractice Supabase not configured. "
                "Set SOLOPRACTICE_SUPABASE_URL and SOLOPRACTICE_SERVICE_ROLE_KEY in .env"
            )

    def is_configured(self) -> bool:
        return self._configured

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": SP_KEY,
            "Authorization": f"Bearer {SP_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _get(self, table: str, params: List[tuple] | Dict[str, str]) -> List[Dict[str, Any]]:
        """Generic Supabase REST GET via PostgREST.

        params can be a list of (key, value) tuples to support multiple filters
        on the same column (e.g. start_time=gte.X AND start_time=lt.Y).
        """
        try:
            url = f"{SP_URL}/rest/v1/{table}"
            # Convert dict to list of tuples so httpx can repeat keys
            param_list = list(params.items()) if isinstance(params, dict) else params
            with httpx.Client(timeout=10) as client:
                resp = client.get(url, headers=self._headers(), params=param_list)
                if not resp.is_success:
                    LOGGER.error("SoloPractice query %s returned %s: %s", table, resp.status_code, resp.text[:200])
                    return []
                data = resp.json()
                return data if isinstance(data, list) else []
        except Exception as exc:
            LOGGER.error("SoloPractice query %s failed: %s", table, exc)
            return []

    # ──────────────────────────────────────────────
    # Appointments
    # ──────────────────────────────────────────────

    def get_appointments_today(self) -> List[Dict[str, Any]]:
        """All appointments for today across all providers."""
        if not self._configured:
            return []
        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        return self._get("appointments", [
            ("select", "id,start_time,end_time,status,visit_category,is_telehealth,provider_id,"
                       "patient:patients(first_name,last_name,date_of_birth)"),
            ("start_time", f"gte.{today}T00:00:00"),
            ("start_time", f"lt.{tomorrow}T00:00:00"),
            ("order", "start_time.asc"),
        ])

    def get_appointments(
        self,
        date_str: Optional[str] = None,
        provider_id: Optional[str] = None,
        practice_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch appointments with optional filters. date_str: YYYY-MM-DD"""
        if not self._configured:
            return []
        param_list: List[tuple] = [
            ("select", "id,start_time,end_time,status,visit_category,is_telehealth,provider_id,"
                       "patient:patients(first_name,last_name)"),
            ("order", "start_time.asc"),
        ]
        if date_str:
            next_day = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            param_list.append(("start_time", f"gte.{date_str}T00:00:00"))
            param_list.append(("start_time", f"lt.{next_day}T00:00:00"))
        if provider_id:
            param_list.append(("provider_id", f"eq.{provider_id}"))
        if practice_id:
            param_list.append(("practice_id", f"eq.{practice_id}"))
        return self._get("appointments", param_list)

    # ──────────────────────────────────────────────
    # Patients
    # ──────────────────────────────────────────────

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single patient record."""
        if not self._configured:
            return None
        rows = self._get("patients", {
            "select": "id,first_name,last_name,date_of_birth,sex,phone_mobile,email",
            "id": f"eq.{patient_id}",
            "limit": "1",
        })
        return rows[0] if rows else None

    def search_patients(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search patients by name (case-insensitive prefix match)."""
        if not self._configured:
            return []
        return self._get("patients", {
            "select": "id,first_name,last_name,date_of_birth,phone_mobile",
            "or": f"(first_name.ilike.{name}%,last_name.ilike.{name}%)",
            "limit": str(limit),
            "order": "last_name.asc",
        })

    # ──────────────────────────────────────────────
    # Lab Results
    # ──────────────────────────────────────────────

    def get_lab_results(self, patient_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent lab results for a patient."""
        if not self._configured:
            return []
        return self._get("lab_results", {
            "select": "id,collection_date,result_date,has_abnormal,has_critical,overall_status,ai_patient_friendly_summary",
            "patient_id": f"eq.{patient_id}",
            "released_to_patient": "eq.true",
            "order": "result_date.desc",
            "limit": str(limit),
        })

    # ──────────────────────────────────────────────
    # Vital Readings
    # ──────────────────────────────────────────────

    def get_vital_readings(self, patient_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent vital readings for a patient."""
        if not self._configured:
            return []
        return self._get("vital_readings", {
            "select": "id,reading_type,value_primary,value_systolic,value_diastolic,unit,is_abnormal,recorded_at",
            "patient_id": f"eq.{patient_id}",
            "order": "recorded_at.desc",
            "limit": str(limit),
        })

    # ──────────────────────────────────────────────
    # Summary for JARVIS briefing
    # ──────────────────────────────────────────────

    def get_daily_summary(self) -> Dict[str, Any]:
        """Pull a daily practice summary for JARVIS morning briefing."""
        if not self._configured:
            return {"error": "SoloPractice not configured"}

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        # Today's appointments
        appointments = self._get("appointments", [
            ("select", "id,start_time,end_time,status,visit_category,provider_id,"
                       "patient:patients(first_name,last_name)"),
            ("start_time", f"gte.{today}T00:00:00"),
            ("start_time", f"lt.{tomorrow}T00:00:00"),
            ("order", "start_time.asc"),
        ])

        total = len(appointments)
        statuses: Dict[str, int] = {}
        for appt in appointments:
            statuses[appt.get("status", "unknown")] = statuses.get(appt.get("status", "unknown"), 0) + 1

        return {
            "date": today,
            "total_appointments": total,
            "status_breakdown": statuses,
            "appointments": appointments[:5],  # first 5 for briefing
        }


# Singleton
solopractice_service = SoloPracticeService()
