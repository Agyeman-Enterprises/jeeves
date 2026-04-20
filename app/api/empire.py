"""Empire API — agent dispatch routes."""
from __future__ import annotations

import importlib
import logging
import pkgutil
import types
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/empire", tags=["empire"])

# Pre-loaded at module import time — maps agent_name → module object.
# All imports happen here during server startup, never during request handling.
_AGENTS: Dict[str, types.ModuleType] = {}


def _preload_agents() -> None:
    """Import every agent module at startup and store by name."""
    import app.agents as agents_pkg
    try:
        import app.agents.masters as masters_pkg
        pkgs = [(agents_pkg, "app.agents."), (masters_pkg, "app.agents.masters.")]
    except ImportError:
        pkgs = [(agents_pkg, "app.agents.")]

    skip = {"base", "base_master", "base_specialist"}
    for pkg, prefix in pkgs:
        for _, name, _ in pkgutil.iter_modules(pkg.__path__):
            if name.startswith("_") or name in skip:
                continue
            try:
                mod = importlib.import_module(f"{prefix}{name}")  # nosemgrep — name comes from pkgutil.iter_modules on our own package, never from user input
                _AGENTS[name] = mod
            except Exception as exc:
                LOGGER.debug("[Empire] could not load agent %s: %s", name, exc)

    LOGGER.info("[Empire] %d agents pre-loaded", len(_AGENTS))


# Load immediately on module import (happens once at server startup)
_preload_agents()


class AgentRequest(BaseModel):
    agent: str
    task: str
    context: Optional[Dict[str, Any]] = None


@router.post("/dispatch")
async def dispatch_agent(req: AgentRequest):
    """Route a task to a pre-loaded agent (no dynamic imports at request time)."""
    agent_module = _AGENTS.get(req.agent)
    if agent_module is None:
        raise HTTPException(404, f"Agent '{req.agent}' not found")
    try:
        result = await agent_module.run(req.task, context=req.context or {})
        return {"agent": req.agent, "status": "complete", "result": result}
    except Exception as exc:
        LOGGER.error("[Empire] dispatch %s: %s", req.agent, exc)
        raise HTTPException(500, str(exc))


@router.get("/agents")
async def list_agents():
    """List pre-loaded agents."""
    names = sorted(_AGENTS.keys())
    return {"agents": names, "count": len(names)}
