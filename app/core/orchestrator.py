"""
Orchestrator — The one brain. Owns all modules.
Every request flows through here. No module thinks for itself.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List, Optional

from app.config import get_settings
from app.core.context_assembler import ContextAssembler
from app.core.intervention_engine import InterventionEngine
from app.core.planner import Planner
from app.integrations.alrtme_client import AlrtMeClient
from app.integrations.ghexit_client import GhexitClient
from app.integrations.litellm_client import LLMClient
from app.integrations.nexus_client import NexusClient
from app.memory.aqui_client import AquiClient
from app.memory.event_store import EventStore
from app.modeling.contradiction_engine import ContradictionEngine
from app.modeling.mimograph import Mimograph
from app.modeling.weighting_engine import WeightingEngine

LOGGER = logging.getLogger(__name__)


class Orchestrator:
    """
    Jeeves's brain. One instance. Owns everything.
    """

    def __init__(self):
        LOGGER.info("[Jeeves] Initializing orchestrator...")

        # Layer 1-2: Memory
        self.event_store = EventStore()
        self.aqui = AquiClient()

        # Layer 3: Mimograph
        self.mimograph = Mimograph()

        # Layer 4: Weighting
        self.weighting = WeightingEngine(event_store=self.event_store)

        # Contradiction engine (combines L3 + L4)
        self.contradictions = ContradictionEngine(
            weighting=self.weighting,
            mimograph=self.mimograph,
        )

        # Layer 5: Planner
        self.planner = Planner(
            weighting=self.weighting,
            mimograph=self.mimograph,
        )

        # Layer 6: Intervention engine
        self.interventions = InterventionEngine(
            weighting=self.weighting,
            contradictions=self.contradictions,
        )

        # Context assembler (feeds LLM)
        self.context = ContextAssembler(
            weighting=self.weighting,
            mimograph=self.mimograph,
            contradictions=self.contradictions,
            event_store=self.event_store,
            aqui=self.aqui,
        )

        # LLM
        self.llm = LLMClient()

        # Integrations
        self.nexus = NexusClient()
        self.ghexit = GhexitClient()
        self.alrtme = AlrtMeClient()

        LOGGER.info("[Jeeves] Orchestrator ready.")

    async def chat(self, message: str, session_id: str = "default") -> str:
        """
        Main chat endpoint. Every response is memory-grounded.
        """
        # Assemble full context
        system_context = await self.context.assemble(user_message=message)

        # Build message history (for now, single-turn; session history TODO(phase-2))
        messages = [{"role": "user", "content": message}]

        # Call LLM with full context
        response = await self.llm.complete(
            messages=messages,
            system=system_context,
            temperature=0.7,
            max_tokens=2000,
        )

        # Ingest this interaction as an event
        from app.schemas.events import EventSource, NormalizedEvent
        self.event_store.ingest(NormalizedEvent(
            source=EventSource.TEXT,
            raw_text=f"User: {message}\nJeeves: {response[:200]}",
            inferred_tags=["conversation"],
        ))

        return response

    async def morning_briefing(self) -> Dict:
        """Generate the morning intelligence report."""
        goals = self.weighting.get_goals()
        contradictions = self.contradictions.get_full_contradiction_report()
        interventions = self.interventions.decide_interventions()
        countdown = self.weighting.get_retirement_countdown()
        plan = self.planner.generate_day_plan()

        # Get Nexus alerts
        nexus_alerts = await self.nexus.get_alerts()

        briefing = {
            "date": plan.date,
            "retirement_countdown": countdown,
            "top_priorities": plan.top_priorities,
            "what_to_drop": plan.what_to_drop,
            "contradictions": contradictions[:3],
            "interventions": [i.model_dump() for i in interventions],
            "nexus_alerts": nexus_alerts[:5],
            "energy_profile": plan.energy_profile,
        }

        # Generate natural language briefing via LLM
        briefing_prompt = (
            f"Generate a concise morning briefing for Akua. Today is {plan.date}.\n"
            f"Retirement: {countdown['days_left']} days left, need ${countdown['monthly_needed']:,}/mo.\n"
            f"Top priorities: {', '.join(plan.top_priorities[:3])}.\n"
            f"Contradictions: {len(contradictions)} active.\n"
            f"Nexus alerts: {len(nexus_alerts)}.\n"
            f"Energy: {plan.energy_profile}.\n"
            f"Be direct. Be brief. No fluff."
        )
        system = await self.context.assemble()
        text = await self.llm.complete(
            messages=[{"role": "user", "content": briefing_prompt}],
            system=system,
            max_tokens=800,
        )
        briefing["text"] = text

        return briefing

    async def health_check(self) -> Dict:
        """Check all service health."""
        aqui_ok = await self.aqui.health()
        nexus_ok = await self.nexus.health()
        ghexit_ok = await self.ghexit.health()

        goals = self.weighting.get_goals()
        countdown = self.weighting.get_retirement_countdown()

        return {
            "status": "alive",
            "version": get_settings().version,
            "services": {
                "aqui": "ok" if aqui_ok else "down",
                "nexus": "ok" if nexus_ok else "down",
                "ghexit": "ok" if ghexit_ok else "down",
            },
            "brain": {
                "goals_tracked": len(goals),
                "retirement_days": countdown["days_left"],
            },
        }


# ── Singleton ──────────────────────────────────────────────────────────
_instance: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _instance
    if _instance is None:
        _instance = Orchestrator()
    return _instance
