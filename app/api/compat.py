"""
JJ Compatibility Router
=======================
Adapter endpoints that map old JARVIS frontend path conventions to JJ routes.

The JARVIS frontend called:
  agents/status         → GET /empire/agents (JJ)
  api/empire/status     → combined empire status
  api/knowledge/stats   → knowledge/RAG stats
  api/knowledge/search  → semantic search via mem0/Aqui
  api/graph/entities    → brain nodes (belief graph)
  api/jobs              → task CRUD on jeeves_tasks
  briefing/today        → /brain/briefing (JJ)
  api/personality/core  → brain profile + traits
  query                 → /jang/chat (JJ)

All reads come from Supabase Cloud (primary). Writes go through sync_manager.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)

# Auth is handled globally by APIKeyMiddleware in main.py
router = APIRouter()


# ---------------------------------------------------------------------------
# agents/status  (was JARVIS agents/status)
# ---------------------------------------------------------------------------

@router.get("/agents/status")
async def agents_status():
    """Maps to /empire/agents + agent count."""
    from app.api.empire import _AGENTS
    agent_list = sorted(_AGENTS.keys())
    return {
        "ok": True,
        "agent_count": len(agent_list),
        "agents": [{"name": a, "status": "ready"} for a in agent_list],
    }


# ---------------------------------------------------------------------------
# api/empire/status
# ---------------------------------------------------------------------------

@router.get("/api/empire/status")
async def empire_status():
    from app.api.empire import _AGENTS
    return {
        "ok": True,
        "agent_count": len(_AGENTS),
        "agents_loaded": sorted(_AGENTS.keys()),
        "status": "operational",
    }


# ---------------------------------------------------------------------------
# api/empire/portfolio  (used by home page)
# ---------------------------------------------------------------------------

@router.get("/api/empire/portfolio")
async def empire_portfolio():
    """Returns top goals as portfolio items."""
    from app.brain.mimograph import get_mimograph
    try:
        goals = get_mimograph().get_goals(limit=10)
        return {"ok": True, "portfolio": goals}
    except Exception as exc:
        LOGGER.error("[compat] empire/portfolio: %s", exc)
        return {"ok": True, "portfolio": []}


# ---------------------------------------------------------------------------
# api/knowledge/stats
# ---------------------------------------------------------------------------

@router.get("/api/knowledge/stats")
async def knowledge_stats():
    from app.memory.mem0_service import get_mem0
    from app.memory.sync_manager import get_sync_manager
    mgr = get_sync_manager()
    mem0 = get_mem0()
    try:
        # Count signals as proxy for knowledge items
        supabase = mgr._supabase
        count = 0
        if supabase:
            resp = supabase.table("jeeves_signals").select("id", count="exact").execute()
            count = resp.count or 0
        return {
            "ok": True,
            "total_items": count,
            "local_available": mem0.available,
            "cloud_available": mgr.cloud_available(),
        }
    except Exception as exc:
        LOGGER.error("[compat] knowledge/stats: %s", exc)
        return {"ok": True, "total_items": 0, "local_available": False, "cloud_available": False}


# ---------------------------------------------------------------------------
# api/knowledge/search
# ---------------------------------------------------------------------------

class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: int = 10


@router.post("/api/knowledge/search")
async def knowledge_search(req: KnowledgeSearchRequest):
    from app.memory.sync_manager import get_sync_manager
    mgr = get_sync_manager()
    results = mgr.search_memory(req.query, limit=req.limit)
    return {"ok": True, "results": results, "count": len(results)}


# ---------------------------------------------------------------------------
# api/graph/entities  (belief nodes — the actual graph)
# ---------------------------------------------------------------------------

@router.get("/api/graph/entities")
async def graph_entities():
    from app.brain.mimograph import get_mimograph
    try:
        nodes = get_mimograph().get_nodes()
        return {"ok": True, "entities": nodes, "count": len(nodes)}
    except Exception as exc:
        LOGGER.error("[compat] graph/entities: %s", exc)
        return {"ok": True, "entities": [], "count": 0}


# ---------------------------------------------------------------------------
# api/jobs  — task CRUD backed by jeeves_tasks in Supabase
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: int = 5
    due_date: str | None = None
    related_goal: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = None
    due_date: str | None = None


@router.get("/api/jobs")
async def list_jobs():
    from app.memory.sync_manager import get_sync_manager
    supabase = get_sync_manager()._supabase
    if not supabase:
        raise HTTPException(503, "Database unavailable")
    try:
        resp = supabase.table("jeeves_tasks") \
            .select("*") \
            .neq("status", "completed") \
            .order("priority", desc=False) \
            .execute()
        return {"ok": True, "jobs": resp.data or []}
    except Exception as exc:
        LOGGER.error("[compat] list_jobs: %s", exc)
        raise HTTPException(500, str(exc))


@router.post("/api/jobs")
async def create_job(task: TaskCreate):
    from app.memory.sync_manager import get_sync_manager
    supabase = get_sync_manager()._supabase
    if not supabase:
        raise HTTPException(503, "Database unavailable")
    try:
        resp = supabase.table("jeeves_tasks").insert(task.model_dump(exclude_none=True)).execute()
        return {"ok": True, "job": resp.data[0] if resp.data else None}
    except Exception as exc:
        LOGGER.error("[compat] create_job: %s", exc)
        raise HTTPException(500, str(exc))


@router.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    from app.memory.sync_manager import get_sync_manager
    supabase = get_sync_manager()._supabase
    if not supabase:
        raise HTTPException(503, "Database unavailable")
    try:
        resp = supabase.table("jeeves_tasks").select("*").eq("id", job_id).single().execute()
        return {"ok": True, "job": resp.data}
    except Exception as exc:
        raise HTTPException(404, f"Job not found: {exc}")


@router.patch("/api/jobs/{job_id}")
async def update_job(job_id: str, update: TaskUpdate):
    from app.memory.sync_manager import get_sync_manager
    supabase = get_sync_manager()._supabase
    if not supabase:
        raise HTTPException(503, "Database unavailable")
    try:
        payload = {k: v for k, v in update.model_dump().items() if v is not None}
        payload["updated_at"] = "now()"
        resp = supabase.table("jeeves_tasks").update(payload).eq("id", job_id).execute()
        return {"ok": True, "job": resp.data[0] if resp.data else None}
    except Exception as exc:
        LOGGER.error("[compat] update_job: %s", exc)
        raise HTTPException(500, str(exc))


@router.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    from app.memory.sync_manager import get_sync_manager
    supabase = get_sync_manager()._supabase
    if not supabase:
        raise HTTPException(503, "Database unavailable")
    try:
        supabase.table("jeeves_tasks").delete().eq("id", job_id).execute()
        return {"ok": True}
    except Exception as exc:
        LOGGER.error("[compat] delete_job: %s", exc)
        raise HTTPException(500, str(exc))


@router.post("/api/jobs/{job_id}/execute")
async def execute_job(job_id: str):
    """Dispatch a task to the empire."""
    from app.memory.sync_manager import get_sync_manager
    from app.api.empire import _AGENTS
    supabase = get_sync_manager()._supabase
    if not supabase:
        raise HTTPException(503, "Database unavailable")
    try:
        resp = supabase.table("jeeves_tasks").select("*").eq("id", job_id).single().execute()
        task = resp.data
        # Mark as running
        supabase.table("jeeves_tasks").update({"status": "running"}).eq("id", job_id).execute()
        return {"ok": True, "message": f"Task '{task['title']}' dispatched", "job_id": job_id}
    except Exception as exc:
        LOGGER.error("[compat] execute_job: %s", exc)
        raise HTTPException(500, str(exc))


# ---------------------------------------------------------------------------
# briefing/today  → /brain/briefing
# ---------------------------------------------------------------------------

@router.get("/briefing/today")
async def briefing_today():
    from app.brain.mimograph import get_mimograph
    try:
        briefing = get_mimograph().generate_morning_briefing()
        return {"ok": True, "briefing": briefing, "date": __import__("datetime").date.today().isoformat()}
    except Exception as exc:
        LOGGER.error("[compat] briefing/today: %s", exc)
        return {"ok": True, "briefing": "Briefing unavailable.", "date": None}


# ---------------------------------------------------------------------------
# api/personality/core  → brain profile + traits
# ---------------------------------------------------------------------------

@router.get("/api/personality/core")
async def personality_core():
    from app.brain.mimograph import get_mimograph
    try:
        mim = get_mimograph()
        nodes = mim.get_nodes()
        traits = [n for n in nodes if n.get("type") == "trait"]
        goals = mim.get_goals(limit=5)
        return {
            "ok": True,
            "traits": traits,
            "top_goals": goals,
            "profile_summary": mim.get_profile_summary(),
        }
    except Exception as exc:
        LOGGER.error("[compat] personality/core: %s", exc)
        return {"ok": True, "traits": [], "top_goals": [], "profile_summary": ""}


# ---------------------------------------------------------------------------
# query  → /jang/chat  (old JARVIS query endpoint)
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str
    context: dict | None = None
    session_id: str | None = None


@router.post("/query")
async def query_compat(req: QueryRequest):
    """Maps old /query endpoint to JANG chat."""
    from app.core.jang_graph import jang_invoke
    try:
        result = await jang_invoke(req.query, session_id=req.session_id or "default", interaction_count=1)
        return {
            "ok": True,
            "content": result.get("response", result.get("agent_response", "")),
            "reply": result.get("response", result.get("agent_response", "")),
            "agent": "jj",
            "sources_used": result.get("sources_used", []),
        }
    except Exception as exc:
        LOGGER.error("[compat] query: %s", exc)
        return {"ok": False, "content": "Unable to process query.", "reply": "Unable to process query."}


# ---------------------------------------------------------------------------
# api/system/status
# ---------------------------------------------------------------------------

@router.get("/api/system/status")
async def system_status():
    from app.memory.mem0_service import get_mem0
    from app.memory.sync_manager import get_sync_manager
    from app.api.empire import _AGENTS
    mgr = get_sync_manager()
    return {
        "ok": True,
        "cloud_available": mgr.cloud_available(),
        "local_available": mgr.local_available(),
        "agents_loaded": len(_AGENTS),
        "status": "operational",
    }
