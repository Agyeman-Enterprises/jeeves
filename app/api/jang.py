"""JANG API — LangGraph chat endpoint."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.jang_graph import jang_invoke, get_jang_graph

router = APIRouter(prefix="/jang", tags=["jang"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    interaction_count: int = 0


@router.post("/chat")
async def jang_chat(req: ChatRequest):
    """Send a message through the JANG LangGraph pipeline."""
    result = await jang_invoke(
        user_input=req.message,
        session_id=req.session_id,
        interaction_count=req.interaction_count,
    )
    return result


@router.get("/status")
async def jang_status():
    """JANG graph health check."""
    graph = get_jang_graph()
    try:
        from app.memory.mem0_service import get_mem0
        mem0_available = get_mem0().available
    except Exception:
        mem0_available = False
    return {
        "graph_compiled": graph is not None,
        "mem0_available": mem0_available,
    }
