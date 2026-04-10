"""
Chat API — The main conversational endpoint.
Every response is memory-grounded via the context assembler.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.orchestrator import get_orchestrator

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Talk to Jeeves. Every response is grounded in goals, memory, and behavior."""
    orch = get_orchestrator()
    response = await orch.chat(req.message, session_id=req.session_id)
    return ChatResponse(response=response, session_id=req.session_id)
