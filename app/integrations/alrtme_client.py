"""
AlrtMe Client — SMS notifications to Akua.
Used for morning briefings, check-in questions, urgent alerts.
"""

from __future__ import annotations

import logging
from typing import Dict

import httpx

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class AlrtMeClient:
    """Send notifications via AlrtMe."""

    def __init__(self):
        s = get_settings()
        self.base_url = s.alrtme_base_url.rstrip("/")
        self.api_key = s.alrtme_api_key
        self.channel = s.alrtme_channel

    async def send(self, title: str, message: str, priority: str = "normal") -> bool:
        """Send a notification to Akua via AlrtMe."""
        if not self.api_key:
            LOGGER.warning("AlrtMe API key not set — notification not sent")
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.base_url}/api/notify",
                    json={
                        "channel": self.channel,
                        "title": title,
                        "message": message,
                        "priority": priority,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if resp.status_code < 400:
                    LOGGER.info("AlrtMe notification sent: %s", title[:50])
                    return True
                LOGGER.warning("AlrtMe returned %d: %s", resp.status_code, resp.text[:100])
                return False
        except Exception as exc:
            LOGGER.warning("AlrtMe send failed: %s", exc)
            return False
