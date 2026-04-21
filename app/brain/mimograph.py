"""
JJ Brain — Mimograph
Generates morning briefings, daily questions, reflections, and insight reports
from the JJ brain data (goals, belief nodes, events).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.brain.user_model import UserModel
from app.db import get_db

LOGGER = logging.getLogger(__name__)

T_STATE = "jeeves_state"
T_PROFILE = "jeeves_profile_answers"


class Mimograph:
    """The living portrait of Akua — generates intelligence from behavioral data."""

    def __init__(self, user_model: UserModel = None):
        self.user_model = user_model or UserModel()

    # ── Morning Briefing ───────────────────────────────────────────────

    def generate_morning_briefing(self) -> Dict:
        """
        Morning intelligence report:
        retirement countdown + behavior-weighted priorities + contradictions + questions.
        """
        profile = self.user_model.get_profile_summary()
        recent_obs = self.user_model.get_recent_observations(hours=24)
        questions = self.generate_daily_questions()
        recent_reflections = self._get_recent_reflections(hours=24)
        retirement = profile["retirement_countdown"]

        lines = []
        lines.append(f"☀️ JJ MORNING BRIEF — {datetime.utcnow().strftime('%A %B %d, %Y')}")
        lines.append(f"Retirement countdown: {retirement['days_left']} days | Need: ${retirement['monthly_needed']:,}/month")
        lines.append("")

        lines.append("📊 YOUR TRUE PRIORITIES (behavior-weighted):")
        for i, g in enumerate(profile["top_goals"][:5], 1):
            score = g["contradiction_score"]
            marker = "✅" if score < 0.2 else "⚠️" if score < 0.5 else "🔴"
            lines.append(f"  {i}. {g['name']}: {g['effective_weight']:.0%} {marker}")
        lines.append("")

        if profile["contradictions"]:
            lines.append("🔴 CONTRADICTIONS DETECTED:")
            for c in profile["contradictions"][:3]:
                lines.append(f"  • {c['goal_name']}: says {c['stated_weight']:.0%}, does {c['revealed_weight']:.0%}")
            lines.append("")

        if recent_reflections:
            lines.append("💡 INSIGHTS:")
            for r in recent_reflections[:2]:
                content = r.get("value", {}).get("content", "") if isinstance(r.get("value"), dict) else ""
                if content:
                    lines.append(f"  • {content[:120]}")
            lines.append("")

        if recent_obs:
            actions = [o for o in recent_obs if o.get("structured_payload", {}).get("observation_type") in ("action", "completion")]
            skips = [o for o in recent_obs if o.get("structured_payload", {}).get("observation_type") in ("skip", "defer")]
            if actions:
                lines.append(f"✅ Yesterday: {len(actions)} actions taken")
            if skips:
                lines.append(f"⏸️ Yesterday: {len(skips)} items skipped/deferred")
            lines.append("")

        if questions:
            lines.append("❓ CHECK-IN QUESTIONS:")
            for q in questions[:3]:
                lines.append(f"  • {q['question']}")
            lines.append("")

        return {
            "text": "\n".join(lines),
            "retirement_countdown": retirement,
            "top_goals": profile["top_goals"],
            "contradictions": profile["contradictions"],
            "questions": questions,
            "recent_observations_count": len(recent_obs),
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ── Daily Questions ────────────────────────────────────────────────

    def generate_daily_questions(self, max_questions: int = 3) -> List[Dict]:
        """
        Targeted questions to reduce uncertainty.
        Priority: contradictions > deferred items > goal gaps > health patterns.
        """
        questions = []

        contradictions = self.user_model.get_contradictions()
        for c in contradictions[:1]:
            if c["severity"] == "critical":
                questions.append({
                    "question": (
                        f"You say '{c['goal_name']}' is {c['stated_weight']:.0%} important, "
                        f"but your actions show {c['revealed_weight']:.0%}. "
                        "Is the goal wrong, or is something blocking you?"
                    ),
                    "question_type": "contradiction",
                    "related_goal": c["goal_id"],
                    "priority": 10,
                })

        goals = self.user_model.get_goals()
        deferred = sorted(
            [g for g in goals if g.get("defer_count", 0) >= 3],
            key=lambda g: g.get("defer_count", 0), reverse=True
        )
        for g in deferred[:1]:
            if len(questions) >= max_questions:
                break
            questions.append({
                "question": (
                    f"'{g['label']}' has been deferred {g['defer_count']} times. "
                    "Should I deprioritize it, find a better time, or is there a blocker?"
                ),
                "question_type": "deferred",
                "related_goal": g["goal_id"],
                "priority": 8,
            })

        top = [g for g in goals if g.get("effective_weight", 0) > 0.7]
        for g in top[:1]:
            if len(questions) >= max_questions:
                break
            last_evidence = g.get("last_evidence_at")
            if last_evidence:
                try:
                    last_dt = datetime.fromisoformat(last_evidence.replace("Z", "+00:00")).replace(tzinfo=None)
                    days_since = (datetime.utcnow() - last_dt).days
                    if days_since > 3:
                        questions.append({
                            "question": f"It's been {days_since} days since you worked on '{g['label']}'. What's happening?",
                            "question_type": "goal_check",
                            "related_goal": g["goal_id"],
                            "priority": 6,
                        })
                except (ValueError, TypeError):
                    pass

        recent = self.user_model.get_recent_observations(hours=72)
        health_obs = [o for o in recent if "health" in o.get("entities", [])]
        if not health_obs and len(questions) < max_questions:
            questions.append({
                "question": "No health activity logged in 3 days. How are you eating and moving?",
                "question_type": "pattern",
                "related_goal": "health_maintenance",
                "priority": 5,
            })

        self._store_questions(questions[:max_questions])
        return questions[:max_questions]

    def answer_question(self, question_text: str, answer: str, related_goal: str = None) -> Dict:
        """Record an answer to a check-in question."""
        self.user_model.record_observation(
            observation_type="statement",
            category="checkin",
            description=f"Q: {question_text[:80]} A: {answer[:200]}",
            source="checkin",
            related_goal=related_goal,
        )
        insight = f"Akua answered: {question_text[:50]}... → {answer[:100]}"
        return {"status": "recorded", "insight": insight}

    # ── Reflection Cycle ───────────────────────────────────────────────

    def run_reflection_cycle(self) -> List[Dict]:
        """
        Nightly: synthesize recent events into higher-order insights.
        Stored in jeeves_state with key = reflection_{timestamp}.
        """
        recent_obs = self.user_model.get_recent_observations(hours=24)
        goals = self.user_model.get_goals()
        contradictions = self.user_model.get_contradictions()
        reflections = []

        if recent_obs:
            actions = [o for o in recent_obs if o.get("structured_payload", {}).get("observation_type") in ("action", "completion")]
            skips = [o for o in recent_obs if o.get("structured_payload", {}).get("observation_type") in ("skip", "defer")]
            active_cats = set(e for o in actions for e in o.get("entities", []))
            avoided_goals = set(g for o in skips for g in o.get("linked_goals", []))
            summary = f"Today: {len(actions)} actions, {len(skips)} skips."
            if active_cats:
                summary += f" Active in: {', '.join(active_cats)}."
            if avoided_goals:
                summary += f" Avoided: {', '.join(avoided_goals)}."
            reflections.append({
                "reflection_type": "daily",
                "content": summary,
                "related_goals": list(set(g for o in recent_obs for g in o.get("linked_goals", []))),
                "confidence": 0.7,
            })

        for c in contradictions[:2]:
            direction = "fear/avoidance" if c["skip_count"] > c["action_count"] else "recent improvement"
            reflections.append({
                "reflection_type": "contradiction",
                "content": (
                    f"'{c['goal_name']}': stated {c['stated_weight']:.0%}, revealed {c['revealed_weight']:.0%}. "
                    f"Pattern suggests {direction}."
                ),
                "related_goals": [c["goal_id"]],
                "confidence": 0.6,
            })

        for g in goals[:3]:
            total = g.get("action_count", 0) + g.get("skip_count", 0) + g.get("defer_count", 0)
            if total > 0:
                rate = g.get("action_count", 0) / total
                direction = "accelerating" if rate > 0.7 else "stalling" if rate < 0.3 else "steady"
                reflections.append({
                    "reflection_type": "pattern",
                    "content": f"'{g['label']}' trajectory: {direction} ({rate:.0%} action rate, {total} obs)",
                    "related_goals": [g["goal_id"]],
                    "confidence": min(0.9, total / 20),
                })

        self._store_reflections(reflections)
        LOGGER.info("[Brain] Reflection cycle: %d reflections", len(reflections))
        return reflections

    # ── Proxy methods (used by compat router + external callers) ──────

    def get_nodes(self, node_type: str = None) -> List[Dict]:
        """Proxy to user_model.get_nodes() — returns belief nodes."""
        return self.user_model.get_nodes(node_type=node_type)

    def get_goals(self, limit: int = None) -> List[Dict]:
        """Proxy to user_model.get_goals() with optional limit."""
        goals = self.user_model.get_goals()
        return goals[:limit] if limit is not None else goals

    def get_profile_summary(self) -> Dict:
        """Proxy to user_model.get_profile_summary()."""
        return self.user_model.get_profile_summary()

    # ── Insight Report ─────────────────────────────────────────────────

    def get_insight_report(self) -> Dict:
        """Full intelligence report for briefings and agent context."""
        profile = self.user_model.get_profile_summary()
        contradictions = self.user_model.get_contradictions()
        traits = self.user_model.get_nodes(node_type="trait")
        blockers = self.user_model.get_nodes(node_type="blocker")
        recent_reflections = self._get_recent_reflections(hours=168)

        return {
            "profile": profile,
            "contradictions": contradictions,
            "traits": [{"name": n["label"], "type": n["node_type"],
                        "strength": n["strength"], "confidence": n.get("confidence", 0)}
                       for n in traits],
            "blockers": [{"name": n["label"], "strength": n["strength"]} for n in blockers],
            "recent_reflections": recent_reflections[:10],
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ── Private helpers ────────────────────────────────────────────────

    def _store_questions(self, questions: List[Dict]):
        db = get_db()
        if not db:
            return
        try:
            for q in questions:
                db.table(T_PROFILE).upsert({
                    "question_id": f"checkin_{datetime.utcnow().strftime('%Y%m%d')}_{q.get('related_goal', 'general')}",
                    "domain": q.get("question_type", "general"),
                    "question_text": q["question"],
                    "answer": "",
                    "confidence": q.get("priority", 5) / 10.0,
                }, on_conflict="question_id").execute()
        except Exception as exc:
            LOGGER.warning("[Brain] _store_questions: %s", exc)

    def _store_reflections(self, reflections: List[Dict]):
        db = get_db()
        if not db:
            return
        try:
            for r in reflections:
                key = f"reflection_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{r['reflection_type']}"
                db.table(T_STATE).upsert({
                    "key": key,
                    "value": {
                        "reflection_type": r["reflection_type"],
                        "content": r["content"],
                        "related_goals": r.get("related_goals", []),
                        "confidence": r.get("confidence", 0.5),
                    },
                }, on_conflict="key").execute()
        except Exception as exc:
            LOGGER.warning("[Brain] _store_reflections: %s", exc)

    def _get_recent_reflections(self, hours: int = 24) -> List[Dict]:
        db = get_db()
        if not db:
            return []
        try:
            since_prefix = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y%m%d")
            res = db.table(T_STATE).select("*").like("key", "reflection_%").order("key", desc=True).limit(20).execute()
            return [r for r in (res.data or []) if r["key"] > f"reflection_{since_prefix}"]
        except Exception as exc:
            LOGGER.warning("[Brain] _get_recent_reflections: %s", exc)
            return []


# ── Singleton ──────────────────────────────────────────────────────────
_instance: Optional[Mimograph] = None


def get_mimograph() -> Mimograph:
    global _instance
    if _instance is None:
        _instance = Mimograph()
    return _instance
