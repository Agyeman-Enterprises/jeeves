"""
Review API — Query the brain's understanding.
Goals, contradictions, mimograph, interventions, profile.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter

from app.core.orchestrator import get_orchestrator

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/goals")
async def get_goals():
    """Get all goals ranked by effective weight."""
    orch = get_orchestrator()
    return {"goals": orch.weighting.get_goals()}


@router.get("/contradictions")
async def get_contradictions():
    """Get active contradictions with explanations."""
    orch = get_orchestrator()
    return {"contradictions": orch.contradictions.get_full_contradiction_report()}


@router.get("/interventions")
async def get_interventions(max_interventions: int = 3):
    """Get today's recommended interventions."""
    orch = get_orchestrator()
    interventions = orch.interventions.decide_interventions(max_interventions)
    return {"interventions": [i.model_dump() for i in interventions]}


@router.get("/what-matters-now")
async def what_matters_now():
    """Top 5 priorities by effective weight."""
    orch = get_orchestrator()
    return {"priorities": orch.planner.what_matters_now()}


@router.get("/what-to-drop")
async def what_to_drop():
    """Things to deprioritize based on behavior."""
    orch = get_orchestrator()
    return {"drop": orch.planner.what_to_drop()}


@router.get("/mimograph")
async def get_mimograph():
    """Get the full belief graph."""
    orch = get_orchestrator()
    return orch.mimograph.get_full_graph()


@router.get("/retirement")
async def retirement_countdown():
    """Retirement countdown and income gap."""
    orch = get_orchestrator()
    return orch.weighting.get_retirement_countdown()


@router.get("/events")
async def recent_events(hours: int = 24, limit: int = 50):
    """Get recent events."""
    orch = get_orchestrator()
    return {"events": orch.event_store.query(hours=hours, limit=limit)}
