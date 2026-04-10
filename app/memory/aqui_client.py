"""
Aqui Client — Interface to the memory vault.
Retrieves conversation history, canon facts, and context packs.
Writes reflections and observations back.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class AquiClient:
    """HTTP client for Aqui memory vault."""

    def __init__(self):
        s = get_settings()
        self.base_url = s.aqui_base_url.rstrip("/")
        self.api_key = s.aqui_api_key
        self._headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Aqui for relevant memories."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/search",
                    json={"query": query, "limit": limit},
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as exc:
            LOGGER.warning("Aqui search failed: %s", exc)
            return []

    async def get_context_pack(self, goal: str, max_tokens: int = 2500) -> Dict:
        """Build a context pack for a specific goal."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/context-pack",
                    json={"goal": goal, "max_tokens": max_tokens, "include_canon": True},
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            LOGGER.warning("Aqui context pack failed: %s", exc)
            return {}

    async def get_canon_facts(self, scope: str = None) -> List[Dict]:
        """Get canon (ground truth) facts."""
        try:
            params = {}
            if scope:
                params["scope"] = scope
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/canon",
                    params=params,
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json().get("facts", [])
        except Exception as exc:
            LOGGER.warning("Aqui canon facts failed: %s", exc)
            return []

    async def get_recent_conversations(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """Get recent conversation chunks for learning."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/search",
                    json={"query": "recent conversations and decisions", "limit": limit},
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as exc:
            LOGGER.warning("Aqui recent conversations failed: %s", exc)
            return []

    async def write_reflection(self, content: str, importance: int = 7) -> bool:
        """Write a reflection back to Aqui."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.base_url}/ingest",
                    json={
                        "content": content,
                        "source": "jeeves_reflection",
                        "importance": importance,
                    },
                    headers=self._headers,
                )
                return resp.status_code < 400
        except Exception as exc:
            LOGGER.warning("Aqui write reflection failed: %s", exc)
            return False

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/")
                return resp.status_code == 200
        except Exception:
            return False
