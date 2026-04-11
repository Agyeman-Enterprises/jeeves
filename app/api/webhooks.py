"""
Webhook API — Receives callbacks from AlrtMe, NEXUS, Ghexit.
This is how the outside world talks BACK to Jeeves.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.orchestrator import get_orchestrator
from app.schemas.events import EventSource, NormalizedEvent

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class GateResponsePayload(BaseModel):
    """Callback from AlrtMe when Akua responds to a gate request."""
    token: str
    action: str  # approve, reject, edit, table, review
    app_name: Optional[str] = None
    alert_id: Optional[str] = None
    message: Optional[str] = None  # Optional free-text response


class AlertResponsePayload(BaseModel):
    """Callback from AlrtMe when Akua responds to an alert."""
    alert_id: str
    response: str  # free text or approve/reject


class NexusDecisionPayload(BaseModel):
    """Callback from NEXUS when an autonomous decision needs approval."""
    decision_id: str
    action: str  # approve, reject, defer
    entity_id: Optional[str] = None
    agent_id: Optional[str] = None


# ── Gate Response (from AlrtMe gate-request flow) ──────────────────────
@router.post("/gate-response")
async def handle_gate_response(payload: GateResponsePayload):
    """
    AlrtMe calls this when Akua taps Approve/Reject/Edit on a gate request.
    Jeeves records the decision and takes action.
    """
    orch = get_orchestrator()

    LOGGER.info("[Webhook] Gate response: action=%s app=%s",
                payload.action, payload.app_name)

    # Record as event
    orch.event_store.ingest(NormalizedEvent(
        source=EventSource.MANUAL,
        raw_text=f"Gate response: {payload.action} for {payload.app_name or 'unknown'}"
                 + (f" — {payload.message}" if payload.message else ""),
        inferred_tags=["gate_response", payload.action, payload.app_name or "unknown"],
        valence=1.0 if payload.action == "approve" else -0.5 if payload.action == "reject" else 0.0,
    ))

    # TODO: Route to specific handler based on app_name
    # e.g., if app_name == "ContentForge" → publish content
    # e.g., if app_name == "claude-code" → continue build
    # For now, log and acknowledge

    return {
        "status": "received",
        "action": payload.action,
        "app_name": payload.app_name,
        "message": f"Jeeves recorded your '{payload.action}' response.",
    }


# ── Alert Response (from AlrtMe alert respond flow) ────────────────────
@router.post("/alert-response")
async def handle_alert_response(payload: AlertResponsePayload):
    """
    AlrtMe calls this when Akua responds to a regular alert.
    """
    orch = get_orchestrator()

    LOGGER.info("[Webhook] Alert response: id=%s response=%s",
                payload.alert_id[:12], payload.response[:50])

    orch.event_store.ingest(NormalizedEvent(
        source=EventSource.MANUAL,
        raw_text=f"Alert response: {payload.response}",
        inferred_tags=["alert_response"],
    ))

    return {"status": "received", "response": payload.response[:100]}


# ── NEXUS Decision (from NEXUS autonomous agents) ──────────────────────
@router.post("/nexus-decision")
async def handle_nexus_decision(payload: NexusDecisionPayload):
    """
    NEXUS calls this when an agent decision needs approval or has been made.
    """
    orch = get_orchestrator()

    LOGGER.info("[Webhook] Nexus decision: id=%s action=%s agent=%s",
                payload.decision_id, payload.action, payload.agent_id)

    orch.event_store.ingest(NormalizedEvent(
        source=EventSource.NEXUS,
        raw_text=f"Nexus decision: {payload.action} (agent={payload.agent_id}, entity={payload.entity_id})",
        inferred_tags=["nexus_decision", payload.action],
    ))

    return {"status": "received", "decision_id": payload.decision_id, "action": payload.action}
