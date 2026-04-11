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

    async def send_gate_request(
        self,
        app_name: str,
        results: str,
        actions: Optional[List[Dict]] = None,
        verdict: str = "FAIL",
        summary: str = "",
        priority: str = "high",
    ) -> Optional[str]:
        """
        Send an actionable gate request via AlrtMe.
        Returns the gate token if successful, None if failed.

        The push notification will have Approve/Reject buttons.
        When Akua taps one, AlrtMe posts to the callback_url.

        Args:
            app_name: Which app/service is asking (e.g., ContentForge, claude-code)
            results: What happened / what needs review
            actions: Custom action buttons with callback_urls
            verdict: PASS or FAIL
            summary: Short summary for the notification
            priority: Notification priority
        """
        if not self.api_key:
            LOGGER.warning("AlrtMe API key not set — gate request not sent")
            return None

        jeeves_base = "https://jeeves.agyemanenterprises.com"

        # Default actions: approve/reject posting back to Jeeves
        if not actions:
            actions = [
                {
                    "action": "approve",
                    "title": "Approve",
                    "callback_url": f"{jeeves_base}/webhooks/gate-response",
                    "style": "primary",
                },
                {
                    "action": "reject",
                    "title": "Reject",
                    "callback_url": f"{jeeves_base}/webhooks/gate-response",
                    "style": "danger",
                },
            ]

        try:
            payload = {
                "api_key": self.api_key,
                "app_name": app_name,
                "verdict": verdict,
                "results": results,
                "actions": actions,
                "summary": summary or results[:100],
                "priority": priority,
            }

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/api/gate-request",
                    json=payload,
                )
                if resp.status_code < 400:
                    data = resp.json()
                    token = data.get("token")
                    LOGGER.info("AlrtMe gate request sent: %s (app=%s)", token[:8] if token else "?", app_name)
                    return token
                LOGGER.warning("AlrtMe gate-request returned %d: %s", resp.status_code, resp.text[:200])
                return None
        except Exception as exc:
            LOGGER.warning("AlrtMe gate-request failed: %s", exc)
            return None

    async def poll_gate_response(self, token: str) -> Optional[str]:
        """
        Poll AlrtMe for Akua's response to a gate request.
        Returns: 'approve', 'reject', None (still waiting), or 'expired'.
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/respond/{token}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("expired"):
                        return "expired"
                    return data.get("response")  # None if still waiting
                return None
        except Exception as exc:
            LOGGER.warning("AlrtMe poll failed: %s", exc)
            return None
