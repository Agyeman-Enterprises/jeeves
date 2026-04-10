"""
Intervention Engine — Layer 6: Decides what to do about what it knows.
ask / remind / reschedule / escalate / delegate / stay quiet
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List

from app.modeling.contradiction_engine import ContradictionEngine
from app.modeling.weighting_engine import WeightingEngine
from app.schemas.schedule import Intervention, InterventionType

LOGGER = logging.getLogger(__name__)


class InterventionEngine:
    """
    Jeeves decides whether to speak or stay quiet.
    Not every contradiction needs surfacing. Not every goal needs a nudge.
    The engine weighs urgency, user state, and intervention fatigue.
    """

    def __init__(self, weighting: WeightingEngine, contradictions: ContradictionEngine):
        self.weighting = weighting
        self.contradictions = contradictions
        self._recent_interventions: List[Dict] = []  # in-memory for now

    def decide_interventions(self, max_interventions: int = 3) -> List[Intervention]:
        """
        Generate today's interventions based on current state.
        Returns at most max_interventions, highest urgency first.
        """
        candidates: List[Intervention] = []

        # 1. Critical contradictions → ASK
        contradiction_report = self.contradictions.get_full_contradiction_report()
        for c in contradiction_report:
            if c["severity"] == "critical":
                candidates.append(Intervention(
                    intervention_type=InterventionType.ASK,
                    target_goal=c["goal_id"],
                    message=c["question"],
                    urgency=0.9,
                    channel="sms",
                ))
            elif c["severity"] == "warning":
                candidates.append(Intervention(
                    intervention_type=InterventionType.REMIND,
                    target_goal=c["goal_id"],
                    message=c["question"],
                    urgency=0.6,
                    channel="pwa",
                ))

        # 2. High-weight goals with no recent action → REMIND
        goals = self.weighting.get_goals()
        for g in goals:
            if g.get("effective_weight", 0) > 0.7:
                last_evidence = g.get("last_evidence_at")
                if last_evidence:
                    try:
                        last_dt = datetime.fromisoformat(str(last_evidence).replace("Z", "+00:00"))
                        days_since = (datetime.utcnow() - last_dt.replace(tzinfo=None)).days
                        if days_since > 5:
                            candidates.append(Intervention(
                                intervention_type=InterventionType.REMIND,
                                target_goal=g["goal_id"],
                                message=f"It's been {days_since} days since you worked on '{g['label']}'. This is your #{goals.index(g)+1} priority.",
                                urgency=min(0.8, 0.4 + days_since * 0.05),
                                channel="pwa",
                            ))
                    except (ValueError, TypeError):
                        pass

        # 3. Retirement countdown urgency
        countdown = self.weighting.get_retirement_countdown()
        if countdown["days_left"] < 200:
            candidates.append(Intervention(
                intervention_type=InterventionType.ESCALATE,
                message=f"Retirement in {countdown['days_left']} days. You need ${countdown['monthly_needed']:,}/month. Are we on track?",
                urgency=0.85,
                channel="sms",
            ))

        # 4. Business delegation opportunities → DELEGATE
        business_goals = [g for g in goals if g.get("category") == "business" and g.get("effective_weight", 0) > 0.5]
        for bg in business_goals[:1]:
            candidates.append(Intervention(
                intervention_type=InterventionType.DELEGATE,
                target_goal=bg["goal_id"],
                message=f"Sending Nexus to audit '{bg['label']}' repos and create marketing plan.",
                urgency=0.5,
                channel="pwa",
            ))

        # Sort by urgency, take top N
        candidates.sort(key=lambda i: i.urgency, reverse=True)

        # Apply intervention fatigue: don't send same goal twice
        seen_goals = set()
        filtered = []
        for c in candidates:
            goal = c.target_goal or "general"
            if goal not in seen_goals:
                seen_goals.add(goal)
                filtered.append(c)
            if len(filtered) >= max_interventions:
                break

        return filtered

    def should_stay_quiet(self) -> bool:
        """
        Sometimes the best intervention is no intervention.
        Stay quiet if:
        - No critical contradictions
        - All top goals have recent evidence
        - It's outside work hours (handled by scheduler)
        """
        contradictions = self.weighting.get_contradictions()
        critical = [c for c in contradictions if c["severity"] == "critical"]
        return len(critical) == 0
