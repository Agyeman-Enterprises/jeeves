"""
Healthcare Agent — SoloPractice EMR Integration
Gives JARVIS access to clinical data: appointments, patients, labs, vitals.

Data comes directly from SoloPractice's Supabase via solopractice_service.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.agents.base import AgentContext, AgentResponse, BaseAgent
from app.services.solopractice.solopractice_service import solopractice_service

LOGGER = logging.getLogger(__name__)

# Keywords that route queries to this agent
_KEYWORDS = [
    "appointment", "appointments", "schedule", "patient", "patients", "clinic",
    "lab", "labs", "results", "vitals", "vital", "EMR", "solopractice",
    "today's patients", "who do i see", "my schedule", "clinical",
]


def _fmt_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%I:%M %p").lstrip("0") or "12:00 AM"
    except Exception:
        return iso


def _summarize_appointments(appts: List[Dict[str, Any]]) -> str:
    if not appts:
        return "No appointments found."
    lines = []
    for a in appts:
        patient = a.get("patient") or {}
        if isinstance(patient, list):
            patient = patient[0] if patient else {}
        name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or "Unknown"
        time_str = _fmt_time(a.get("start_time", ""))
        status = a.get("status", "scheduled").replace("_", " ").title()
        visit = a.get("visit_category", "") or ""
        telehealth = " (Telehealth)" if a.get("is_telehealth") else ""
        lines.append(f"  • {time_str} — {name}{telehealth} [{status}]{f' — {visit}' if visit else ''}")
    return "\n".join(lines)


class HealthcareAgent(BaseAgent):
    """Provides clinical data from SoloPractice EMR via Supabase."""

    name = "HealthcareAgent"
    description = "Accesses SoloPractice EMR: appointments, patients, lab results, and vitals."
    capabilities = [
        "Show today's appointment schedule",
        "List appointments for a specific date",
        "Look up a patient record",
        "Search patients by name",
        "Get lab results for a patient",
        "Get vital sign readings for a patient",
        "Provide a daily clinical summary",
    ]

    def __init__(self, database=None) -> None:
        super().__init__()
        self.database = database

    def supports(self, query: str) -> bool:
        q = query.lower()
        return any(kw in q for kw in _KEYWORDS)

    def handle(self, query: str, context: Optional[AgentContext] = None) -> AgentResponse:
        if not solopractice_service.is_configured():
            return AgentResponse(
                agent=self.name,
                content=(
                    "SoloPractice is not connected. "
                    "Add SOLOPRACTICE_SUPABASE_URL and SOLOPRACTICE_SERVICE_ROLE_KEY to JARVIS .env."
                ),
                status="warning",
            )

        q = query.lower()

        # ── Daily summary ──────────────────────────────────────────────
        if any(kw in q for kw in ["summary", "briefing", "overview", "today"]):
            summary = solopractice_service.get_daily_summary()
            if "error" in summary:
                return AgentResponse(agent=self.name, content=summary["error"], status="error")
            total = summary["total_appointments"]
            breakdown = summary["status_breakdown"]
            breakdown_str = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in breakdown.items())
            preview = _summarize_appointments(summary.get("appointments", []))
            content = (
                f"**Today ({summary['date']}) — {total} appointments**\n"
                f"Status: {breakdown_str}\n\n"
                f"First 5:\n{preview}"
            )
            return AgentResponse(agent=self.name, content=content, data=summary)

        # ── Appointments for a date ─────────────────────────────────────
        if any(kw in q for kw in ["appointment", "schedule", "see", "patients"]):
            # Try to extract a date from query like "2026-03-05" or "tomorrow"
            date_str: Optional[str] = None
            date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", query)
            if date_match:
                date_str = date_match.group(1)
            elif "tomorrow" in q:
                from datetime import timedelta
                date_str = (date.today() + timedelta(days=1)).isoformat()
            elif "today" not in q:
                date_str = date.today().isoformat()

            appts = solopractice_service.get_appointments(date_str=date_str)
            label = date_str or date.today().isoformat()
            summary_text = _summarize_appointments(appts)
            content = f"**Appointments for {label}** ({len(appts)} total)\n\n{summary_text}"
            return AgentResponse(agent=self.name, content=content, data={"appointments": appts})

        # ── Patient search ─────────────────────────────────────────────
        if any(kw in q for kw in ["patient", "find patient", "search patient", "look up", "search for", "find"]):
            # Extract name: try most-specific patterns first
            name_match = (
                re.search(r'"([^"]+)"', query)                                        # "quoted name"
                or re.search(r"named?\s+([A-Za-z][A-Za-z\-\']+(?:\s+[A-Za-z][A-Za-z\-\']+)?)", query, re.I)  # named Maria / named Maria Santos
                or re.search(r"(?:search for|find|look up)\s+(?:patient\s+)?([A-Za-z][A-Za-z\-\']+)", query, re.I)  # search for Santos / look up patient Chen
                or re.search(r"patient\s+([A-Za-z][A-Za-z\-\']+)", query, re.I)      # patient Santos
            )
            if name_match:
                name = name_match.group(1).strip()
                patients = solopractice_service.search_patients(name)
                if not patients:
                    return AgentResponse(agent=self.name, content=f"No patients found matching '{name}'.")
                lines = [
                    f"  • {p['first_name']} {p['last_name']} — DOB: {p.get('date_of_birth', 'N/A')} — {p.get('phone_mobile', '')}"
                    for p in patients
                ]
                content = f"**Patients matching '{name}':**\n" + "\n".join(lines)
                return AgentResponse(agent=self.name, content=content, data={"patients": patients})
            return AgentResponse(
                agent=self.name,
                content="Please specify a patient name to search, e.g. \"find patient Smith\"",
            )

        # ── Fallback ───────────────────────────────────────────────────
        summary = solopractice_service.get_daily_summary()
        total = summary.get("total_appointments", 0)
        return AgentResponse(
            agent=self.name,
            content=f"SoloPractice is connected. Today has {total} appointments. Ask me about schedules, patients, labs, or vitals.",
            data=summary,
        )
