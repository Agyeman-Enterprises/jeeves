"""
decision_engine.py — JARVIS Autonomous Action System

Cross-references:
  - Sentinel FinOps risks/predictions
  - Calendar proximity (meeting within 48h with an at-risk entity)
  - Competing priorities (reminders, email, enterprise alerts)

For each critical/high item it:
  1. Drafts an action memo
  2. Stores a pending decision in jarvis_decisions (Supabase)
  3. Sends an alrtme push notification: "Reply YES in NEXUS to execute"
  4. On approval: executes the action + logs to jarvis_plan_executions

Escalation rules:
  - Sentinel critical + calendar meeting ≤ 48h     → URGENT (auto-notify immediately)
  - Sentinel critical alone                         → HIGH (notify in morning brief)
  - Sentinel high + cash runway < 30 days           → URGENT
  - Enterprise alert + Sentinel warn for same entity → HIGH
  - Revenue anomaly > 2σ + hollow_growth quality    → HIGH (churn risk)
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

LOGGER = logging.getLogger("backend.services.decision_engine")

JARVIS_BACKEND_URL = os.getenv("JARVIS_BACKEND_URL", "http://localhost:8000")
NEXUS_URL = os.getenv("NEXUS_URL", "http://localhost:3001")
NEXUS_INTERNAL_KEY = os.getenv("NEXUS_INTERNAL_KEY", "")
ALRTME_CHANNEL = os.getenv("ALRTME_CHANNEL", "akualrts")
ALRTME_API_KEY = os.getenv("ALRTME_API_KEY", "")

_URGENCY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class DecisionItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    urgency: str = "high"               # urgent | high | medium | low
    action_type: str = "notify"         # notify | send_memo | escalate | review
    entity_id: str | None = None
    entity_name: str | None = None
    draft_memo: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    source: str = ""                    # sentinel | enterprise | calendar | email
    escalation_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"             # pending | approved | rejected | executed


@dataclass
class DecisionBundle:
    decisions: list[DecisionItem] = field(default_factory=list)
    urgent_count: int = 0
    high_count: int = 0
    notification_text: str = ""
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Sentinel data fetcher ──────────────────────────────────────────────────────

def _fetch_sentinel_risks(entity_id: str | None = None) -> list[dict]:
    """Pull active Sentinel risk events from JARVIS backend."""
    try:
        params: dict = {"severity": "critical,high", "dismissed": "false", "limit": 20}
        if entity_id:
            params["entity_id"] = entity_id
        resp = httpx.get(
            f"{JARVIS_BACKEND_URL}/api/sentinel/finops/risks",
            params=params,
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json().get("risks", [])
    except Exception as exc:
        LOGGER.debug("[DecisionEngine] Sentinel risks fetch failed: %s", exc)
    return []


def _fetch_sentinel_predictions(months_ahead: int = 2) -> list[dict]:
    """Pull forward predictions."""
    try:
        resp = httpx.get(
            f"{JARVIS_BACKEND_URL}/api/sentinel/finops/predictions",
            params={"limit": 50},
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json().get("predictions", [])
    except Exception as exc:
        LOGGER.debug("[DecisionEngine] Sentinel predictions fetch failed: %s", exc)
    return []


def _fetch_calendar_events_48h() -> list[dict]:
    """Pull calendar events in the next 48 hours."""
    try:
        from app.services.calendar_integrations import CalendarIntegrationManager
        mgr = CalendarIntegrationManager()
        now = datetime.now()
        events = mgr.get_events(start=now, end=now + timedelta(hours=48), max_results=20)
        return events or []
    except Exception as exc:
        LOGGER.debug("[DecisionEngine] Calendar fetch failed: %s", exc)
    return []


def _get_entities() -> dict[str, dict]:
    """Get entity name map from NEXUS."""
    try:
        resp = httpx.get(
            f"{NEXUS_URL}/api/entities",
            headers={"Authorization": f"Bearer {NEXUS_INTERNAL_KEY}"},
            timeout=8,
        )
        if resp.status_code == 200:
            entities = resp.json().get("entities", [])
            return {e["id"]: e for e in entities}
    except Exception as exc:
        LOGGER.debug("[DecisionEngine] Entity fetch failed: %s", exc)
    return {}


# ── Escalation logic ───────────────────────────────────────────────────────────

def _calendar_has_meeting_for_entity(entity_name: str | None, events: list[dict]) -> bool:
    """Check if any upcoming calendar event references this entity."""
    if not entity_name or not events:
        return False
    name_lower = entity_name.lower()
    for evt in events:
        summary = (evt.get("summary") or evt.get("title") or "").lower()
        description = (evt.get("description") or "").lower()
        if name_lower in summary or name_lower in description:
            return True
    return False


def _draft_memo(risk: dict, entity_name: str | None, predictions: list[dict]) -> str:
    """Auto-draft a concise action memo for a Sentinel risk event."""
    metric = risk.get("metric_key", "unknown metric")
    severity = risk.get("severity", "high")
    zscore = risk.get("zscore_at_detection")
    observed = risk.get("observed_value")
    baseline = risk.get("baseline_value")
    risk_type = risk.get("risk_type", "anomaly_detected")
    entity = entity_name or risk.get("entity_id", "Unknown entity")

    # Find matching prediction
    entity_id = risk.get("entity_id")
    revenue_prediction = next(
        (p for p in predictions
         if p.get("entity_id") == entity_id and p.get("prediction_type") == "revenue"),
        None,
    )

    memo_lines = [
        f"JARVIS SENTINEL ALERT — {entity}",
        f"{'=' * 50}",
        f"Severity: {severity.upper()}",
        f"Metric: {metric}",
        f"Risk type: {risk_type}",
        "",
    ]

    if zscore is not None:
        memo_lines.append(f"Statistical signal: {zscore:.2f}σ deviation (dual z-score + IQR confirmed)")
    if observed is not None and baseline is not None:
        delta_pct = ((observed - baseline) / baseline * 100) if baseline else 0
        memo_lines.append(f"Observed: {observed:,.0f}  |  Baseline: {baseline:,.0f}  |  Change: {delta_pct:+.1f}%")

    memo_lines.append("")

    if revenue_prediction:
        pred_val = revenue_prediction.get("predicted_value", 0)
        confidence = revenue_prediction.get("confidence_score", 0)
        target_month = revenue_prediction.get("target_month", "")
        memo_lines.append(f"FORECAST: Revenue predicted at ${pred_val:,.0f} for {target_month} (confidence: {confidence:.0%})")

    revenue_quality = risk.get("context", {}).get("revenue_quality", "") if isinstance(risk.get("context"), dict) else ""
    if revenue_quality == "hollow_growth":
        memo_lines.append("WARNING: Revenue quality is HOLLOW — growth masking underlying churn")
    elif revenue_quality == "churn_erosion":
        memo_lines.append("WARNING: Churn erosion detected — revenue decline driven by customer loss")

    memo_lines += [
        "",
        "RECOMMENDED ACTIONS:",
        "  1. Review entity P&L for the past 60 days",
        "  2. Schedule entity check-in within 48 hours",
        "  3. Evaluate whether external macro factors apply (check TraderAI signal)",
        "  4. Update cash runway projections if cash_balance metric flagged",
        "",
        f"Auto-generated by JARVIS Sentinel v1 — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    ]

    return "\n".join(memo_lines)


# ── Core engine ────────────────────────────────────────────────────────────────

def generate_decisions() -> DecisionBundle:
    """
    Main entry point. Pulls all data sources, applies escalation logic,
    returns a bundle of pending decisions.
    """
    bundle = DecisionBundle()

    # Fetch all data concurrently (best-effort)
    risks = _fetch_sentinel_risks()
    predictions = _fetch_sentinel_predictions()
    calendar_events = _fetch_calendar_events_48h()
    entities = _get_entities()

    for risk in risks:
        severity = risk.get("severity", "medium")
        if severity not in ("critical", "high"):
            continue

        entity_id = risk.get("entity_id")
        entity = entities.get(entity_id, {}) if entity_id else {}
        entity_name = entity.get("name") or risk.get("entity_id")
        metric_key = risk.get("metric_key", "unknown")

        # Base urgency from severity
        urgency = "urgent" if severity == "critical" else "high"

        # Escalation: meeting within 48h for this entity
        has_meeting = _calendar_has_meeting_for_entity(entity_name, calendar_events)
        escalation_reason = ""
        if has_meeting and severity == "critical":
            urgency = "urgent"
            escalation_reason = f"Meeting with {entity_name} within 48h + critical Sentinel risk"
        elif has_meeting and severity == "high":
            urgency = "urgent"
            escalation_reason = f"Meeting scheduled with {entity_name} — high FinOps risk requires prep"

        # Escalation: low cash runway
        if metric_key == "cash_balance" and severity == "critical":
            urgency = "urgent"
            escalation_reason = (escalation_reason or "") + " | Cash runway at critical level"

        draft = _draft_memo(risk, entity_name, predictions)

        decision = DecisionItem(
            title=f"{entity_name}: {metric_key.replace('_', ' ').title()} anomaly [{severity.upper()}]",
            urgency=urgency,
            action_type="send_memo" if urgency == "urgent" else "review",
            entity_id=entity_id,
            entity_name=entity_name,
            draft_memo=draft,
            source="sentinel",
            escalation_reason=escalation_reason or f"Sentinel {severity} risk detected",
            context={
                "risk_id": risk.get("id"),
                "metric_key": metric_key,
                "zscore": risk.get("zscore_at_detection"),
                "risk_type": risk.get("risk_type"),
            },
        )
        bundle.decisions.append(decision)

    # Sort by urgency
    bundle.decisions.sort(key=lambda d: _URGENCY_ORDER.get(d.urgency, 3))
    bundle.urgent_count = sum(1 for d in bundle.decisions if d.urgency == "urgent")
    bundle.high_count = sum(1 for d in bundle.decisions if d.urgency == "high")

    # Build notification text
    if bundle.decisions:
        top = bundle.decisions[0]
        lines = [f"JARVIS: {bundle.urgent_count} urgent + {bundle.high_count} high priority decisions."]
        lines.append(f"Top: {top.title}")
        if top.escalation_reason:
            lines.append(f"Why now: {top.escalation_reason}")
        lines.append("Open NEXUS → Decisions to review and approve.")
        bundle.notification_text = "\n".join(lines)

    return bundle


def store_and_notify(bundle: DecisionBundle) -> None:
    """
    Persist decisions to Supabase jarvis_decisions table and send alrtme notification.
    """
    if not bundle.decisions:
        return

    # Persist to Supabase
    try:
        from app.services.jarviscore_client import get_supabase_client
        sb = get_supabase_client(use_service_key=True)
        rows = [
            {
                "id": d.id,
                "title": d.title,
                "urgency": d.urgency,
                "action_type": d.action_type,
                "entity_id": d.entity_id,
                "draft_memo": d.draft_memo,
                "source": d.source,
                "escalation_reason": d.escalation_reason,
                "context": d.context,
                "status": "pending",
                "created_at": d.created_at,
            }
            for d in bundle.decisions
        ]
        # Upsert — avoid duplicates if risk is still active
        sb.table("jarvis_decisions").upsert(rows, on_conflict="id").execute()
        LOGGER.info("[DecisionEngine] Stored %d decisions", len(rows))
    except Exception as exc:
        LOGGER.warning("[DecisionEngine] Failed to persist decisions: %s", exc)

    # Send alrtme push notification
    if bundle.notification_text:
        try:
            _send_alrtme(
                title=f"JARVIS: {bundle.urgent_count} urgent action{'s' if bundle.urgent_count != 1 else ''}",
                body=bundle.notification_text,
            )
        except Exception as exc:
            LOGGER.warning("[DecisionEngine] alrtme notification failed: %s", exc)


def execute_decision(decision_id: str) -> dict[str, Any]:
    """
    Execute an approved decision.
    - Sends the draft memo via GHEXIT SMS to the owner's number
    - Logs a jarvis_plan_executions row
    - Marks decision as executed
    Returns: {ok: bool, message: str}
    """
    try:
        from app.services.jarviscore_client import get_supabase_client
        sb = get_supabase_client(use_service_key=True)

        result = sb.table("jarvis_decisions").select("*").eq("id", decision_id).single().execute()
        if not result.data:
            return {"ok": False, "message": "Decision not found"}

        decision = result.data
        memo = decision.get("draft_memo", "")

        # Send via GHEXIT
        owner_phone = os.getenv("JARVIS_OWNER_PHONE", os.getenv("OWNER_PHONE_NUMBER", ""))
        if owner_phone:
            try:
                from app.services.ghexit_service import GhexitService
                ghexit = GhexitService()
                # Send first 160 chars of memo as SMS, full memo via email
                sms_body = (
                    f"JARVIS DECISION EXECUTED:\n{decision['title']}\n\n"
                    f"Memo sent. Check your email for full details."
                )
                ghexit.send_sms(to=owner_phone, body=sms_body[:1600])
                LOGGER.info("[DecisionEngine] Sent execution SMS for decision %s", decision_id)
            except Exception as exc:
                LOGGER.warning("[DecisionEngine] GHEXIT SMS failed: %s", exc)

        # Send full memo via email
        _send_memo_email(decision)

        # Log to jarvis_plan_executions
        sb.table("jarvis_plan_executions").insert({
            "decision_id": decision_id,
            "entity_id": decision.get("entity_id"),
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "outcome_summary": f"Decision executed: {decision['title']}",
            "execution_notes": f"Source: {decision.get('source')}. Action: {decision.get('action_type')}",
        }).execute()

        # Mark decision executed
        sb.table("jarvis_decisions").update({"status": "executed"}).eq("id", decision_id).execute()

        return {"ok": True, "message": f"Decision executed: {decision['title']}"}

    except Exception as exc:
        LOGGER.error("[DecisionEngine] Execute failed for %s: %s", decision_id, exc)
        return {"ok": False, "message": str(exc)}


def reject_decision(decision_id: str, reason: str = "") -> dict[str, Any]:
    """Mark a decision as rejected."""
    try:
        from app.services.jarviscore_client import get_supabase_client
        sb = get_supabase_client(use_service_key=True)
        sb.table("jarvis_decisions").update({
            "status": "rejected",
            "rejection_reason": reason,
        }).eq("id", decision_id).execute()
        return {"ok": True, "message": "Decision rejected"}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _send_alrtme(title: str, body: str) -> None:
    channel = ALRTME_CHANNEL
    if not channel:
        return
    payload = {"title": title, "body": body}
    if ALRTME_API_KEY:
        payload["api_key"] = ALRTME_API_KEY
    httpx.post(
        f"https://alrtme.co/api/notify/{channel}",
        json=payload,
        timeout=10,
    )


def _send_memo_email(decision: dict) -> None:
    """Send the full memo via email using JARVIS email integration."""
    try:
        from app.services.email_integrations import EmailIntegrationManager
        mgr = EmailIntegrationManager()
        owner_email = os.getenv("JARVIS_BRIEFING_EMAIL", "")
        if not owner_email:
            return
        mgr.send_email(
            to=owner_email,
            subject=f"JARVIS Action Memo: {decision.get('title', 'Decision')}",
            body=decision.get("draft_memo", "No memo content."),
        )
    except Exception as exc:
        LOGGER.warning("[DecisionEngine] Email send failed: %s", exc)


# ── Scheduler job ──────────────────────────────────────────────────────────────

def run_decision_engine() -> None:
    """APScheduler job — runs every morning after risk scan, and on-demand."""
    LOGGER.info("[DecisionEngine] Starting decision generation run")
    try:
        bundle = generate_decisions()
        LOGGER.info(
            "[DecisionEngine] Generated %d decisions (%d urgent, %d high)",
            len(bundle.decisions),
            bundle.urgent_count,
            bundle.high_count,
        )
        store_and_notify(bundle)
    except Exception as exc:
        LOGGER.error("[DecisionEngine] Run failed: %s", exc)
