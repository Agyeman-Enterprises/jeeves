"""
JJ Brain — User Model
Living profile of Akua: goals, belief nodes, events, and computed intelligence.
Persistence: JJ Supabase (tzjygaxpzrtevlnganjs) — jeeves_* tables.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.db import get_db

LOGGER = logging.getLogger(__name__)

# ── Table constants ────────────────────────────────────────────────────
T_GOALS = "jeeves_goals"
T_NODES = "jeeves_belief_nodes"
T_EVENTS = "jeeves_events"
T_STATE = "jeeves_state"
T_PROFILE = "jeeves_profile_answers"


class UserModel:
    """
    Living model of Akua — goals, traits, events, and computed intelligence.
    All data lives in JJ Supabase. No seeding — data already exists.
    """

    # ── Goal operations ────────────────────────────────────────────────

    def get_goals(self) -> List[Dict]:
        """All goals sorted by effective_weight descending."""
        db = get_db()
        if not db:
            return []
        try:
            res = db.table(T_GOALS).select("*").order("effective_weight", desc=True).execute()
            return res.data or []
        except Exception as exc:
            LOGGER.error("[Brain] get_goals: %s", exc)
            return []

    def get_goal(self, goal_id: str) -> Optional[Dict]:
        db = get_db()
        if not db:
            return None
        try:
            res = db.table(T_GOALS).select("*").eq("goal_id", goal_id).single().execute()
            return res.data
        except Exception as exc:
            LOGGER.error("[Brain] get_goal(%s): %s", goal_id, exc)
            return None

    def record_action_for_goal(self, goal_id: str, action_score: float, description: str = ""):
        """
        Update goal weights from a behavioral observation.
        action_score: 1.0=strongly supports, -1.0=strongly contradicts.
        """
        db = get_db()
        if not db:
            return
        goal = self.get_goal(goal_id)
        if not goal:
            LOGGER.warning("[Brain] Unknown goal_id: %s", goal_id)
            return
        try:
            alpha = 0.1
            old_revealed = goal.get("revealed_weight", 0.0)
            new_revealed = max(0.0, min(1.0, (alpha * max(0.0, action_score)) + ((1 - alpha) * old_revealed)))

            action_count = goal.get("action_count", 0)
            skip_count = goal.get("skip_count", 0)
            defer_count = goal.get("defer_count", 0)
            if action_score > 0.3:
                action_count += 1
            elif action_score < -0.3:
                skip_count += 1
            else:
                defer_count += 1

            stated = goal.get("stated_weight", 0.5)
            total_obs = action_count + skip_count + defer_count
            confidence = min(1.0, total_obs / 30)
            consistency = max(0.0, 1.0 - abs(stated - new_revealed))
            effective = max(0.0, min(1.0, ((stated * (1 - confidence)) + (new_revealed * confidence)) * consistency))

            contradiction_score = max(0.0, abs(stated - new_revealed) - 0.2) if total_obs >= 3 else 0.0

            db.table(T_GOALS).update({
                "revealed_weight": round(new_revealed, 4),
                "effective_weight": round(effective, 4),
                "confidence": round(confidence, 4),
                "contradiction_score": round(contradiction_score, 4),
                "action_count": action_count,
                "skip_count": skip_count,
                "defer_count": defer_count,
                "last_evidence_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("goal_id", goal_id).execute()

            LOGGER.info("[Brain] goal=%s revealed=%.2f effective=%.2f", goal_id, new_revealed, effective)
        except Exception as exc:
            LOGGER.error("[Brain] record_action_for_goal: %s", exc)

    def get_contradictions(self) -> List[Dict]:
        """Goals where stated importance diverges significantly from revealed behavior."""
        goals = self.get_goals()
        contradictions = []
        for g in goals:
            stated = g.get("stated_weight", 0.5)
            revealed = g.get("revealed_weight", 0.0)
            gap = abs(stated - revealed)
            total_obs = g.get("action_count", 0) + g.get("skip_count", 0) + g.get("defer_count", 0)
            if gap > 0.3 and total_obs >= 3:
                severity = "critical" if gap > 0.6 else "warning" if gap > 0.4 else "info"
                contradictions.append({
                    "goal_id": g["goal_id"],
                    "goal_name": g["label"],
                    "stated_weight": stated,
                    "revealed_weight": revealed,
                    "gap": gap,
                    "severity": severity,
                    "action_count": g.get("action_count", 0),
                    "skip_count": g.get("skip_count", 0),
                    "description": f"Says {stated:.0%} important, behavior shows {revealed:.0%}",
                })
        contradictions.sort(key=lambda x: x["gap"], reverse=True)
        return contradictions

    def run_nightly_decay(self):
        """Apply decay to all goal weights based on inactivity."""
        goals = self.get_goals()
        db = get_db()
        if not db:
            return
        now = datetime.utcnow()
        for g in goals:
            last_evidence = g.get("last_evidence_at")
            if not last_evidence:
                continue
            try:
                last_dt = datetime.fromisoformat(last_evidence.replace("Z", "+00:00")).replace(tzinfo=None)
                days_inactive = (now - last_dt).days
                half_life = g.get("decay_half_life_days", 30.0)
                if days_inactive > 0:
                    decay = 0.5 ** (days_inactive / half_life)
                    new_revealed = round(g.get("revealed_weight", 0.0) * decay, 4)
                    new_effective = round(
                        (g["stated_weight"] * (1 - g.get("confidence", 0.1))) +
                        (new_revealed * g.get("confidence", 0.1)), 4
                    )
                    db.table(T_GOALS).update({
                        "revealed_weight": new_revealed,
                        "effective_weight": max(new_effective, g["stated_weight"] * 0.1),
                        "updated_at": now.isoformat(),
                    }).eq("goal_id", g["goal_id"]).execute()
            except Exception as exc:
                LOGGER.warning("[Brain] decay goal=%s: %s", g.get("goal_id"), exc)

    # ── Belief node (trait) operations ─────────────────────────────────

    def get_nodes(self, node_type: str = None) -> List[Dict]:
        """Get belief nodes, optionally filtered by type."""
        db = get_db()
        if not db:
            return []
        try:
            q = db.table(T_NODES).select("*").order("strength", desc=True)
            if node_type:
                q = q.eq("node_type", node_type)
            return (q.execute().data or [])
        except Exception as exc:
            LOGGER.error("[Brain] get_nodes: %s", exc)
            return []

    def update_node(self, node_id: str, evidence: str, strength_delta: float = 0.05):
        """Update a belief node's strength from new evidence."""
        db = get_db()
        if not db:
            return
        try:
            res = db.table(T_NODES).select("*").eq("node_id", node_id).single().execute()
            if not res.data:
                LOGGER.warning("[Brain] Unknown node_id: %s", node_id)
                return
            node = res.data
            new_strength = max(0.0, min(1.0, node["strength"] + strength_delta))
            new_confidence = min(1.0, node.get("confidence", 0.1) + 0.05)
            db.table(T_NODES).update({
                "strength": round(new_strength, 4),
                "confidence": round(new_confidence, 4),
                "evidence_count": node.get("evidence_count", 0) + 1,
                "last_evidence": evidence,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("node_id", node_id).execute()
        except Exception as exc:
            LOGGER.error("[Brain] update_node(%s): %s", node_id, exc)

    # ── Event / observation recording ─────────────────────────────────

    def record_observation(self, observation_type: str, category: str,
                           description: str, value: float = 1.0,
                           related_goal: str = None, source: str = "manual",
                           context: Dict = None):
        """Record a behavior, action, statement, or emotion as a jeeves_event."""
        db = get_db()
        if not db:
            return
        try:
            payload = {"observation_type": observation_type}
            if context:
                payload.update(context)
            db.table(T_EVENTS).insert({
                "source": source,
                "modality": "text",
                "raw_text": description,
                "structured_payload": payload,
                "entities": [category],
                "linked_goals": [related_goal] if related_goal else [],
                "valence": max(-1.0, min(1.0, value)),
                "arousal": 0.5,
                "certainty": 0.6,
                "inferred_tags": [observation_type, category],
                "self_reported_intent": description[:200],
            }).execute()

            if related_goal:
                score = value if observation_type in ("action", "completion") else -abs(value)
                if observation_type in ("skip", "defer"):
                    score = -0.5
                self.record_action_for_goal(related_goal, score, description)

            LOGGER.info("[Brain] event: %s/%s — %s", observation_type, category, description[:60])
        except Exception as exc:
            LOGGER.error("[Brain] record_observation: %s", exc)

    def get_recent_observations(self, hours: int = 24, category: str = None) -> List[Dict]:
        """Recent events from the last N hours."""
        db = get_db()
        if not db:
            return []
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            q = db.table(T_EVENTS).select("*").gte("timestamp", since).order("timestamp", desc=True)
            if category:
                q = q.contains("entities", [category])
            return (q.limit(100).execute().data or [])
        except Exception as exc:
            LOGGER.error("[Brain] get_recent_observations: %s", exc)
            return []

    # ── Intelligence aggregation ───────────────────────────────────────

    def get_retirement_countdown(self) -> Dict:
        """Days until EOY 2026 and income gap."""
        target = datetime(2026, 12, 31)
        days_left = max(0, (target - datetime.utcnow()).days)
        return {
            "days_left": days_left,
            "months_left": round(max(1, days_left / 30), 1),
            "target_annual": 1_000_000,
            "monthly_needed": round(1_000_000 / 12),
            "weekly_needed": round(1_000_000 / 52),
        }

    def get_profile_summary(self) -> Dict:
        """Full profile for briefings and LLM context."""
        goals = self.get_goals()
        nodes = self.get_nodes()
        contradictions = self.get_contradictions()
        retirement = self.get_retirement_countdown()
        top_goals = goals[:5]
        traits = [n for n in nodes if n["node_type"] == "trait"]

        return {
            "retirement_countdown": retirement,
            "top_goals": [
                {
                    "goal_id": g["goal_id"],
                    "name": g["label"],
                    "effective_weight": g["effective_weight"],
                    "stated_weight": g["stated_weight"],
                    "contradiction_score": g.get("contradiction_score", 0.0),
                }
                for g in top_goals
            ],
            "contradictions": [c for c in contradictions if c["severity"] == "critical"][:3],
            "key_traits": [{"name": n["label"], "type": n["node_type"], "strength": n["strength"]}
                           for n in traits[:8]],
            "total_goals": len(goals),
            "total_events": sum(
                g.get("action_count", 0) + g.get("skip_count", 0) for g in goals
            ),
        }
