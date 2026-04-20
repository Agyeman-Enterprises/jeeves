"""
Context Assembler - Builds system prompt for every LLM call.
No contradictions, no retirement pressure. Butler tone only.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional
from app.memory.aqui_client import AquiClient
from app.memory.event_store import EventStore
from app.modeling.mimograph import Mimograph
from app.modeling.weighting_engine import WeightingEngine

LOGGER = logging.getLogger(__name__)

class ContextAssembler:
    def __init__(self, weighting: WeightingEngine, mimograph: Mimograph,
                 event_store: EventStore, aqui: AquiClient):
        self.weighting = weighting
        self.mimograph = mimograph
        self.event_store = event_store
        self.aqui = aqui

    async def assemble(self, user_message: str = "") -> str:
        parts = []
        parts.append(self._identity_block())
        goals = self.weighting.get_goals()
        if goals:
            parts.append(self._goals_block(goals[:5]))
        recent = self.event_store.query(hours=24, limit=15)
        if recent:
            parts.append(self._events_block(recent))
        if user_message:
            try:
                # AquiClient.search already handles mem0 fallback internally
                mem_results = await self.aqui.search(user_message, limit=5)
                if mem_results:
                    parts.append(self._aqui_block(mem_results))
            except Exception as exc:
                LOGGER.warning("Memory search failed: %s", exc)
        parts.append(self._format_block())
        return "\n\n".join(parts)

    def _identity_block(self) -> str:
        return """YOU ARE JJ - Dr. Akua Agyeman's personal butler and chief of staff.

WHO AAA IS:
- 60-year-old Med-Peds physician, Chief Hospitalist at Guam Memorial Hospital
- Building a business empire to transition out of medicine
- 34+ businesses including SaaS apps, books, and a content/marketing engine
- Lives in Guam (ChST, UTC+10). Swims. Dislikes cooking. Workaholic.
- Revenue goal: $85K this year across the portfolio

YOUR JOB:
- Work first, report second. "I have had Stratova draft 3 posts. Approve?" not "You should market more."
- Surface opportunities: leads, content gaps, revenue moves, scheduling conflicts
- Protect her time and energy. She has hospital shifts - plan around them.
- Dispatch agents (Nexus, Neuralia, ContentForge, Stratova) and report what they did
- Learn her patterns. If she liked Marley Spoon meals, find equivalents.
- Track income, shifts, and TaxRx updates proactively

WHAT YOU NEVER DO:
- Lecture about work-life balance, avoidance, or lifestyle choices
- Surface the same concern more than once in 24 hours
- Use ALL CAPS, CRITICAL, HARD TRUTH, you need to, or countdown pressure
- Generate walls of text
- Ask her to do things you could do or dispatch an agent to do
- Moralise. Ever."""

    def _goals_block(self, goals: List[Dict]) -> str:
        lines = ["CURRENT PRIORITIES (by effective weight):"]
        for i, g in enumerate(goals, 1):
            weight = g.get("effective_weight", 0)
            lines.append(f"  {i}. {g.get('label', 'Unknown')} - {weight:.0%}")
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
        lines = ["RELEVANT MEMORIES (from Aqui):"]
        for r in results[:5]:
            content = r.get("content", r.get("text", ""))[:120]
            lines.append(f"  - {content}")
        return "\n".join(lines)

    def _format_block(self) -> str:
        return """RESPONSE FORMAT:
- Lead with what you have DONE or what needs a decision
- Under 150 words unless detail is requested
- End with one clear ask or next action
- Never repeat a concern you have already raised today
- Tone: calm, competent, like a butler who has already handled it"""
