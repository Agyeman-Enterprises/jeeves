"""
Nexus Client — Business intelligence integration.
Queries portfolio, alerts, entity health, and triggers agent runs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class NexusClient:
    """HTTP client for Nexus business intelligence."""

    def __init__(self):
        s = get_settings()
        self.base_url = s.nexus_base_url.rstrip("/")
        self.api_key = s.nexus_internal_key
        self._headers = {}
        if self.api_key:
            self._headers["Authorization"] = f"Bearer {self.api_key}"
            self._headers["x-nexus-internal-key"] = self.api_key

    async def get_portfolio_overview(self) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{self.base_url}/api/v1/portfolio/overview", headers=self._headers)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            LOGGER.warning("Nexus portfolio overview failed: %s", exc)
            return {}

    async def get_alerts(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/alerts", headers=self._headers)
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, list) else data.get("alerts", [])
        except Exception as exc:
            LOGGER.warning("Nexus alerts failed: %s", exc)
            return []

    async def get_entities(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/entities", headers=self._headers)
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, list) else data.get("entities", [])
        except Exception as exc:
            LOGGER.warning("Nexus entities failed: %s", exc)
            return []

    async def trigger_agent(self, agent_id: str) -> Dict:
        """Trigger a Nexus agent run."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/api/agents/run",
                    json={"agent_id": agent_id},
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            LOGGER.warning("Nexus agent trigger failed: %s", exc)
            return {"error": str(exc)}

    async def trigger_github_sync(self) -> Dict:
        """Trigger GitHub repo scanning."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/api/cron/github-sync",
                    headers={**self._headers, "x-vercel-cron": "true"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            LOGGER.warning("Nexus GitHub sync failed: %s", exc)
            return {"error": str(exc)}

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/health")
                return resp.status_code == 200
        except Exception:
            return False
