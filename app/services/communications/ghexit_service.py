"""
GHEXIT Communications Service for JARVIS.
Provides SMS, Voice, and Email via GHEXIT API.
Uses shared ports.json for service discovery - NO HARDCODED PORTS.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LOGGER = logging.getLogger(__name__)

# Shared config location
PORTS_CONFIG = Path(os.getenv("PORTS_CONFIG_PATH", r"C:\dev\config\ports.json"))


def _discover_ghexit_port() -> Optional[int]:
    """Read GHEXIT port from shared ports.json."""
    try:
        if PORTS_CONFIG.exists():
            data = json.loads(PORTS_CONFIG.read_text())
            return data.get("ghexit_backend") or data.get("ghexit")
    except Exception as exc:
        LOGGER.debug("Could not read ports.json: %s", exc)
    return None


class GhexitService:
    """
    Service for communications via GHEXIT API.
    Replaces direct Twilio/SignalWire/Resend integrations.
    """

    def __init__(self) -> None:
        self._initialized = False
        self._base_url: Optional[str] = None
        self._headers: Optional[Dict[str, str]] = None
        self._is_configured: Optional[bool] = None
        self.timeout = 30.0

    def _ensure_initialized(self) -> None:
        """Lazy initialization — env var takes priority over ports.json."""
        if self._initialized:
            return

        # Env var always wins (production URL)
        if os.getenv("GHEXIT_BASE_URL"):
            self._base_url = os.getenv("GHEXIT_BASE_URL").rstrip("/")
            LOGGER.info("GHEXIT using env GHEXIT_BASE_URL: %s", self._base_url)
        else:
            # Fall back to local port discovery (dev only)
            discovered_port = _discover_ghexit_port()
            if discovered_port:
                self._base_url = f"http://localhost:{discovered_port}"
                LOGGER.info("GHEXIT discovered at port %d from ports.json", discovered_port)
            else:
                self._base_url = None
                LOGGER.warning("GHEXIT_BASE_URL not set and not found in ports.json")
        
        # API key for auth
        api_key = os.getenv("GHEXIT_API_KEY")
        self._is_configured = bool(api_key and self._base_url)
        
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"
        
        self._initialized = True

    @property
    def base_url(self) -> Optional[str]:
        self._ensure_initialized()
        return self._base_url  # None if not discovered

    @property
    def headers(self) -> Dict[str, str]:
        self._ensure_initialized()
        return self._headers or {"Content-Type": "application/json"}

    @property
    def is_configured(self) -> bool:
        self._ensure_initialized()
        return self._is_configured or False

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to GHEXIT API."""
        self._ensure_initialized()
        
        if not self._base_url:
            return {"success": False, "error": "GHEXIT not discovered - check ports.json"}
        
        url = f"{self._base_url.rstrip('/')}/api/v1/{endpoint.lstrip('/')}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            LOGGER.error("GHEXIT API error: %s %s", exc.response.status_code, exc.response.text)
            return {"success": False, "error": f"GHEXIT API error: {exc.response.status_code}"}
        except httpx.RequestError as exc:
            LOGGER.error("GHEXIT request failed: %s", exc)
            return {"success": False, "error": f"GHEXIT unavailable: {exc}"}

    # ==================== SMS ====================

    def send_sms(self, to: str, body: str, from_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Send SMS via GHEXIT.

        Args:
            to: Recipient phone number in E.164 format
            body: Message body
            from_number: Optional sender number

        Returns:
            Dict with success status and message details
        """
        payload = {"to": to, "body": body}
        if from_number:
            payload["from"] = from_number

        result = self._request("POST", "messages", json_data=payload)
        
        if result.get("success"):
            LOGGER.info("SMS sent via GHEXIT to %s", to)
        return result

    # ==================== Voice ====================

    def make_call(
        self,
        to: str,
        from_number: Optional[str] = None,
        message: Optional[str] = None,
        swml_script: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make a voice call via GHEXIT (SignalWire SWML).

        Args:
            to: Recipient phone number in E.164 format
            from_number: Optional caller ID
            message: Optional TTS message to speak
            swml_script: Optional custom SWML script

        Returns:
            Dict with success status and call details
        """
        payload: Dict[str, Any] = {"to": to}
        
        if from_number:
            payload["from"] = from_number
        if message:
            payload["message"] = message
        if swml_script:
            payload["swmlScript"] = swml_script

        result = self._request("POST", "calls", json_data=payload)
        
        if result.get("success"):
            LOGGER.info("Call initiated via GHEXIT to %s", to)
        return result

    def send_tts_call(self, to: str, message: str) -> Dict[str, Any]:
        """
        Make a voice call with TTS message.

        Args:
            to: Recipient phone number
            message: Message to speak via TTS

        Returns:
            Dict with success status and call details
        """
        return self.make_call(to=to, message=message)

    def hangup_call(self, call_id: str) -> Dict[str, Any]:
        """
        Hangup an active call.

        Args:
            call_id: The call ID to terminate

        Returns:
            Dict with success status
        """
        return self._request("DELETE", f"calls/{call_id}")

    # ==================== Email ====================

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        html: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send email via GHEXIT (Resend).

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            from_email: Optional sender email
            html: Optional HTML body

        Returns:
            Dict with success status and email details
        """
        payload: Dict[str, Any] = {
            "to": to,
            "subject": subject,
            "text": body,
        }
        
        if from_email:
            payload["from"] = from_email
        if html:
            payload["html"] = html

        result = self._request("POST", "emails", json_data=payload)
        
        if result.get("success"):
            LOGGER.info("Email sent via GHEXIT to %s", to)
        return result

    # ==================== Health ====================

    def health_check(self) -> Dict[str, Any]:
        """Check GHEXIT service health."""
        self._ensure_initialized()
        
        if not self._base_url:
            return {"available": False, "error": "GHEXIT not discovered"}
        
        try:
            url = f"{self._base_url.rstrip('/')}/api/health"
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url)
                return {"available": response.status_code == 200, "status": response.status_code}
        except Exception as exc:
            return {"available": False, "error": str(exc)}

    def is_available(self) -> bool:
        """Check if GHEXIT is reachable."""
        return self.health_check().get("available", False)

    def refresh_discovery(self) -> bool:
        """Re-discover GHEXIT port from ports.json. Call if GHEXIT started after JARVIS."""
        self._initialized = False
        self._ensure_initialized()
        return bool(self._base_url)


# Singleton instance (lazy initialized)
ghexit_service = GhexitService()
