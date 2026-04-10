"""
Morning Cycle — Runs at 7am Guam time.
1. Pull Aqui memories from overnight
2. Update brain model
3. Generate morning briefing
4. Generate check-in questions
5. Send briefing via AlrtMe SMS
"""

from __future__ import annotations

import asyncio
import logging

from app.core.orchestrator import get_orchestrator

LOGGER = logging.getLogger(__name__)


async def run_morning_cycle():
    """Execute the full morning wake-up cycle."""
    LOGGER.info("[Morning] ☀️ Starting morning cycle...")
    orch = get_orchestrator()

    # 1. Pull recent Aqui conversations for learning
    try:
        conversations = await orch.aqui.get_recent_conversations(hours=12)
        LOGGER.info("[Morning] Pulled %d conversations from Aqui", len(conversations))

        # Ingest relevant ones as events
        from app.schemas.events import EventSource, NormalizedEvent
        for conv in conversations[:20]:
            content = conv.get("content", conv.get("text", ""))
            if content:
                orch.event_store.ingest(NormalizedEvent(
                    source=EventSource.AQUI,
                    raw_text=content[:500],
                    inferred_tags=["aqui_memory", "overnight"],
                ))
    except Exception as exc:
        LOGGER.warning("[Morning] Aqui pull failed: %s", exc)

    # 2. Generate morning briefing
    try:
        briefing = await orch.morning_briefing()
        briefing_text = briefing.get("text", "No briefing generated.")
        LOGGER.info("[Morning] Briefing generated (%d chars)", len(briefing_text))
    except Exception as exc:
        LOGGER.error("[Morning] Briefing generation failed: %s", exc)
        briefing_text = f"Morning briefing failed: {exc}"

    # 3. Generate interventions
    interventions = orch.interventions.decide_interventions(max_interventions=3)
    LOGGER.info("[Morning] %d interventions generated", len(interventions))

    # 4. Send via AlrtMe SMS
    try:
        # Truncate for SMS
        sms_text = briefing_text[:800] if len(briefing_text) > 800 else briefing_text
        sent = await orch.alrtme.send(
            title="☀️ Jeeves Morning Brief",
            message=sms_text,
            priority="normal",
        )
        LOGGER.info("[Morning] AlrtMe SMS sent: %s", sent)
    except Exception as exc:
        LOGGER.warning("[Morning] AlrtMe send failed: %s", exc)

    LOGGER.info("[Morning] ☀️ Morning cycle complete.")
    return {"status": "complete", "briefing_length": len(briefing_text), "interventions": len(interventions)}


def run_morning_cycle_sync():
    """Sync wrapper for APScheduler."""
    asyncio.run(run_morning_cycle())
