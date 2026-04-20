"""
JJ Memory Service — mem0ai local vector store.
Fallback when Aqui (Hetzner) is unreachable.
Short-term: mem0 in-process qdrant (survives restarts via local file)
Long-term: Aqui knowledge vault (when available)
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.config import get_settings

LOGGER = logging.getLogger(__name__)

try:
    from mem0 import Memory
    _MEM0_AVAILABLE = True
except ImportError:
    _MEM0_AVAILABLE = False
    LOGGER.warning("[mem0] Not installed — pip install mem0ai qdrant-client")

_USER_ID = "akua"


def _build_config() -> dict:
    s = get_settings()
    data_dir = os.getenv("JJ_MEM0_DIR", "/app/data/mem0")
    os.makedirs(data_dir, exist_ok=True)
    return {
        "llm": {
            "provider": "anthropic",
            "config": {
                "model": s.fallback_model,
                "api_key": s.anthropic_api_key,
                "max_tokens": 2048,
                "temperature": 0.1,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
            },
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "jj_memory",
                "path": data_dir,
            },
        },
        "history_db_path": f"{data_dir}/history.db",
    }


class JJMemoryService:
    """
    mem0-backed local memory for JJ.
    Used as fallback when Aqui is unreachable, and for short-term session context.
    """

    def __init__(self) -> None:
        self._mem: Any = None
        self._available = False
        if not _MEM0_AVAILABLE:
            return
        try:
            self._mem = Memory.from_config(_build_config())
            self._available = True
            LOGGER.info("[mem0] Memory service initialized ✓")
        except Exception as exc:
            LOGGER.error("[mem0] Init failed: %s", exc)

    @property
    def available(self) -> bool:
        return self._available

    def add(self, content: str, metadata: dict = None) -> list:
        if not self._available:
            return []
        try:
            result = self._mem.add(content, user_id=_USER_ID, metadata=metadata or {})
            return result if isinstance(result, list) else []
        except Exception as exc:
            LOGGER.error("[mem0] add: %s", exc)
            return []

    def search(self, query: str, limit: int = 10) -> list:
        if not self._available:
            return []
        try:
            results = self._mem.search(query, user_id=_USER_ID, limit=limit)
            return results if isinstance(results, list) else []
        except Exception as exc:
            LOGGER.error("[mem0] search: %s", exc)
            return []

    def get_context_block(self, query: str, limit: int = 8) -> str:
        """Formatted memory block for LLM prompt injection."""
        memories = self.search(query, limit=limit)
        lines = [f"• {m['memory']}" for m in memories
                 if m.get("memory") and m.get("score", 0) > 0.3]
        if not lines:
            return ""
        return "Relevant memories:\n" + "\n".join(lines)

    def record_preference(self, preference: str, context: str, outcome: str = "positive"):
        self.add(f"PREFERENCE [{outcome}]: {preference} (context: {context})",
                 metadata={"type": "preference", "outcome": outcome})

    def record_reflection(self, insight: str):
        self.add(f"REFLECTION: {insight}", metadata={"type": "reflection"})


# Singleton
_instance: JJMemoryService = None


def get_mem0() -> JJMemoryService:
    global _instance
    if _instance is None:
        _instance = JJMemoryService()
    return _instance
