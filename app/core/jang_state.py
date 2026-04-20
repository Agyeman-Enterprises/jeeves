"""JANG State — LangGraph TypedDict flowing through the JJ JANG graph."""
from __future__ import annotations

from typing import Optional, TypedDict


class JANGState(TypedDict):
    # ── Identity ──────────────────────────────────────────────────────────
    user_id: str
    session_id: str
    interaction_id: str

    # ── Input ─────────────────────────────────────────────────────────────
    user_input: str

    # ── Context retrieval ─────────────────────────────────────────────────
    memory_context: str
    rag_context: str

    # ── Intent / routing ─────────────────────────────────────────────────
    intent: Optional[str]
    use_orchestrator: bool

    # ── Output ────────────────────────────────────────────────────────────
    agent_response: str
    sources_used: list[str]

    # ── Learning signals ──────────────────────────────────────────────────
    importance_score: float
    new_facts: list[str]

    # ── Reflection control ────────────────────────────────────────────────
    interaction_count: int
    should_reflect: bool
    reflection: Optional[str]

    # ── Observability ─────────────────────────────────────────────────────
    latency_ms: dict
    error: Optional[str]
