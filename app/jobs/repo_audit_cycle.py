"""
Repo Audit Cycle — Runs daily at 6am.
Triggers Nexus to scan all GitHub repos.
Classifies apps as MARKET-READY / NEEDS-FIX / NOT-READY.
Reports findings to Jeeves for morning briefing.
"""

from __future__ import annotations

import asyncio
import logging

from app.core.orchestrator import get_orchestrator

LOGGER = logging.getLogger(__name__)


async def run_repo_audit():
    """Trigger Nexus repo scanning and collect results."""
    LOGGER.info("[RepoAudit] 🔍 Starting repo audit cycle...")
    orch = get_orchestrator()

    # Trigger Nexus GitHub sync
    try:
        result = await orch.nexus.trigger_github_sync()
        LOGGER.info("[RepoAudit] Nexus GitHub sync result: %s", result)
    except Exception as exc:
        LOGGER.warning("[RepoAudit] Nexus GitHub sync failed: %s", exc)

    # Get entity list (businesses)
    try:
        entities = await orch.nexus.get_entities()
        LOGGER.info("[RepoAudit] Nexus reports %d entities", len(entities))
    except Exception as exc:
        LOGGER.warning("[RepoAudit] Nexus entities fetch failed: %s", exc)
        entities = []

    # Get any alerts generated
    try:
        alerts = await orch.nexus.get_alerts()
        LOGGER.info("[RepoAudit] %d Nexus alerts active", len(alerts))
    except Exception as exc:
        LOGGER.warning("[RepoAudit] Nexus alerts fetch failed: %s", exc)
        alerts = []

    LOGGER.info("[RepoAudit] 🔍 Repo audit complete. %d entities, %d alerts.", len(entities), len(alerts))
    return {"entities": len(entities), "alerts": len(alerts)}


def run_repo_audit_sync():
    """Sync wrapper for APScheduler."""
    asyncio.run(run_repo_audit())
