"""
AlrtMe Client — Push notifications to Akua.
Used for morning briefings, check-in questions, urgent alerts.

AlrtMe API: POST /api/ingest
Auth: api_key in body (NOT header)
Required fields: api_key, source, title, message
Optional: priority (critical/high/normal/low), topic, data, url, channels
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import httpx

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class AlrtMeClient:
    """Send notifications via AlrtMe /api/ingest endpoint."""

    def __init__(self):
        s = get_settings()
        self.base_url = s.alrtme_base_url.rstrip("/")
        self.api_key = s.alrtme_api_key

    async def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        source: str = "jeeves",
        topic: str = "briefing",
        channels: Optional[List[str]] = None,
    ) -> bool:
        """
        Send a notification to Akua via AlrtMe.

        Args:
            title: Notification title
            message: Notification body
            priority: critical|high|normal|low
            source: Source identifier (default: jeeves)
            topic: Topic for grouping (default: briefing)
            channels: Override delivery channels (default: based on priority)
        """
        if not self.api_key:
            LOGGER.warning("AlrtMe API key not set — notification not sent")
            return False
        try:
            payload = {
                "api_key": self.api_key,
                "source": source,
                "title": title,
                "message": message,
                "priority": priority,
                "topic": topic,
            }
            if channels:
                payload["channels"] = channels

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/api/ingest",
                    json=payload,
                )
                if resp.status_code < 400:
                    LOGGER.info("AlrtMe notification sent: %s (priority=%s)", title[:50], priority)
                    return True
                LOGGER.warning("AlrtMe returned %d: %s", resp.status_code, resp.text[:200])
                return False
        except Exception as exc:
            LOGGER.warning("AlrtMe send failed: %s", exc)
            return False

    async def send_critical(self, title: str, message: str) -> bool:
        """Send critical alert — push + SMS."""
        return await self.send(title, message, priority="critical", topic="alert")

    async def send_briefing(self, message: str) -> bool:
        """Send morning briefing — push only."""
        return await self.send("Jeeves Morning Brief", message, priority="normal", topic="briefing")

    async def send_checkin(self, question: str) -> bool:
        """Send a check-in question — push only."""
        return await self.send("Jeeves Check-in", question, priority="normal", topic="checkin")
