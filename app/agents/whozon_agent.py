"""
WhoZon Agent — On-Call Scheduling Assistant.

Gives JARVIS full access to WhoZonCall: view current schedules, who's on call,
and create new schedule periods and shift assignments.

Responds to natural-language queries like:
  "Who's on call today?"
  "Show me the March 2026 schedule"
  "Create a new schedule for April 2026"
  "Assign Dr. Smith to NICU Day on March 10"
  "What service lines are there?"
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.agents.base import AgentContext, AgentResponse, BaseAgent
from app.services.whozon_service import whozon_service

LOGGER = logging.getLogger(__name__)

# Keywords that route queries to this agent
_KEYWORDS = [
    "on call", "oncall", "on-call", "whozon", "schedule", "schedules",
    "shift", "shifts", "call schedule", "coverage",
    "nicu", "npp", "telepicu", "telenicu", "micu", "peds", "newborn nursery",
    "who's on", "who is on", "whos on",
    "service line", "service lines", "providers on call",
    "create schedule", "new schedule", "assign", "assign provider",
    "amion", "call schedule", "on-call schedule",
]


def _fmt_date(iso: str) -> str:
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return iso


def _fmt_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return iso


def _extract_date(query: str) -> Optional[date]:
    """Try to extract a date from the query."""
    q = query.lower()
    if "today" in q:
        return date.today()
    if "tomorrow" in q:
        return date.today() + timedelta(days=1)
    if "yesterday" in q:
        return date.today() - timedelta(days=1)
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", query)
    if m:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    # "March 10" or "March 10, 2026"
    m = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+(\d{1,2})(?:,?\s+(\d{4}))?",
        query, re.I,
    )
    if m:
        month_str, day_str, year_str = m.groups()
        year = int(year_str) if year_str else date.today().year
        try:
            return datetime.strptime(f"{month_str[:3].capitalize()} {day_str} {year}", "%b %d %Y").date()
        except Exception:
            pass
    return None


def _extract_month_range(query: str):
    """Return (start_date, end_date, label) for a month mentioned in query."""
    m = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"(?:\s+(\d{4}))?",
        query, re.I,
    )
    if m:
        month_str, year_str = m.groups()
        year = int(year_str) if year_str else date.today().year
        try:
            start = datetime.strptime(f"{month_str[:3].capitalize()} 1 {year}", "%b %d %Y").date()
            # last day of month
            if start.month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, start.month + 1, 1) - timedelta(days=1)
            label = start.strftime("%B %Y")
            return start.isoformat(), end.isoformat(), label
        except Exception:
            pass
    return None


class WhoZonAgent(BaseAgent):
    """Handles on-call scheduling via WhoZonCall — read and create schedules."""

    name = "WhoZonAgent"
    description = "Reads and creates on-call schedules in WhoZonCall (GMH)."
    capabilities = [
        "Show who is on call today or any date",
        "List schedule periods",
        "Create a new schedule period",
        "Add shifts to a schedule",
        "Assign a provider to a shift",
        "List service lines and shift types",
        "List providers",
    ]

    def __init__(self, database=None) -> None:
        super().__init__()
        self.database = database

    def supports(self, query: str) -> bool:
        q = query.lower()
        return any(kw in q for kw in _KEYWORDS)

    def handle(self, query: str, context: Optional[AgentContext] = None) -> AgentResponse:
        if not whozon_service.is_configured():
            return AgentResponse(
                agent=self.name,
                content=(
                    "WhoZonCall is not connected. "
                    "Add WHOZON_SUPABASE_URL and WHOZON_SERVICE_ROLE_KEY to JARVIS .env."
                ),
                status="warning",
            )

        q = query.lower()

        # ── CREATE SCHEDULE PERIOD ─────────────────────────────────────────────
        if any(kw in q for kw in ["create schedule", "new schedule", "create a schedule", "create new schedule"]):
            return self._handle_create_period(query, q)

        # ── ASSIGN PROVIDER TO SHIFT ───────────────────────────────────────────
        if any(kw in q for kw in ["assign", "put on"]):
            return self._handle_assign(query, q)

        # ── ADD SHIFT ─────────────────────────────────────────────────────────
        if any(kw in q for kw in ["add shift", "create shift", "schedule shift"]):
            return self._handle_add_shift(query, q)

        # ── WHO'S ON CALL ──────────────────────────────────────────────────────
        if any(kw in q for kw in ["who's on", "who is on", "whos on", "on call today",
                                    "coverage today", "on-call today"]):
            return self._handle_who_on_call(query, q)

        # ── SHIFTS ON DATE ────────────────────────────────────────────────────
        if any(kw in q for kw in ["shifts on", "shifts for", "schedule on", "schedule for"]):
            return self._handle_shifts_on_date(query, q)

        # ── LIST SCHEDULES ─────────────────────────────────────────────────────
        if any(kw in q for kw in ["list schedule", "show schedule", "all schedule", "schedule periods",
                                    "view schedule"]):
            return self._handle_list_periods()

        # ── LIST SERVICE LINES ─────────────────────────────────────────────────
        if any(kw in q for kw in ["service line", "service lines", "what lines", "what service"]):
            return self._handle_service_lines()

        # ── LIST PROVIDERS ────────────────────────────────────────────────────
        if any(kw in q for kw in ["provider", "providers", "who are", "staff"]):
            return self._handle_providers()

        # ── SHIFT TYPES ───────────────────────────────────────────────────────
        if any(kw in q for kw in ["shift type", "shift types"]):
            return self._handle_shift_types()

        # ── FALLBACK: today's on-call summary ────────────────────────────────
        return self._handle_who_on_call(query, q)

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _handle_who_on_call(self, query: str, q: str) -> AgentResponse:
        """Show who's on call on a given date."""
        target_date = _extract_date(query) or date.today()
        label = target_date.strftime("%A, %B %d %Y")

        shifts = whozon_service.get_shifts_on_date(target_date)
        provider_names = whozon_service.get_provider_names()
        service_lines = {sl["id"]: sl["name"] for sl in whozon_service.get_service_lines()}

        if not shifts:
            return AgentResponse(
                agent=self.name,
                content=f"No shifts found for {label}.",
            )

        lines = [f"**On Call — {label}** ({len(shifts)} shifts)\n"]
        primary = [s for s in shifts if not s.get("is_backup")]
        backup = [s for s in shifts if s.get("is_backup")]

        if primary:
            lines.append("**Primary Coverage:**")
            for s in primary:
                pname = provider_names.get(s.get("provider_id", ""), "Unassigned")
                sl = service_lines.get(s.get("service_line_id", ""), "Unknown")
                time_str = (
                    f"{_fmt_time(s['start_time'])} – {_fmt_time(s['end_time'])}"
                    if s.get("start_time") and s.get("end_time")
                    else ""
                )
                lines.append(f"  • {sl}: **{pname}** {time_str}")

        if backup:
            lines.append("\n**Backup:**")
            for s in backup:
                pname = provider_names.get(s.get("provider_id", ""), "Unassigned")
                sl = service_lines.get(s.get("service_line_id", ""), "Unknown")
                lines.append(f"  • {sl}: {pname}")

        return AgentResponse(agent=self.name, content="\n".join(lines), data={"shifts": shifts})

    def _handle_list_periods(self) -> AgentResponse:
        """List all schedule periods."""
        periods = whozon_service.get_all_periods(limit=10)
        if not periods:
            return AgentResponse(
                agent=self.name,
                content="No schedule periods found. Say 'create a new schedule for [month]' to get started.",
            )
        lines = ["**Schedule Periods:**"]
        for p in periods:
            status = p.get("status", "draft").upper()
            lines.append(
                f"  • **{p['name']}** ({p['start_date']} → {p['end_date']}) [{status}]"
            )
        return AgentResponse(agent=self.name, content="\n".join(lines), data={"periods": periods})

    def _handle_create_period(self, query: str, q: str) -> AgentResponse:
        """Create a new schedule period for a month."""
        result = _extract_month_range(query)
        if not result:
            return AgentResponse(
                agent=self.name,
                content=(
                    "Please specify a month, e.g. 'create a new schedule for April 2026' "
                    "or 'create schedule March 2026'."
                ),
            )
        start_date, end_date, label = result
        name = f"{label} On-Call Schedule"

        created = whozon_service.create_schedule_period(
            name=name,
            start_date=start_date,
            end_date=end_date,
        )
        if not created:
            return AgentResponse(
                agent=self.name,
                content=f"Failed to create the schedule period for {label}. Check JARVIS logs.",
                status="error",
            )

        period_id = created.get("id", "?")
        return AgentResponse(
            agent=self.name,
            content=(
                f"Created **{name}** ({start_date} to {end_date}) as a draft.\n\n"
                f"Period ID: `{period_id}`\n\n"
                "Next steps:\n"
                "  • Say 'add shift for NICU Day on March 5 2026' to add shifts\n"
                "  • Or open WhoZonCall to fill in the full schedule\n"
                "  • When ready: 'publish schedule [period ID]'"
            ),
            data={"period": created},
        )

    def _handle_add_shift(self, query: str, q: str) -> AgentResponse:
        """Add a shift to the current or specified period."""
        # Find the most recent period to attach this shift to
        periods = whozon_service.get_all_periods(limit=5)
        if not periods:
            return AgentResponse(
                agent=self.name,
                content="No schedule periods found. Create one first: 'create a new schedule for [month]'.",
            )

        # Use the most recent draft or active period
        target_period = None
        for p in periods:
            if p.get("status") in ("draft", "active"):
                target_period = p
                break
        if not target_period:
            target_period = periods[0]

        # Extract shift date
        shift_date = _extract_date(query)
        if not shift_date:
            return AgentResponse(
                agent=self.name,
                content="Please include a date, e.g. 'add shift for NICU Day on March 5 2026'.",
            )

        # Extract service line
        service_line_names = whozon_service.get_service_lines()
        matched_line = None
        for sl in service_line_names:
            if sl["name"].lower() in q or sl["code"].lower() in q:
                matched_line = sl
                break
        if not matched_line:
            lines_list = ", ".join(sl["name"] for sl in service_line_names[:6])
            return AgentResponse(
                agent=self.name,
                content=(
                    f"Couldn't identify a service line. Available: {lines_list}.\n"
                    "Example: 'add shift for NICU Day on March 5'"
                ),
            )

        created = whozon_service.create_shift(
            schedule_period_id=target_period["id"],
            service_line_id=matched_line["id"],
            shift_date=shift_date.isoformat(),
        )
        if not created:
            return AgentResponse(
                agent=self.name,
                content="Failed to create shift. Check JARVIS logs.",
                status="error",
            )

        return AgentResponse(
            agent=self.name,
            content=(
                f"Added **{matched_line['name']}** shift on {shift_date.strftime('%B %d, %Y')} "
                f"to schedule '{target_period['name']}'.\n"
                f"Shift ID: `{created.get('id', '?')}`\n"
                "Say 'assign [name] to this shift' or open WhoZonCall to assign a provider."
            ),
            data={"shift": created},
        )

    def _handle_assign(self, query: str, q: str) -> AgentResponse:
        """Assign a provider to a shift on a specific date/service line."""
        # Find provider by name
        # Pattern: "assign Dr. Smith" or "assign Smith" or "assign John Smith"
        name_match = (
            re.search(r"assign\s+(?:dr\.?\s+)?([A-Za-z][A-Za-z\-\']+(?:\s+[A-Za-z][A-Za-z\-\']+)?)", query, re.I)
            or re.search(r"put\s+(?:dr\.?\s+)?([A-Za-z][A-Za-z\-\']+)\s+on", query, re.I)
        )
        if not name_match:
            return AgentResponse(
                agent=self.name,
                content="Please specify a provider name, e.g. 'assign Dr. Smith to NICU Day on March 5'.",
            )

        provider_name = name_match.group(1).strip()
        providers = whozon_service.search_providers(provider_name)
        if not providers:
            return AgentResponse(
                agent=self.name,
                content=f"No provider found matching '{provider_name}'. Check the name or add them in WhoZonCall.",
            )
        if len(providers) > 1:
            names = ", ".join(f"{p['first_name']} {p['last_name']}" for p in providers[:5])
            return AgentResponse(
                agent=self.name,
                content=f"Multiple providers match '{provider_name}': {names}. Please be more specific.",
            )

        provider = providers[0]
        provider_id = provider["id"]
        provider_display = f"{provider['first_name']} {provider['last_name']}"

        # Find shift by date + service line
        shift_date = _extract_date(query)
        if not shift_date:
            return AgentResponse(
                agent=self.name,
                content=f"Please include a date, e.g. 'assign {provider_display} to NICU Day on March 5'.",
            )

        # Find service line
        service_lines = whozon_service.get_service_lines()
        matched_line = None
        for sl in service_lines:
            if sl["name"].lower() in q or sl["code"].lower() in q:
                matched_line = sl
                break

        # Get shifts on that date
        shifts_on_date = whozon_service.get_shifts_on_date(shift_date)
        if not shifts_on_date:
            return AgentResponse(
                agent=self.name,
                content=(
                    f"No shifts found on {shift_date.strftime('%B %d, %Y')}. "
                    "Create one first: 'add shift for NICU Day on [date]'."
                ),
            )

        # Find the right shift
        target_shift = None
        if matched_line:
            for s in shifts_on_date:
                if s.get("service_line_id") == matched_line["id"] and not s.get("provider_id"):
                    target_shift = s
                    break
            if not target_shift:
                # Try any shift on that service line even if already assigned
                for s in shifts_on_date:
                    if s.get("service_line_id") == matched_line["id"]:
                        target_shift = s
                        break
        else:
            # No service line specified — use first unassigned shift
            for s in shifts_on_date:
                if not s.get("provider_id"):
                    target_shift = s
                    break
            if not target_shift:
                target_shift = shifts_on_date[0]

        if not target_shift:
            return AgentResponse(
                agent=self.name,
                content=f"Couldn't find a matching shift on {shift_date.strftime('%B %d, %Y')}.",
            )

        updated = whozon_service.assign_provider(target_shift["id"], provider_id)
        if not updated:
            return AgentResponse(
                agent=self.name,
                content="Failed to assign provider. Check JARVIS logs.",
                status="error",
            )

        sl_names = {sl["id"]: sl["name"] for sl in service_lines}
        sl_name = sl_names.get(target_shift.get("service_line_id", ""), "shift")
        return AgentResponse(
            agent=self.name,
            content=(
                f"Assigned **{provider_display}** to **{sl_name}** "
                f"on {shift_date.strftime('%B %d, %Y')}."
            ),
            data={"shift": updated, "provider": provider},
        )

    def _handle_shifts_on_date(self, query: str, q: str) -> AgentResponse:
        """Show shifts for a specific date."""
        target_date = _extract_date(query) or date.today()
        return self._handle_who_on_call(query, q)

    def _handle_service_lines(self) -> AgentResponse:
        """List all active service lines."""
        lines = whozon_service.get_service_lines()
        if not lines:
            return AgentResponse(agent=self.name, content="No service lines found.")
        items = [f"  • **{sl['name']}** (`{sl['code']}`)" for sl in lines]
        return AgentResponse(
            agent=self.name,
            content="**Service Lines:**\n" + "\n".join(items),
            data={"service_lines": lines},
        )

    def _handle_providers(self) -> AgentResponse:
        """List all active providers."""
        providers = whozon_service.get_providers_list()
        if not providers:
            return AgentResponse(agent=self.name, content="No providers found in WhoZonCall.")
        items = [
            f"  • {p['first_name']} {p['last_name']} ({p.get('initials', '')})"
            for p in providers
        ]
        return AgentResponse(
            agent=self.name,
            content=f"**Providers ({len(providers)}):**\n" + "\n".join(items),
            data={"providers": providers},
        )

    def _handle_shift_types(self) -> AgentResponse:
        """List available shift types."""
        types = whozon_service.get_shift_types()
        if not types:
            return AgentResponse(agent=self.name, content="No shift types found.")
        items = [
            f"  • **{st['name']}** (`{st['code']}`) — "
            f"{st.get('start_time', '?')} to {st.get('end_time', '?')}"
            for st in types
        ]
        return AgentResponse(
            agent=self.name,
            content="**Shift Types:**\n" + "\n".join(items),
            data={"shift_types": types},
        )
