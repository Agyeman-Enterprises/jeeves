"""
LiteLLM Client — Real LLM integration.
Uses production LiteLLM/Ollama path on Hetzner.
Falls back to Anthropic if local is down.
No mock responses ever.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class LLMClient:
    """
    Calls the real LLM. No mocks. No hardcoded responses.
    Primary: LiteLLM proxy (ai.agyemanenterprises.com) → DeepSeek-R1 32B
    Fallback: Anthropic Claude via API
    """

    def __init__(self):
        s = get_settings()
        self.primary_url = s.litellm_base_url.rstrip("/")
        self.primary_key = s.litellm_api_key
        self.primary_model = s.litellm_model
        self.fallback_key = s.anthropic_api_key
        self.fallback_model = s.fallback_model

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send messages to LLM, get response text.
        Tries primary (LiteLLM), falls back to Anthropic.
        """
        # Try primary (OpenAI-compatible endpoint via LiteLLM)
        try:
            result = await self._call_litellm(messages, system, temperature, max_tokens)
            if result:
                return result
        except Exception as exc:
            LOGGER.warning("Primary LLM failed: %s — falling back to Anthropic", exc)

        # Fallback to Anthropic
        if self.fallback_key:
            try:
                return await self._call_anthropic(messages, system, temperature, max_tokens)
            except Exception as exc:
                LOGGER.error("Fallback LLM also failed: %s", exc)

        return "[Jeeves: Both LLM backends are down. Please check LiteLLM and Anthropic keys.]"

    async def _call_litellm(
        self, messages: List[Dict], system: str,
        temperature: float, max_tokens: int,
    ) -> Optional[str]:
        """Call LiteLLM OpenAI-compatible endpoint."""
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        headers = {"Content-Type": "application/json"}
        if self.primary_key:
            headers["Authorization"] = f"Bearer {self.primary_key}"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.primary_url}/v1/chat/completions",
                json={
                    "model": self.primary_model,
                    "messages": all_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(
        self, messages: List[Dict], system: str,
        temperature: float, max_tokens: int,
    ) -> str:
        """Call Anthropic Claude API directly."""
        headers = {
            "x-api-key": self.fallback_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.fallback_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            # Anthropic returns content as list of blocks
            return "".join(block["text"] for block in data.get("content", []) if block.get("type") == "text")
