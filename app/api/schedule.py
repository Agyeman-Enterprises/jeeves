"""
Schedule API — Day plans and check-ins.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.orchestrator import get_orchestrator

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/today")
async def today_plan():
    """Get today's plan."""
    orch = get_orchestrator()
    plan = orch.planner.generate_day_plan()
    return plan.model_dump()


@router.get("/briefing")
async def morning_briefing():
    """Generate the full morning briefing (LLM-powered)."""
    orch = get_orchestrator()
    return await orch.morning_briefing()


class CheckinAnswer(BaseModel):
    question: str
    answer: str


@router.post("/checkin")
async def answer_checkin(req: CheckinAnswer):
    """Answer a check-in question. Brain learns from the answer."""
    orch = get_orchestrator()

    # Ingest as event
    from app.schemas.events import EventSource, NormalizedEvent
    orch.event_store.ingest(NormalizedEvent(
        source=EventSource.CHECKIN,
        raw_text=f"Q: {req.question}\nA: {req.answer}",
        inferred_tags=["checkin", "self_report"],
    ))

    return {"status": "recorded", "insight": f"Answer to '{req.question[:50]}...' recorded."}
