"""
Morning Cycle — Runs at 7am Guam time.
Evening Check-In — Runs at 6pm Guam time.
"""
from __future__ import annotations
import asyncio
import logging
from app.core.orchestrator import get_orchestrator
from app.brain.mimograph import get_mimograph

LOGGER = logging.getLogger(__name__)

async def _get_guam_weather() -> dict:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": 13.4443, "longitude": 144.7937,
                        "current": "temperature_2m,weathercode",
                        "temperature_unit": "fahrenheit",
                        "timezone": "Pacific/Guam", "forecast_days": 1},
            )
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", {})
            temp_f = current.get("temperature_2m", 82)
            code = current.get("weathercode", 0)
            condition = "clear" if code <= 2 else "overcast" if code <= 3 else "rainy"
            return {"temp_f": temp_f, "condition": condition, "code": code}
    except Exception as exc:
        LOGGER.warning("[Morning] Weather fetch failed: %s", exc)
        return {"temp_f": 82, "condition": "unknown", "code": 0}

async def run_morning_cycle():
    LOGGER.info("[Morning] Starting morning cycle...")
    orch = get_orchestrator()
    orch.suggestions.reset_daily()
    weather = await _get_guam_weather()
    LOGGER.info("[Morning] Weather: %.0fF, %s", weather["temp_f"], weather["condition"])
    try:
        conversations = await orch.aqui.get_recent_conversations(hours=12)
        from app.schemas.events import EventSource, NormalizedEvent
        for conv in conversations[:20]:
            content = conv.get("content", conv.get("text", ""))
            if content:
                orch.event_store.ingest(NormalizedEvent(
                    source=EventSource.AQUI, raw_text=content[:500],
                    inferred_tags=["aqui_memory", "overnight"]))
    except Exception as exc:
        LOGGER.warning("[Morning] Aqui pull failed: %s", exc)
    try:
        briefing = await orch.morning_briefing(weather=weather)
        briefing_text = briefing.get("text", "Good morning. Nothing urgent today.")
    except Exception as exc:
        LOGGER.error("[Morning] Briefing failed: %s", exc)
        briefing_text = "Good morning. Running into a hiccup — will have it sorted shortly."
        briefing = {}

    # Append brain intelligence (goals + contradictions)
    try:
        brain_brief = get_mimograph().generate_morning_briefing()
        brain_text = brain_brief.get("text", "")
        if brain_text:
            briefing_text = briefing_text + "\n\n" + brain_text[:600]
    except Exception as exc:
        LOGGER.warning("[Morning] Brain briefing failed: %s", exc)
    try:
        await orch.alrtme.send(title="JJ Morning Brief", message=briefing_text[:800],
                               priority="normal", source="jj", topic="briefing")
    except Exception as exc:
        LOGGER.warning("[Morning] AlrtMe send failed: %s", exc)
    LOGGER.info("[Morning] Morning cycle complete.")
    return {"status": "complete", "briefing_length": len(briefing_text),
            "weather": weather, "emails": briefing.get("emails_needing_response", 0),
            "shifts": briefing.get("shifts_today", 0)}

async def run_evening_checkin():
    LOGGER.info("[Evening] Starting evening check-in...")
    orch = get_orchestrator()
    try:
        checkin = await orch.evening_checkin()
        text = checkin.get("text", "")
        if text:
            await orch.alrtme.send(title="JJ Evening Check-in", message=text[:500],
                                   priority="low", source="jj", topic="checkin")
    except Exception as exc:
        LOGGER.warning("[Evening] Check-in failed: %s", exc)
    LOGGER.info("[Evening] Evening check-in complete.")

def run_morning_cycle_sync():
    asyncio.run(run_morning_cycle())

def run_evening_checkin_sync():
    asyncio.run(run_evening_checkin())
