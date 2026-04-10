"""
Planner — Layer 5: Generates day plans from weights + constraints.
Considers: effective weights, calendar, energy profile, blockers, deadlines, recovery.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.modeling.weighting_engine import WeightingEngine
from app.modeling.mimograph import Mimograph
from app.schemas.schedule import DayPlan, InterventionType, TimeBlock

LOGGER = logging.getLogger(__name__)


class Planner:
    """
    Generates "what matters now", "what to drop", and "what to ask".
    """

    def __init__(self, weighting: WeightingEngine, mimograph: Mimograph):
        self.weighting = weighting
        self.mimograph = mimograph

    def generate_day_plan(self, calendar_events: List[Dict] = None,
                          energy_profile: str = "normal") -> DayPlan:
        """
        Build today's plan from:
        - Top goals by effective weight
        - Calendar constraints (hospital shifts, appointments)
        - Energy profile (post_shift_low, normal, high)
        - Active blockers
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        goals = self.weighting.get_goals()
        calendar_events = calendar_events or []

        # Sort goals by effective weight
        actionable = [g for g in goals if g.get("effective_weight", 0) > 0.1]

        # Determine fixed blocks from calendar
        fixed_blocks = []
        for event in calendar_events:
            fixed_blocks.append(TimeBlock(
                start=datetime.fromisoformat(event["start"]) if isinstance(event.get("start"), str) else datetime.utcnow(),
                end=datetime.fromisoformat(event["end"]) if isinstance(event.get("end"), str) else datetime.utcnow() + timedelta(hours=1),
                label=event.get("summary", "Calendar event"),
                category="work" if "shift" in event.get("summary", "").lower() else "other",
                is_fixed=True,
                source="calendar",
            ))

        # Compute available hours
        has_shift = any("shift" in b.label.lower() or "hospital" in b.label.lower() for b in fixed_blocks)

        # Top priorities = top 3-5 goals by effective weight that aren't blocked
        blocked_goals = set()
        for g in actionable:
            blockers = self.mimograph.what_blocks(g["goal_id"])
            if any(b["weight"] > 0.8 for b in blockers):
                blocked_goals.add(g["goal_id"])

        top_priorities = [g["goal_id"] for g in actionable[:5] if g["goal_id"] not in blocked_goals]

        # What to drop: low effective weight + low contradiction (nobody cares)
        what_to_drop = [
            g["label"] for g in goals
            if g.get("effective_weight", 0) < 0.2 and g.get("contradiction_score", 0) < 0.2
        ]

        # What to ask: high contradiction or high uncertainty
        what_to_ask = []
        contradictions = self.weighting.get_contradictions()
        for c in contradictions[:2]:
            what_to_ask.append(
                f"'{c['label']}': stated {c['stated_weight']:.0%} vs revealed {c['revealed_weight']:.0%}. What's happening?"
            )

        # Energy adjustment
        if has_shift:
            energy_profile = "post_shift_low"
        elif energy_profile == "unknown":
            energy_profile = "normal"

        return DayPlan(
            date=today,
            blocks=fixed_blocks,
            top_priorities=top_priorities,
            what_to_drop=what_to_drop[:3],
            what_to_ask=what_to_ask,
            energy_profile=energy_profile,
        )

    def what_matters_now(self) -> List[Dict]:
        """Top 5 things that matter right now, ranked by effective weight."""
        goals = self.weighting.get_goals()
        return [
            {"goal_id": g["goal_id"], "label": g["label"],
             "effective_weight": g.get("effective_weight", 0),
             "contradiction_score": g.get("contradiction_score", 0)}
            for g in goals[:5]
        ]

    def what_to_drop(self) -> List[Dict]:
        """Things that should be deprioritized based on behavior."""
        goals = self.weighting.get_goals()
        return [
            {"goal_id": g["goal_id"], "label": g["label"],
             "effective_weight": g.get("effective_weight", 0),
             "reason": "Low effective weight + no recent action"}
            for g in goals
            if g.get("effective_weight", 0) < 0.15
        ]
