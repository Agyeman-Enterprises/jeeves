"""
Weighting Engine — Layer 4: The ranking center.
Computes effective weights from stated, revealed, persistence, recency, sacrifice.
Detects contradictions. Applies decay. The heart of Jeeves's understanding.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.db import get_db
from app.memory.event_store import EventStore
from app.schemas.goals import SEED_GOALS, Goal

LOGGER = logging.getLogger(__name__)

GOALS_TABLE = "jeeves_goals"


class WeightingEngine:
    """
    For each goal:
    - stated_weight: what Akua says (updated from check-ins)
    - revealed_weight: what behavior shows (updated from events)
    - effective_weight: f(stated, revealed, persistence, recency, sacrifice)
    - contradiction_score: how misaligned stated vs revealed
    - volatility: how much effective_weight fluctuates
    - confidence: how much data we have
    """

    def __init__(self, event_store: EventStore = None):
        self.event_store = event_store or EventStore()
        self._ensure_seed()

    def _ensure_seed(self):
        db = get_db()
        if not db:
            return
        try:
            existing = db.table(GOALS_TABLE).select("goal_id").limit(1).execute()
            if not existing.data:
                LOGGER.info("[Weighting] Seeding %d goals", len(SEED_GOALS))
                for g in SEED_GOALS:
                    db.table(GOALS_TABLE).insert(g.model_dump(mode="json")).execute()
        except Exception as exc:
            LOGGER.warning("[Weighting] Seed error: %s", exc)

    # ── Core: get all goals ────────────────────────────────────────────
    def get_goals(self) -> List[Dict]:
        db = get_db()
        if not db:
            return []
        try:
            res = db.table(GOALS_TABLE).select("*").order("effective_weight", desc=True).execute()
            return res.data or []
        except Exception as exc:
            LOGGER.error("[Weighting] get_goals error: %s", exc)
            return []

    def get_goal(self, goal_id: str) -> Optional[Dict]:
        db = get_db()
        if not db:
            return None
        try:
            res = db.table(GOALS_TABLE).select("*").eq("goal_id", goal_id).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception as exc:
            LOGGER.error("[Weighting] get_goal error: %s", exc)
            return None

    # ── Record evidence ────────────────────────────────────────────────
    def record_evidence(self, goal_id: str, action_score: float, description: str = ""):
        """
        Record behavioral evidence for a goal.
        action_score: 1.0 = strongly supports, -1.0 = strongly contradicts
        """
        db = get_db()
        if not db:
            return
        goal = self.get_goal(goal_id)
        if not goal:
            LOGGER.warning("[Weighting] Unknown goal: %s", goal_id)
            return

        try:
            # Update revealed weight via exponential moving average
            alpha = 0.12  # learning rate
            old_revealed = goal.get("revealed_weight", 0.0)
            # Normalize action_score from [-1,1] to [0,1] for weight
            normalized = (action_score + 1.0) / 2.0
            new_revealed = (alpha * normalized) + ((1 - alpha) * old_revealed)
            new_revealed = max(0.0, min(1.0, new_revealed))

            # Update counts
            ac = goal.get("action_count", 0)
            sc = goal.get("skip_count", 0)
            dc = goal.get("defer_count", 0)
            if action_score > 0.3:
                ac += 1
            elif action_score < -0.3:
                sc += 1
            else:
                dc += 1

            # Compute effective weight
            effective = self._compute_effective(
                stated=goal.get("stated_weight", 0.5),
                revealed=new_revealed,
                action_count=ac,
                skip_count=sc,
                defer_count=dc,
                last_evidence_at=datetime.utcnow(),
                decay_half_life=goal.get("decay_half_life_days", 30),
            )

            # Contradiction score
            contradiction = self._compute_contradiction(
                stated=goal.get("stated_weight", 0.5),
                revealed=new_revealed,
                is_core=(goal.get("stated_weight", 0) >= 0.8),
            )

            # Confidence
            total_obs = ac + sc + dc
            confidence = min(1.0, total_obs / 30)

            db.table(GOALS_TABLE).update({
                "revealed_weight": round(new_revealed, 4),
                "effective_weight": round(effective, 4),
                "contradiction_score": round(contradiction, 4),
                "confidence": round(confidence, 4),
                "action_count": ac,
                "skip_count": sc,
                "defer_count": dc,
                "last_evidence_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("goal_id", goal_id).execute()

            LOGGER.info("[Weighting] %s: revealed=%.2f effective=%.2f contradiction=%.2f",
                        goal_id, new_revealed, effective, contradiction)
        except Exception as exc:
            LOGGER.error("[Weighting] record_evidence error: %s", exc)

    # ── Compute effective weight ───────────────────────────────────────
    def _compute_effective(
        self, stated: float, revealed: float,
        action_count: int, skip_count: int, defer_count: int,
        last_evidence_at: Optional[datetime], decay_half_life: float,
    ) -> float:
        """
        effective_weight = f(stated, revealed, persistence, recency, sacrifice)

        - persistence: action_count / total — how consistently Akua acts on this
        - recency: exponential decay from last evidence
        - sacrifice: if Akua sacrifices other things for this, it matters more
        """
        total = action_count + skip_count + defer_count
        if total == 0:
            return stated  # no data yet, trust stated

        # Persistence weighting (how consistently she acts on this)
        persistence = action_count / total

        # Recency decay
        recency = 1.0
        if last_evidence_at:
            days_since = max(0, (datetime.utcnow() - last_evidence_at).total_seconds() / 86400)
            if decay_half_life > 0:
                recency = math.pow(0.5, days_since / decay_half_life)

        # Confidence blend: more data → trust revealed more
        confidence = min(1.0, total / 30)

        # Base: weighted blend of stated and revealed
        base = (stated * (1 - confidence)) + (revealed * confidence)

        # Apply persistence and recency
        effective = base * (0.6 + 0.4 * persistence) * (0.5 + 0.5 * recency)

        return max(0.0, min(1.0, effective))

    # ── Contradiction scoring ──────────────────────────────────────────
    def _compute_contradiction(self, stated: float, revealed: float, is_core: bool) -> float:
        """
        Contradiction = gap between stated and revealed.
        Amplified for core goals (stated >= 0.8).

        If you say weight loss is 0.4 and skip training → low contradiction.
        If you say income replacement is 1.0 and avoid sales → HIGH contradiction.
        """
        raw_gap = abs(stated - revealed)

        # Amplify for core goals
        if is_core and raw_gap > 0.3:
            return min(1.0, raw_gap * 1.5)

        return raw_gap

    # ── Get contradictions ─────────────────────────────────────────────
    def get_contradictions(self, min_confidence: float = 0.1) -> List[Dict]:
        """Get goals with significant contradictions, sorted by severity."""
        goals = self.get_goals()
        contradictions = []
        for g in goals:
            score = g.get("contradiction_score", 0)
            conf = g.get("confidence", 0)
            if score > 0.2 and conf >= min_confidence:
                stated = g.get("stated_weight", 0.5)
                revealed = g.get("revealed_weight", 0.0)
                severity = "critical" if score > 0.6 else "warning" if score > 0.4 else "info"
                contradictions.append({
                    "goal_id": g["goal_id"],
                    "label": g["label"],
                    "stated_weight": stated,
                    "revealed_weight": revealed,
                    "contradiction_score": score,
                    "severity": severity,
                    "confidence": conf,
                    "action_count": g.get("action_count", 0),
                    "skip_count": g.get("skip_count", 0),
                })
        contradictions.sort(key=lambda c: c["contradiction_score"], reverse=True)
        return contradictions

    # ── Run full weight update (nightly) ───────────────────────────────
    def run_nightly_update(self) -> Dict:
        """
        Nightly reconciliation:
        - Recompute all effective weights with fresh decay
        - Update contradiction scores
        - Return summary of changes
        """
        db = get_db()
        if not db:
            return {"error": "no db"}
        goals = self.get_goals()
        changes = []
        for g in goals:
            old_effective = g.get("effective_weight", 0)
            new_effective = self._compute_effective(
                stated=g.get("stated_weight", 0.5),
                revealed=g.get("revealed_weight", 0.0),
                action_count=g.get("action_count", 0),
                skip_count=g.get("skip_count", 0),
                defer_count=g.get("defer_count", 0),
                last_evidence_at=datetime.fromisoformat(g["last_evidence_at"]) if g.get("last_evidence_at") else None,
                decay_half_life=g.get("decay_half_life_days", 30),
            )
            new_contradiction = self._compute_contradiction(
                stated=g.get("stated_weight", 0.5),
                revealed=g.get("revealed_weight", 0.0),
                is_core=(g.get("stated_weight", 0) >= 0.8),
            )
            delta = abs(new_effective - old_effective)
            if delta > 0.001:
                try:
                    db.table(GOALS_TABLE).update({
                        "effective_weight": round(new_effective, 4),
                        "contradiction_score": round(new_contradiction, 4),
                        "updated_at": datetime.utcnow().isoformat(),
                    }).eq("goal_id", g["goal_id"]).execute()
                    changes.append({
                        "goal_id": g["goal_id"],
                        "label": g["label"],
                        "old_effective": round(old_effective, 4),
                        "new_effective": round(new_effective, 4),
                        "delta": round(delta, 4),
                    })
                except Exception as exc:
                    LOGGER.error("[Weighting] nightly update error for %s: %s", g["goal_id"], exc)

        LOGGER.info("[Weighting] Nightly update: %d goals changed", len(changes))
        return {"goals_updated": len(changes), "changes": changes}

    # ── Retirement countdown ───────────────────────────────────────────
    def get_retirement_countdown(self) -> Dict:
        target = datetime(2026, 12, 31)
        days_left = max(0, (target - datetime.utcnow()).days)
        months_left = max(1, days_left / 30)
        return {
            "days_left": days_left,
            "months_left": round(months_left, 1),
            "target_annual": 1_000_000,
            "monthly_needed": round(1_000_000 / 12),
        }
