"""
Context Assembler — Before EVERY LLM call, assemble the full context.
Retrieves: goals, contradictions, recent events, schedule, Nexus alerts,
active open loops, preference directives.

This is what makes Jeeves's responses grounded in reality, not generic.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.memory.aqui_client import AquiClient
from app.memory.event_store import EventStore
from app.modeling.contradiction_engine import ContradictionEngine
from app.modeling.mimograph import Mimograph
from app.modeling.weighting_engine import WeightingEngine

LOGGER = logging.getLogger(__name__)


class ContextAssembler:
    """
    Builds the system prompt context block injected before every LLM call.
    Makes Jeeves aware of who Akua is, what she's doing, and what matters.
    """

    def __init__(
        self,
        weighting: WeightingEngine,
        mimograph: Mimograph,
        contradictions: ContradictionEngine,
        event_store: EventStore,
        aqui: AquiClient,
    ):
        self.weighting = weighting
        self.mimograph = mimograph
        self.contradictions = contradictions
        self.event_store = event_store
        self.aqui = aqui

    async def assemble(self, user_message: str = "") -> str:
        """
        Build the full context block for an LLM call.
        Returns a formatted string to inject as system context.
        """
        parts = []

        # ── Identity ──────────────────────────────────────────────
        parts.append(self._identity_block())

        # ── Top goals ─────────────────────────────────────────────
        goals = self.weighting.get_goals()
        parts.append(self._goals_block(goals[:7]))

        # ── Top contradictions ────────────────────────────────────
        contradiction_report = self.contradictions.get_full_contradiction_report()
        if contradiction_report:
            parts.append(self._contradictions_block(contradiction_report[:3]))

        # ── Recent events (last 24h) ─────────────────────────────
        recent = self.event_store.query(hours=24, limit=20)
        if recent:
            parts.append(self._events_block(recent))

        # ── Aqui memory context ───────────────────────────────────
        if user_message:
            try:
                aqui_results = await self.aqui.search(user_message, limit=5)
                if aqui_results:
                    parts.append(self._aqui_block(aqui_results))
            except Exception as exc:
                LOGGER.warning("Aqui search failed during context assembly: %s", exc)

        # ── Personality directives ────────────────────────────────
        parts.append(self._personality_block())

        # ── Retirement countdown ──────────────────────────────────
        countdown = self.weighting.get_retirement_countdown()
        parts.append(f"RETIREMENT COUNTDOWN: {countdown['days_left']} days. Need ${countdown['monthly_needed']:,}/month.")

        return "\n\n".join(parts)

    def _identity_block(self) -> str:
        return """YOU ARE JEEVES — Dr. Akua Agyeman's Chief of Staff.
You are a consummate professional who WORKS, not lectures. You are modeled after P.G. Wodehouse's
Jeeves: competent, discreet, proactive, and always two steps ahead.

YOUR JOB IS TO:
- Surface opportunities and actionable next steps (not opinions about her lifestyle)
- Direct agents to do work: "I've had Stratova draft posts. Approve?" not "You should market more"
- Report what you've DONE, what needs her decision, and what's coming next
- Schedule around her real constraints (hospital shifts, energy, time zones)
- Track her 40+ businesses and tell her which need attention and why

YOU DO NOT:
- Lecture about work-life balance, avoidance patterns, or lifestyle choices
- Say "you should" without having already started doing it
- Moralize about contradictions — just surface facts and ask what she wants
- Generate walls of text — be brief, specific, actionable
- Use ALL CAPS, bold warnings, or confrontational tone

TONE: Calm, competent, brief. Like a butler who has already handled 90% of it and just needs
a nod to handle the rest. Think: "The matter has been attended to, ma'am" not "YOU NEED TO ACT NOW."

She is a 60yo Med-Peds physician (Chief Hospitalist, Guam Memorial), building a business empire
to retire from medicine by EOY 2026. She has ~40 SaaS apps, 17 books, and a marketing engine.
Your job is to make things happen, not tell her what she already knows."""

    def _goals_block(self, goals: List[Dict]) -> str:
        lines = ["CURRENT GOALS (ranked by effective weight — what behavior shows, not just what she says):"]
        for i, g in enumerate(goals, 1):
            stated = g.get("stated_weight", 0)
            effective = g.get("effective_weight", 0)
            contradiction = g.get("contradiction_score", 0)
            marker = " ⚠️CONTRADICTION" if contradiction > 0.4 else ""
            lines.append(f"  {i}. {g['label']}: effective={effective:.0%} (stated={stated:.0%}){marker}")
        return "\n".join(lines)

    def _contradictions_block(self, contradictions: List[Dict]) -> str:
        lines = ["ACTIVE CONTRADICTIONS (address these when relevant):"]
        for c in contradictions:
            lines.append(f"  • [{c['severity'].upper()}] {c['explanation']}")
        return "\n".join(lines)

    def _events_block(self, events: List[Dict]) -> str:
        lines = ["RECENT ACTIVITY (last 24 hours):"]
        for e in events[:10]:
            ts = e.get("timestamp", "")[:16]
            text = e.get("raw_text", "")[:80]
            source = e.get("source", "?")
            lines.append(f"  [{ts}] ({source}) {text}")
        return "\n".join(lines)

    def _aqui_block(self, results: List[Dict]) -> str:
        lines = ["RELEVANT MEMORIES (from Aqui vault):"]
        for r in results[:5]:
            content = r.get("content", r.get("text", ""))[:120]
            lines.append(f"  • {content}")
        return "\n".join(lines)

    def _personality_block(self) -> str:
        return """RESPONSE FORMAT:
- Lead with what you've DONE or what's ready for her decision
- "I've done X. Need your approval for Y. Z is scheduled for tomorrow."
- Keep responses under 150 words unless she asks for detail
- Use bullet points, not paragraphs
- End with a clear ask or next action, not a lecture
- When contradictions exist, state the fact once. Don't repeat it.
  "Marketing deferred 8 times. Want me to assign it to Neuralia instead?"
  NOT "You keep avoiding marketing which is critical to your goals..."
- Every response should move something forward, not just observe."""
