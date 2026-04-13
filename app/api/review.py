"""
Review API — Query the brain's understanding.
Goals, suggestions, mimograph, profile.
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


@router.get("/suggestions")
async def get_suggestions(max_suggestions: int = 4):
    """Get today's action-first suggestions from JJ."""
    orch = get_orchestrator()
    suggestions = orch.suggestions.generate(max_suggestions=max_suggestions)
    return {"suggestions": [s.to_dict() for s in suggestions]}


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


@router.get("/events")
async def recent_events(hours: int = 24, limit: int = 50):
    """Get recent events."""
    orch = get_orchestrator()
    return {"events": orch.event_store.query(hours=hours, limit=limit)}


@router.get("/health")
async def brain_health():
    """Brain status and service health."""
    orch = get_orchestrator()
    return await orch.health_check()
