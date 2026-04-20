"""Brain API — goals, belief nodes, observations, briefings, contradictions."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.brain.mimograph import get_mimograph
from app.brain.user_model import UserModel

router = APIRouter(prefix="/brain", tags=["brain"])

_user_model = UserModel()


# ── Request models ─────────────────────────────────────────────────────

class ObserveRequest(BaseModel):
    observation_type: str          # action | skip | defer | statement | completion
    category: str
    description: str
    value: float = 1.0
    related_goal: Optional[str] = None
    source: str = "manual"


class AnswerRequest(BaseModel):
    question: str
    answer: str
    related_goal: Optional[str] = None


class NodeUpdateRequest(BaseModel):
    node_id: str
    evidence: str
    strength_delta: float = 0.05


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/observe")
async def observe(req: ObserveRequest):
    """Record a behavioral observation and update goal weights."""
    _user_model.record_observation(
        observation_type=req.observation_type,
        category=req.category,
        description=req.description,
        value=req.value,
        related_goal=req.related_goal,
        source=req.source,
    )
    return {"status": "recorded"}


@router.get("/goals")
async def get_goals():
    """All goals ranked by effective_weight."""
    return {"goals": _user_model.get_goals()}


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    goal = _user_model.get_goal(goal_id)
    if not goal:
        raise HTTPException(404, f"Goal {goal_id} not found")
    return goal


@router.get("/contradictions")
async def get_contradictions():
    """Goals where stated importance diverges from revealed behavior."""
    return {"contradictions": _user_model.get_contradictions()}


@router.get("/traits")
async def get_traits():
    """Belief nodes of type trait."""
    return {"traits": _user_model.get_nodes(node_type="trait")}


@router.get("/nodes")
async def get_nodes(node_type: Optional[str] = None):
    """All belief nodes, optionally filtered by type."""
    return {"nodes": _user_model.get_nodes(node_type=node_type)}


@router.post("/nodes/update")
async def update_node(req: NodeUpdateRequest):
    """Update a belief node's strength from evidence."""
    _user_model.update_node(req.node_id, req.evidence, req.strength_delta)
    return {"status": "updated"}


@router.get("/profile")
async def get_profile():
    """Full profile summary for briefings and LLM context."""
    return _user_model.get_profile_summary()


@router.get("/retirement")
async def get_retirement():
    """Days left and income gap to EOY 2026 retirement target."""
    return _user_model.get_retirement_countdown()


@router.get("/briefing")
async def get_briefing():
    """Generate morning intelligence briefing."""
    return get_mimograph().generate_morning_briefing()


@router.get("/questions")
async def get_questions():
    """Generate today's targeted check-in questions."""
    return {"questions": get_mimograph().generate_daily_questions()}


@router.post("/answer")
async def answer_question(req: AnswerRequest):
    """Record an answer to a check-in question."""
    return get_mimograph().answer_question(req.question, req.answer, req.related_goal)


@router.post("/reflect")
async def run_reflection():
    """Trigger the reflection cycle (normally runs nightly)."""
    reflections = get_mimograph().run_reflection_cycle()
    return {"reflections": reflections, "count": len(reflections)}


@router.get("/insights")
async def get_insights():
    """Full intelligence report: profile + contradictions + traits + reflections."""
    return get_mimograph().get_insight_report()


@router.get("/status")
async def brain_status():
    """Brain health: goal count, node count, event count."""
    goals = _user_model.get_goals()
    nodes = _user_model.get_nodes()
    events = _user_model.get_recent_observations(hours=168)
    return {
        "goals_tracked": len(goals),
        "belief_nodes": len(nodes),
        "events_last_7d": len(events),
        "goals_with_data": sum(1 for g in goals if g.get("action_count", 0) + g.get("skip_count", 0) > 0),
        "critical_contradictions": sum(1 for g in goals if g.get("contradiction_score", 0) > 0.5),
    }
