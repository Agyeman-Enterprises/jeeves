"""
Nightly Reconciliation — Runs at 11pm Guam time.
1. Reconcile what Akua said vs did today
2. Run full weight update (decay, recalculate effective weights)
3. Generate reflections
4. Plan tomorrow
5. Write reflections to Aqui
"""

from __future__ import annotations

import asyncio
import logging

from app.core.orchestrator import get_orchestrator
from app.brain.mimograph import get_mimograph
from app.brain.user_model import UserModel

LOGGER = logging.getLogger(__name__)

_brain_user_model = UserModel()


async def run_nightly_reconciliation():
    """Execute the nightly sleep cycle."""
    LOGGER.info("[Nightly] 🌙 Starting nightly reconciliation...")
    orch = get_orchestrator()

    # 1. Run full weight update with decay
    try:
        update_result = orch.weighting.run_nightly_update()
        LOGGER.info("[Nightly] Weight update: %d goals changed", update_result.get("goals_updated", 0))
    except Exception as exc:
        LOGGER.error("[Nightly] Weight update failed: %s", exc)

    # 2. Generate contradiction report
    contradictions = orch.contradictions.get_full_contradiction_report()
    critical = [c for c in contradictions if c.get("severity") == "critical"]
    LOGGER.info("[Nightly] Contradictions: %d total, %d critical", len(contradictions), len(critical))

    # 3. Generate reflections via LLM
    reflections = []
    try:
        # Get today's events for reflection
        events = orch.event_store.query(hours=24, limit=50)
        goals = orch.weighting.get_goals()

        if events:
            reflection_prompt = (
                f"Reflect on Akua's day. She had {len(events)} recorded events.\n"
                f"Events summary: {'; '.join(e.get('raw_text', '')[:50] for e in events[:10])}\n"
                f"Top goal weights: {'; '.join(g['label'] + '=' + str(round(g.get('effective_weight', 0) * 100)) + '%' for g in goals[:5])}\n"
                f"Critical contradictions: {len(critical)}\n\n"
                f"Generate 3 concise reflections about patterns, progress, and concerns.\n"
                f"Format: one sentence each, direct and specific."
            )
            system = await orch.context.assemble()
            reflection_text = await orch.llm.complete(
                messages=[{"role": "user", "content": reflection_prompt}],
                system=system,
                max_tokens=500,
                temperature=0.5,
            )
            reflections = reflection_text.split("\n")
            reflections = [r.strip() for r in reflections if r.strip() and len(r.strip()) > 10]
    except Exception as exc:
        LOGGER.warning("[Nightly] Reflection generation failed: %s", exc)

    # 4. Write reflections to Aqui
    for r in reflections[:5]:
        try:
            await orch.aqui.write_reflection(r, importance=7)
        except Exception as exc:
            LOGGER.warning("[Nightly] Aqui reflection write failed: %s", exc)

    # 5. Plan tomorrow (interventions for morning)
    tomorrow_interventions = orch.interventions.decide_interventions(max_interventions=5)
    LOGGER.info("[Nightly] Tomorrow's interventions: %d", len(tomorrow_interventions))

    # 6. JJ Brain: decay goal weights + run reflection cycle
    brain_reflections = []
    try:
        _brain_user_model.run_nightly_decay()
        brain_reflections = get_mimograph().run_reflection_cycle()
        LOGGER.info("[Nightly] Brain: %d reflections generated", len(brain_reflections))
    except Exception as exc:
        LOGGER.warning("[Nightly] Brain reflection cycle failed: %s", exc)

    LOGGER.info("[Nightly] 🌙 Nightly reconciliation complete. %d reflections, %d brain reflections, %d tomorrow interventions.",
                len(reflections), len(brain_reflections), len(tomorrow_interventions))

    return {
        "status": "complete",
        "goals_updated": update_result.get("goals_updated", 0) if isinstance(update_result, dict) else 0,
        "contradictions_found": len(contradictions),
        "critical_contradictions": len(critical),
        "reflections_generated": len(reflections),
        "tomorrow_interventions": len(tomorrow_interventions),
        "brain_reflections": len(brain_reflections),
    }


def run_nightly_reconciliation_sync():
    """Sync wrapper for APScheduler."""
    asyncio.run(run_nightly_reconciliation())
