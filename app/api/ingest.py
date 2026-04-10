"""
Ingest API — Layer 1: Normalize and store events from any source.
Voice, text, SMS, email, calendar, OCR, repo events all come through here.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.orchestrator import get_orchestrator
from app.schemas.events import EventModality, EventSource, NormalizedEvent

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    source: str  # voice, text, sms, email, calendar, ocr, file, repo, manual
    raw_text: str
    modality: str = "text"
    entities: List[str] = []
    linked_goals: List[str] = []
    valence: float = 0.0
    duration_minutes: Optional[float] = None
    self_reported_intent: Optional[str] = None
    structured_payload: Dict = {}


@router.post("")
async def ingest_event(req: IngestRequest):
    """Ingest a normalized event from any source."""
    orch = get_orchestrator()

    event = NormalizedEvent(
        source=EventSource(req.source) if req.source in EventSource.__members__.values() else EventSource.MANUAL,
        modality=EventModality(req.modality) if req.modality in EventModality.__members__.values() else EventModality.TEXT,
        raw_text=req.raw_text,
        entities=req.entities,
        linked_goals=req.linked_goals,
        valence=req.valence,
        duration_minutes=req.duration_minutes,
        self_reported_intent=req.self_reported_intent,
        structured_payload=req.structured_payload,
    )

    event_id = orch.event_store.ingest(event)

    # If linked to goals, update weighting
    for goal_id in req.linked_goals:
        orch.weighting.record_evidence(goal_id, req.valence, req.raw_text[:100])

    return {"status": "ingested", "event_id": event_id}


@router.post("/observe")
async def observe(observation_type: str = "action", category: str = "general",
                  description: str = "", value: float = 1.0,
                  related_goal: Optional[str] = None):
    """Quick observation endpoint — shorthand for common behaviors."""
    orch = get_orchestrator()

    event = NormalizedEvent(
        source=EventSource.MANUAL,
        raw_text=f"[{observation_type}] {category}: {description}",
        valence=value if observation_type in ("action", "completion") else -abs(value) if observation_type in ("skip", "defer") else 0.0,
        linked_goals=[related_goal] if related_goal else [],
        inferred_tags=[category, observation_type],
    )
    event_id = orch.event_store.ingest(event)

    if related_goal:
        score = value if observation_type in ("action", "completion") else -0.5
        orch.weighting.record_evidence(related_goal, score, description)

    return {"status": "observed", "event_id": event_id}
