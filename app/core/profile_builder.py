"""
Profile Builder — JJ learns who AAA really is from her own words.

Architecture based on Personal Construct Theory (George Kelly):
People understand their world through personal constructs — bipolar dimensions
of meaning built from experience. JJ builds AAA's construct map from direct
testimony, not inference or assumption.

Three layers:
1. Direct Testimony    — answers to questions → high confidence facts
2. Behavioral Evidence — what JJ observes vs what AAA said → patterns
3. Synthesis           — periodic inference run → updates mimograph with confidence scores

Question bank covers 8 life domains:
Identity, Work, Health, Finance, Relationships, Fear/Blocks, Values, Energy/Time

Rules:
- Never assume. Only assert what AAA has confirmed.
- Resurface questions after 90 days to check for drift.
- Flag contradictions only when behavioral evidence is strong (3+ data points).
- Confidence score drops if contradicted by behavior.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.db import get_db

LOGGER = logging.getLogger(__name__)

# ── Question Bank ──────────────────────────────────────────────────────────────
# Each question has: id, domain, text, follow_up (optional), resurfacing_days
QUESTION_BANK: List[Dict] = [
    # IDENTITY
    {"id": "id_001", "domain": "identity",
     "text": "In your own words, what are you building — and why does it matter to you personally?",
     "resurfacing_days": 90},
    {"id": "id_002", "domain": "identity",
     "text": "How do you want to be remembered by the people who know you best?",
     "resurfacing_days": 180},
    {"id": "id_003", "domain": "identity",
     "text": "What does a genuinely good day look like for you — not productive, just good?",
     "resurfacing_days": 60},
    {"id": "id_004", "domain": "identity",
     "text": "Which of your roles feels most like the real you right now — doctor, builder, mother, entrepreneur?",
     "resurfacing_days": 90},

    # WORK & BUSINESS
    {"id": "wk_001", "domain": "work",
     "text": "Of your 34 businesses, which one excites you most right now and why?",
     "resurfacing_days": 30},
    {"id": "wk_002", "domain": "work",
     "text": "Which business would you shut down today if you were honest with yourself?",
     "resurfacing_days": 60},
    {"id": "wk_003", "domain": "work",
     "text": "What kind of work puts you in a flow state — where time disappears?",
     "resurfacing_days": 90},
    {"id": "wk_004", "domain": "work",
     "text": "What does your ideal working week look like once medicine is behind you?",
     "resurfacing_days": 90},
    {"id": "wk_005", "domain": "work",
     "text": "What's the one thing about building businesses that you find genuinely hard?",
     "resurfacing_days": 60},

    # HEALTH
    {"id": "hl_001", "domain": "health",
     "text": "What does feeling physically strong and well mean for you day-to-day?",
     "resurfacing_days": 60},
    {"id": "hl_002", "domain": "health",
     "text": "What form of exercise do you genuinely enjoy — not feel you should do, actually enjoy?",
     "resurfacing_days": 90},
    {"id": "hl_003", "domain": "health",
     "text": "What's your honest relationship with food right now — fuel, pleasure, stress, habit?",
     "resurfacing_days": 60},
    {"id": "hl_004", "domain": "health",
     "text": "When you're under serious stress, what does your body tell you first?",
     "resurfacing_days": 90},
    {"id": "hl_005", "domain": "health",
     "text": "What's one health habit you've kept consistently that you're proud of?",
     "resurfacing_days": 90},

    # FINANCE
    {"id": "fn_001", "domain": "finance",
     "text": "What would having $85K this year actually change for you — specifically?",
     "resurfacing_days": 30},
    {"id": "fn_002", "domain": "finance",
     "text": "What's your honest relationship with money — does it feel scarce, abundant, complicated?",
     "resurfacing_days": 90},
    {"id": "fn_003", "domain": "finance",
     "text": "What's the one financial decision you keep deferring that you know needs to be made?",
     "resurfacing_days": 45},
    {"id": "fn_004", "domain": "finance",
     "text": "What would financial security actually look like to you — a number, a feeling, a situation?",
     "resurfacing_days": 90},

    # RELATIONSHIPS & PEOPLE
    {"id": "rl_001", "domain": "relationships",
     "text": "Who are the most important people in your life right now and what do you want for them?",
     "resurfacing_days": 90},
    {"id": "rl_002", "domain": "relationships",
     "text": "Who do you feel most yourself around?",
     "resurfacing_days": 90},
    {"id": "rl_003", "domain": "relationships",
     "text": "Is there a relationship in your life that's costing you more than it's giving right now?",
     "resurfacing_days": 60},

    # FEARS & BLOCKS
    {"id": "fb_001", "domain": "blocks",
     "text": "What's the thing you know you need to do but keep finding reasons not to?",
     "resurfacing_days": 30},
    {"id": "fb_002", "domain": "blocks",
     "text": "What would you attempt if you knew you couldn't fail?",
     "resurfacing_days": 90},
    {"id": "fb_003", "domain": "blocks",
     "text": "What fear shows up most often when you think about the next 12 months?",
     "resurfacing_days": 45},
    {"id": "fb_004", "domain": "blocks",
     "text": "What does asking for help feel like for you — easy, hard, specific to certain people?",
     "resurfacing_days": 90},

    # VALUES
    {"id": "vl_001", "domain": "values",
     "text": "What would you never compromise on, no matter what?",
     "resurfacing_days": 180},
    {"id": "vl_002", "domain": "values",
     "text": "When have you felt most proud of a decision you made?",
     "resurfacing_days": 120},
    {"id": "vl_003", "domain": "values",
     "text": "What does freedom mean to you specifically?",
     "resurfacing_days": 90},

    # ENERGY & TIME
    {"id": "en_001", "domain": "energy",
     "text": "When during the day do you do your clearest thinking?",
     "resurfacing_days": 90},
    {"id": "en_002", "domain": "energy",
     "text": "What drains you fastest — people, tasks, environments, decisions?",
     "resurfacing_days": 60},
    {"id": "en_003", "domain": "energy",
     "text": "What does rest look like for you — sleep, solitude, movement, something else?",
     "resurfacing_days": 60},
    {"id": "en_004", "domain": "energy",
     "text": "How do you feel about your current schedule — does it reflect what matters to you?",
     "resurfacing_days": 30},

    # FUTURE & ASPIRATIONS
    {"id": "ft_001", "domain": "future",
     "text": "What do you want your life to look like on January 1st, 2027?",
     "resurfacing_days": 60},
    {"id": "ft_002", "domain": "future",
     "text": "What's the one thing you'd regret not doing in the next 12 months?",
     "resurfacing_days": 45},
    {"id": "ft_003", "domain": "future",
     "text": "Who do you want to become — not what you want to do, who you want to BE?",
     "resurfacing_days": 90},
    {"id": "ft_004", "domain": "future",
     "text": "What would you do with your days if the $85K was already secured?",
     "resurfacing_days": 60},
]


class ProfileBuilder:
    """
    Builds AAA's psychological and behavioral profile from direct testimony.

    Stores answers in Supabase (jeeves_profile_answers table).
    Synthesizes into mimograph-compatible constructs periodically.
    """

    def __init__(self):
        self.db = get_db()
        self._ensure_tables()

    def _ensure_tables(self):
        """Create profile tables if they don't exist yet."""
        if not self.db:
            return
        try:
            self.db.rpc("query", {"query": "SELECT 1 FROM jeeves_profile_answers LIMIT 1"})
        except Exception:
            # Tables don't exist — will be created via migration
            LOGGER.info("[Profile] Profile tables not yet created — run migration.")

    # ── Question Selection ─────────────────────────────────────────────

    def get_next_question(self) -> Optional[Dict]:
        """
        Select the best question to ask today.

        Priority:
        1. Never-asked questions (highest priority — fill gaps first)
        2. Questions due for resurfacing (answer is stale)
        3. Domains with fewest answers (balance coverage)
        """
        asked = self._get_asked_questions()
        asked_ids = {r["question_id"] for r in asked}
        asked_map = {r["question_id"]: r for r in asked}

        today = datetime.now(tz=timezone.utc)

        # Score each question
        candidates = []
        for q in QUESTION_BANK:
            qid = q["id"]
            if qid not in asked_ids:
                # Never asked — highest priority
                candidates.append((q, 100.0))
            else:
                # Check if due for resurfacing
                last_asked = asked_map[qid]
                last_dt_str = last_asked.get("answered_at") or last_asked.get("asked_at", "")
                if last_dt_str:
                    try:
                        last_dt = datetime.fromisoformat(last_dt_str.replace("Z", "+00:00"))
                        days_since = (today - last_dt).days
                        if days_since >= q["resurfacing_days"]:
                            score = 50.0 + (days_since - q["resurfacing_days"]) * 0.5
                            candidates.append((q, score))
                    except ValueError:
                        pass

        if not candidates:
            return None

        # Sort by score descending, pick top
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Balance domains — prefer domain with fewest answers
        domain_counts: Dict[str, int] = {}
        for r in asked:
            q_data = next((q for q in QUESTION_BANK if q["id"] == r["question_id"]), None)
            if q_data:
                domain = q_data["domain"]
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Among top 5 candidates, pick one from least-covered domain
        top_candidates = candidates[:5]
        top_candidates.sort(
            key=lambda x: domain_counts.get(x[0]["domain"], 0)
        )

        return top_candidates[0][0]

    def get_check_in_questions(self, count: int = 2) -> List[Dict]:
        """
        Get 2-3 questions for the evening check-in.
        Mixes: one identity/values question + one practical question.
        """
        all_candidates = []

        # Get one deep question (identity, values, future, blocks)
        deep_domains = {"identity", "values", "future", "blocks"}
        # Get one practical question (work, health, finance, energy)
        practical_domains = {"work", "health", "finance", "energy", "relationships"}

        asked = self._get_asked_questions()
        asked_ids = {r["question_id"] for r in asked}

        deep_unanswered = [q for q in QUESTION_BANK
                           if q["domain"] in deep_domains and q["id"] not in asked_ids]
        practical_unanswered = [q for q in QUESTION_BANK
                                 if q["domain"] in practical_domains and q["id"] not in asked_ids]

        result = []
        if deep_unanswered:
            result.append(deep_unanswered[0])
        if practical_unanswered:
            result.append(practical_unanswered[0])

        return result[:count]

    # ── Answer Storage ─────────────────────────────────────────────────

    def record_answer(self, question_id: str, answer: str) -> bool:
        """
        Store AAA's answer to a question.
        Updates the profile and triggers a confidence recalculation.
        """
        if not self.db:
            LOGGER.warning("[Profile] No DB — answer not stored.")
            return False

        try:
            question = next((q for q in QUESTION_BANK if q["id"] == question_id), None)
            if not question:
                LOGGER.warning("[Profile] Unknown question_id: %s", question_id)
                return False

            now = datetime.now(tz=timezone.utc).isoformat()
            self.db.table("jeeves_profile_answers").upsert({
                "question_id": question_id,
                "domain": question["domain"],
                "question_text": question["text"],
                "answer": answer,
                "answered_at": now,
                "confidence": 1.0,  # Direct testimony = full confidence
            }).execute()

            LOGGER.info("[Profile] Answer recorded: %s (domain=%s)", question_id, question["domain"])
            return True

        except Exception as exc:
            LOGGER.error("[Profile] Failed to store answer: %s", exc)
            return False

    def record_behavioral_evidence(
        self,
        domain: str,
        observation: str,
        supports_claim: Optional[str] = None,
        contradicts_claim: Optional[str] = None,
        strength: float = 0.3,
    ) -> None:
        """
        Record what JJ observed about AAA's behavior.
        Used to calibrate confidence in profile claims over time.

        strength: 0.0–1.0 (single observation = 0.3, strong pattern = 0.7+)
        """
        if not self.db:
            return

        try:
            self.db.table("jeeves_behavioral_evidence").insert({
                "domain": domain,
                "observation": observation[:500],
                "supports_claim": supports_claim,
                "contradicts_claim": contradicts_claim,
                "strength": strength,
                "observed_at": datetime.now(tz=timezone.utc).isoformat(),
            }).execute()
        except Exception as exc:
            LOGGER.warning("[Profile] Behavioral evidence not stored: %s", exc)

    # ── Profile Synthesis ──────────────────────────────────────────────

    def synthesize_profile(self) -> Dict:
        """
        Build a structured profile from all answers + behavioral evidence.

        Returns a dict organized by domain with:
        - confirmed facts (from answers)
        - behavioral patterns (from evidence)
        - confidence scores
        - genuine contradictions (behavior vs stated, 3+ evidence points)
        """
        if not self.db:
            return {}

        try:
            answers_resp = self.db.table("jeeves_profile_answers").select("*").execute()
            answers = answers_resp.data or []

            evidence_resp = self.db.table("jeeves_behavioral_evidence").select("*").execute()
            evidence = evidence_resp.data or []

        except Exception as exc:
            LOGGER.error("[Profile] Synthesis failed: %s", exc)
            return {}

        profile: Dict = {}

        # Group answers by domain
        for answer in answers:
            domain = answer.get("domain", "general")
            if domain not in profile:
                profile[domain] = {"facts": [], "patterns": [], "contradictions": []}
            profile[domain]["facts"].append({
                "question": answer.get("question_text", ""),
                "answer": answer.get("answer", ""),
                "answered_at": answer.get("answered_at", ""),
                "confidence": answer.get("confidence", 1.0),
            })

        # Add behavioral evidence
        for ev in evidence:
            domain = ev.get("domain", "general")
            if domain not in profile:
                profile[domain] = {"facts": [], "patterns": [], "contradictions": []}

            contradicts = ev.get("contradicts_claim")
            if contradicts:
                profile[domain]["contradictions"].append({
                    "claim": contradicts,
                    "observation": ev.get("observation", ""),
                    "strength": ev.get("strength", 0.3),
                })
            else:
                profile[domain]["patterns"].append({
                    "observation": ev.get("observation", ""),
                    "strength": ev.get("strength", 0.3),
                })

        # Only surface contradictions with 3+ evidence points
        for domain_data in profile.values():
            raw_contradictions = domain_data.get("contradictions", [])
            # Group by claim
            claim_groups: Dict[str, List] = {}
            for c in raw_contradictions:
                claim = c.get("claim", "")
                claim_groups.setdefault(claim, []).append(c)
            # Keep only well-evidenced contradictions
            domain_data["contradictions"] = [
                {
                    "claim": claim,
                    "evidence_count": len(items),
                    "avg_strength": sum(i["strength"] for i in items) / len(items),
                    "observations": [i["observation"] for i in items[:3]],
                }
                for claim, items in claim_groups.items()
                if len(items) >= 3
            ]

        return profile

    def get_profile_summary(self) -> str:
        """
        Return a concise profile summary for injection into LLM context.
        Only high-confidence facts — no assumptions, no speculation.
        """
        profile = self.synthesize_profile()
        if not profile:
            return "Profile: Still being built from check-in answers."

        lines = ["AAA PROFILE (from her own words — high confidence only):"]
        for domain, data in profile.items():
            facts = data.get("facts", [])
            if facts:
                lines.append(f"\n[{domain.upper()}]")
                for f in facts[-3:]:  # Most recent 3 per domain
                    lines.append(f"  • {f['answer'][:120]}")

        return "\n".join(lines)

    # ── Data Retrieval ─────────────────────────────────────────────────

    def _get_asked_questions(self) -> List[Dict]:
        """Return all questions that have been asked (answered or not)."""
        if not self.db:
            return []
        try:
            resp = self.db.table("jeeves_profile_answers").select(
                "question_id, answered_at"
            ).execute()
            return resp.data or []
        except Exception:
            return []

    def get_answer_count(self) -> int:
        """How many questions have been answered so far."""
        return len(self._get_asked_questions())

    def get_domain_coverage(self) -> Dict[str, int]:
        """How many answers exist per domain."""
        asked = self._get_asked_questions()
        asked_ids = {r["question_id"] for r in asked}
        coverage: Dict[str, int] = {}
        for q in QUESTION_BANK:
            if q["id"] in asked_ids:
                domain = q["domain"]
                coverage[domain] = coverage.get(domain, 0) + 1
        return coverage
