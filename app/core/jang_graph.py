"""
JANG Graph — LangGraph state machine for JJ.

  START
    → retrieve_memory      (mem0: what do we know about this user/topic?)
    → query_rag            (Aqui: what knowledge is relevant?)
    → synthesize           (Claude: generate response with full context)
    → score_importance     (heuristic: how novel/important was this turn?)
    → [conditional]
        ├── reflect        (every 10 turns or importance > 0.8)
        └── ─────────────→ write_back  (Aqui + mem0: persist new knowledge)
    → respond
    END
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Literal

LOGGER = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END, START
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    LOGGER.warning("[jang] langgraph not installed — JANG graph disabled. pip install langgraph")

from app.core.jang_state import JANGState

_rag_service = None
_mem0 = None


def _get_mem0():
    global _mem0
    if _mem0 is None:
        try:
            from app.memory.mem0_service import get_mem0
            svc = get_mem0()
            _mem0 = svc if svc.available else None
        except Exception as exc:
            LOGGER.error("[jang] Failed to init mem0: %s", exc)
    return _mem0


def _get_rag():
    global _rag_service
    if _rag_service is None:
        try:
            from app.services.rag_service import RAGService
            _rag_service = RAGService()
        except Exception as exc:
            LOGGER.debug("[jang] RAGService not available (Phase 5): %s", exc)
    return _rag_service


SPECIALIZED_INTENTS = {
    "calendar", "schedule", "meeting", "appointment",
    "email", "send email", "draft email",
    "file", "document", "dropbox", "drive",
    "task", "todo", "reminder",
    "sms", "text", "message",
    "finance", "invoice", "payment",
    "shift", "amion", "hospital",
    "whozoncall", "on-call",
    "ad", "advertisement", "campaign",
    "linkedin", "social media",
    "browse", "search web", "scrape",
}


def _needs_orchestrator(user_input: str, intent: str | None) -> bool:
    if intent and intent.lower() in SPECIALIZED_INTENTS:
        return True
    text = user_input.lower()
    return any(kw in text for kw in SPECIALIZED_INTENTS)


# ── Graph Nodes ────────────────────────────────────────────────────────────────

def retrieve_memory_node(state: JANGState) -> dict:
    t0 = time.time()
    mem = _get_mem0()
    memory_context = ""

    if mem:
        # JJ mem0 is single-user — no user_id param needed
        memory_context = mem.get_context_block(query=state["user_input"], limit=8)

    elapsed = round((time.time() - t0) * 1000, 1)
    latency = dict(state.get("latency_ms", {}))
    latency["retrieve_memory"] = elapsed
    LOGGER.debug("[jang] retrieve_memory: %d chars, %.1fms", len(memory_context), elapsed)
    return {"memory_context": memory_context, "latency_ms": latency}


def query_rag_node(state: JANGState) -> dict:
    t0 = time.time()
    rag = _get_rag()
    rag_context = ""

    if rag:
        try:
            result = rag.query_all(state["user_input"])
            if isinstance(result, dict):
                rag_context = result.get("combined_context", "")
            elif isinstance(result, str):
                rag_context = result
        except Exception as exc:
            LOGGER.error("[jang] RAG query failed: %s", exc)

    elapsed = round((time.time() - t0) * 1000, 1)
    latency = dict(state.get("latency_ms", {}))
    latency["query_rag"] = elapsed
    LOGGER.debug("[jang] query_rag: %d chars, %.1fms", len(rag_context), elapsed)
    return {"rag_context": rag_context, "latency_ms": latency}


def synthesize_node(state: JANGState) -> dict:
    t0 = time.time()
    user_input = state["user_input"]
    intent = state.get("intent")
    use_orch = _needs_orchestrator(user_input, intent)

    response = _direct_claude_synthesis(state)

    elapsed = round((time.time() - t0) * 1000, 1)
    latency = dict(state.get("latency_ms", {}))
    latency["synthesize"] = elapsed
    return {
        "agent_response": response,
        "new_facts": [],
        "use_orchestrator": use_orch,
        "latency_ms": latency,
    }


def _direct_claude_synthesis(state: JANGState) -> str:
    try:
        import anthropic
        from app.config import get_settings
        client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)

        system = (
            "You are JJ — Dr. Akua Agyeman's personal butler and chief of staff.\n"
            "Work first, report second. Under 150 words unless detail is requested.\n"
            "Never lecture. Never moralize. Tone: calm, competent."
        )

        context_parts = []
        if state.get("memory_context"):
            context_parts.append(f"Memory:\n{state['memory_context']}")
        if state.get("rag_context"):
            context_parts.append(f"Knowledge:\n{state['rag_context']}")

        user_msg = state["user_input"]
        if context_parts:
            user_msg = "\n\n".join(context_parts) + f"\n\nUser: {user_msg}"

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return msg.content[0].text if msg.content else ""
    except Exception as exc:
        LOGGER.error("[jang] Direct Claude synthesis failed: %s", exc)
        return "I encountered an error processing your request. Please try again."


def score_importance_node(state: JANGState) -> dict:
    t0 = time.time()
    importance = 0.5

    text = state["user_input"].lower()
    high_signals = [
        "prefer", "always", "never", "decide", "plan", "goal",
        "important", "remember", "from now on", "i like", "i don't like",
        "critical", "urgent", "emergency", "immediately", "seized", "irs",
        "debt", "due now", "passport", "blocked", "crisis", "help me",
    ]
    if any(sig in text for sig in high_signals):
        importance = 0.85
    elif "?" in state["user_input"]:
        importance = 0.4

    elapsed = round((time.time() - t0) * 1000, 1)
    latency = dict(state.get("latency_ms", {}))
    latency["score_importance"] = elapsed

    count = state.get("interaction_count", 0) + 1
    should_reflect = (count % 10 == 0) or (importance >= 0.8)

    LOGGER.debug("[jang] importance=%.2f, count=%d, reflect=%s", importance, count, should_reflect)
    return {
        "importance_score": importance,
        "interaction_count": count,
        "should_reflect": should_reflect,
        "latency_ms": latency,
    }


def reflect_node(state: JANGState) -> dict:
    t0 = time.time()
    reflection = None
    mem = _get_mem0()

    if mem:
        try:
            recent_mems = mem.search(state.get("user_input", "recent activity"), limit=20)
            if recent_mems:
                memory_text = "\n".join(
                    f"• {m.get('memory', '')}" for m in recent_mems if m.get("memory")
                )
                if memory_text:
                    try:
                        import anthropic
                        from app.config import get_settings
                        client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
                        msg = client.messages.create(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=512,
                            messages=[{"role": "user", "content": (
                                f"Based on these recent memories, generate one key insight:\n{memory_text}"
                            )}],
                        )
                        reflection = msg.content[0].text if msg.content else None
                        if reflection:
                            mem.record_reflection(reflection)
                            LOGGER.info("[jang] Reflection generated and stored")
                    except Exception as exc:
                        LOGGER.error("[jang] Reflection synthesis failed: %s", exc)
        except Exception as exc:
            LOGGER.error("[jang] Reflection failed: %s", exc)

    elapsed = round((time.time() - t0) * 1000, 1)
    latency = dict(state.get("latency_ms", {}))
    latency["reflect"] = elapsed
    return {"reflection": reflection, "latency_ms": latency}


def write_back_node(state: JANGState) -> dict:
    t0 = time.time()
    importance = state.get("importance_score", 0.5)

    # Dual-write: Supabase Cloud (primary) → local mem0 (secondary, queued if down)
    try:
        from app.memory.sync_manager import get_sync_manager
        mgr = get_sync_manager()
        conversation_summary = (
            f"User: {state['user_input']}\n"
            f"JJ: {state.get('agent_response', '')[:500]}"
        )
        mgr.write_memory(
            conversation_summary,
            metadata={
                "type": "conversation",
                "importance": importance,
                "session_id": state.get("session_id", ""),
            },
        )
        for fact in state.get("new_facts", []):
            if fact:
                mgr.write_memory(fact, metadata={"type": "fact", "importance": importance})
    except Exception as exc:
        LOGGER.error("[jang] sync_manager write-back failed: %s", exc)

    # Write to Aqui for high-importance turns (supplementary — non-critical path)
    if importance >= 0.6:
        try:
            _write_to_aqui(state)
        except Exception as exc:
            LOGGER.debug("[jang] Aqui write-back failed (non-fatal): %s", exc)

    elapsed = round((time.time() - t0) * 1000, 1)
    latency = dict(state.get("latency_ms", {}))
    latency["write_back"] = elapsed
    return {"latency_ms": latency}


def _write_to_aqui(state: JANGState) -> None:
    import httpx
    aqui_url = os.getenv("AQUI_BASE_URL", "")
    aqui_key = os.getenv("AQUI_API_KEY", "")
    if not aqui_url or not aqui_key:
        return
    payload = {
        "source": "jj_jang_write_back",
        "content": (
            f"[importance={state.get('importance_score', 0):.2f}]\n\n"
            f"User: {state['user_input']}\n\n"
            f"JJ: {state.get('agent_response', '')}"
        ),
    }
    with httpx.Client(timeout=5.0) as client:
        client.post(
            f"{aqui_url.rstrip('/')}/ingest",
            json=payload,
            headers={"Authorization": f"Bearer {aqui_key}"},
        )


def respond_node(state: JANGState) -> dict:
    sources = []
    if state.get("memory_context"):
        sources.append("mem0")
    if state.get("rag_context"):
        sources.append("rag")
    if state.get("reflection"):
        sources.append("reflection")
    return {"sources_used": sources}


def should_reflect_edge(state: JANGState) -> Literal["reflect", "write_back"]:
    return "reflect" if state.get("should_reflect") else "write_back"


# ── Graph Builder ──────────────────────────────────────────────────────────────

def build_jang_graph():
    if not _LANGGRAPH_AVAILABLE:
        LOGGER.warning("[jang] LangGraph not available — graph not built")
        return None
    try:
        graph = StateGraph(JANGState)
        graph.add_node("retrieve_memory", retrieve_memory_node)
        graph.add_node("query_rag", query_rag_node)
        graph.add_node("synthesize", synthesize_node)
        graph.add_node("score_importance", score_importance_node)
        graph.add_node("reflect", reflect_node)
        graph.add_node("write_back", write_back_node)
        graph.add_node("respond", respond_node)

        graph.add_edge(START, "retrieve_memory")
        graph.add_edge("retrieve_memory", "query_rag")
        graph.add_edge("query_rag", "synthesize")
        graph.add_edge("synthesize", "score_importance")
        graph.add_conditional_edges(
            "score_importance",
            should_reflect_edge,
            {"reflect": "reflect", "write_back": "write_back"},
        )
        graph.add_edge("reflect", "write_back")
        graph.add_edge("write_back", "respond")
        graph.add_edge("respond", END)

        compiled = graph.compile()
        LOGGER.info("[jang] LangGraph compiled ✓")
        return compiled
    except Exception as exc:
        LOGGER.error("[jang] Graph compilation failed: %s", exc)
        return None


_jang_graph = None


def get_jang_graph():
    global _jang_graph
    if _jang_graph is None:
        _jang_graph = build_jang_graph()
    return _jang_graph


async def jang_invoke(
    user_input: str,
    session_id: str | None = None,
    interaction_count: int = 0,
) -> dict:
    """Main entry point for JANG queries. Returns response dict."""
    session_id = session_id or str(uuid.uuid4())
    interaction_id = str(uuid.uuid4())

    initial_state: JANGState = {
        "user_id": "akua",
        "session_id": session_id,
        "interaction_id": interaction_id,
        "user_input": user_input,
        "intent": None,
        "memory_context": "",
        "rag_context": "",
        "use_orchestrator": False,
        "agent_response": "",
        "sources_used": [],
        "importance_score": 0.5,
        "new_facts": [],
        "interaction_count": interaction_count,
        "should_reflect": False,
        "reflection": None,
        "latency_ms": {},
        "error": None,
    }

    graph = get_jang_graph()

    if graph is None:
        response = _direct_claude_synthesis(initial_state)
        return {
            "response": response,
            "sources_used": ["claude_direct"],
            "importance_score": 0.5,
            "reflection": None,
            "latency_ms": {},
            "fallback": True,
        }

    try:
        final_state = graph.invoke(initial_state)
        return {
            "response": final_state.get("agent_response", ""),
            "sources_used": final_state.get("sources_used", []),
            "importance_score": final_state.get("importance_score", 0.5),
            "reflection": final_state.get("reflection"),
            "latency_ms": final_state.get("latency_ms", {}),
            "interaction_count": final_state.get("interaction_count", 0),
            "fallback": False,
        }
    except Exception as exc:
        LOGGER.error("[jang] Graph invocation failed: %s", exc)
        response = _direct_claude_synthesis(initial_state)
        return {
            "response": response,
            "sources_used": ["claude_fallback"],
            "importance_score": 0.5,
            "reflection": None,
            "latency_ms": {},
            "error": str(exc),
            "fallback": True,
        }
