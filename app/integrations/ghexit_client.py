"""
Ghexit Client — Communications integration.
Sends SMS, triggers voice calls, manages AI receptionist.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import httpx

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class GhexitClient:
    """HTTP client for Ghexit communications."""

    def __init__(self):
        s = get_settings()
        self.base_url = s.ghexit_base_url.rstrip("/")
        self.token = s.ghexit_service_token
        self._headers = {}
        if self.token:
            self._headers["Authorization"] = f"Bearer {self.token}"

    async def send_sms(self, to: str, message: str) -> Dict:
        """Send SMS via Ghexit."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/api/agent",
                    json={"action": "send_sms", "to": to, "message": message},
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            LOGGER.warning("Ghexit SMS failed: %s", exc)
            return {"error": str(exc)}

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/health")
                return resp.status_code == 200
        except Exception:
            return False
