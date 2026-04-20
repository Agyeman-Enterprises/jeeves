"""
GHEXIT Service — JARVIS communications layer.

GHEXIT handles SMS, calls, alerts, and messaging via multiple carriers
(Telnyx, SignalWire, Vonage, Twilio). JARVIS calls GHEXIT to send
notifications, alerts, and messages rather than calling carriers directly.

API base: http://localhost:4000
Auth: Bearer gx_live_xxx (or configured GHEXIT_API_KEY)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

GHEXIT_BASE_URL = os.getenv("GHEXIT_BASE_URL", "http://localhost:4000")
GHEXIT_API_KEY = os.getenv("GHEXIT_API_KEY", "")


class GhexitServiceError(Exception):
    pass


class GhexitService:
    """
    JARVIS → GHEXIT communications client.
    Sends SMS, triggers alerts, and initiates calls via GHEXIT's carrier network.
    """

    def __init__(self) -> None:
        self.base_url = GHEXIT_BASE_URL.rstrip("/")
        self.api_key = GHEXIT_API_KEY
        self.timeout = 15.0

    @property
    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise GhexitServiceError(
                "GHEXIT_API_KEY not configured. Set it in .env."
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}/api/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = getattr(client, method)(url, headers=self._headers, **kwargs)
                resp.raise_for_status()
                return resp.json() if resp.content else {}
        except httpx.HTTPStatusError as e:
            LOGGER.error("GHEXIT %s %s → %s: %s", method.upper(), path, e.response.status_code, e.response.text[:200])
            raise GhexitServiceError(f"GHEXIT request failed: {e.response.status_code}") from e
        except Exception as e:
            LOGGER.error("GHEXIT request error: %s", e)
            raise GhexitServiceError(str(e)) from e

    # ── Messaging ─────────────────────────────────────────────────────────────

    def send_sms(self, to: str, body: str, from_: Optional[str] = None) -> Dict[str, Any]:
        """Send an SMS via GHEXIT."""
        payload: Dict[str, Any] = {"to": to, "body": body}
        if from_:
            payload["from"] = from_
        result = self._request("post", "v1/messages", json=payload)
        LOGGER.info("SMS sent to %s via GHEXIT", to)
        return result

    def list_messages(self, limit: int = 50, status: Optional[str] = None) -> List[Dict]:
        """List recent messages."""
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        return self._request("get", "v1/messages", params=params)

    # ── Alerts ────────────────────────────────────────────────────────────────

    def create_alert(self, name: str, message: str, channels: List[str], **kwargs) -> Dict[str, Any]:
        """Create an alert rule in GHEXIT."""
        payload = {"name": name, "message": message, "channels": channels, **kwargs}
        return self._request("post", "v1/alerts/rules", json=payload)

    def list_alerts(self) -> List[Dict]:
        """List active alert rules."""
        return self._request("get", "v1/alerts/rules")

    # ── Calls ─────────────────────────────────────────────────────────────────

    def make_call(self, to: str, from_: str, webhook_url: str, **kwargs) -> Dict[str, Any]:
        """Initiate an outbound call via GHEXIT."""
        payload = {"to": to, "from": from_, "webhookUrl": webhook_url, **kwargs}
        return self._request("post", "v1/calls", json=payload)

    # ── Health ────────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Returns True if GHEXIT is reachable."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except Exception:
            return False
