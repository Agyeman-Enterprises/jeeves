"""
Twilio service for SMS, WhatsApp, and voice calls.
Supports future swap to Ghexit via configuration flag.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Configuration from environment
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")  # E.164 format, e.g. +14155551234
WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g. whatsapp:+14155551234

# Future: Ghexit support
GHEXIT_API_BASE_URL = os.getenv("GHEXIT_API_BASE_URL")
GHEXIT_API_KEY = os.getenv("GHEXIT_API_KEY")
USE_GHEXIT = bool(GHEXIT_API_BASE_URL and GHEXIT_API_KEY)

# Try to import Twilio SDK
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    LOGGER.warning("twilio not installed. Install with: pip install twilio")
    Client = None  # type: ignore


class TwilioService:
    """Service for Twilio SMS, WhatsApp, and voice operations."""

    def __init__(self) -> None:
        self.client: Optional[Any] = None
        self.is_configured = False

        if USE_GHEXIT:
            LOGGER.info("Ghexit mode enabled (Twilio replacement)")
            # Ghexit implementation would go here
            return

        if not TWILIO_AVAILABLE:
            LOGGER.warning("Twilio library not available")
            return

        if not ACCOUNT_SID or not AUTH_TOKEN:
            LOGGER.warning(
                "Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN"
            )
            return

        try:
            self.client = Client(ACCOUNT_SID, AUTH_TOKEN)
            self.is_configured = True
            LOGGER.info("Twilio service configured successfully")
        except Exception as exc:
            LOGGER.error("Failed to initialize Twilio client: %s", exc)

    def send_sms(self, to: str, body: str) -> Dict[str, Any]:
        """
        Send SMS via Twilio.

        Args:
            to: Recipient phone number in E.164 format (e.g., +14155551234)
            body: Message body

        Returns:
            Dict with success status and message SID or error
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Twilio not configured. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN",
            }

        if not FROM_NUMBER:
            return {
                "success": False,
                "error": "TWILIO_FROM_NUMBER not configured",
            }

        try:
            message = self.client.messages.create(
                body=body,
                from_=FROM_NUMBER,
                to=to,
            )
            LOGGER.info("SMS sent to %s: %s", to, message.sid)
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
            }
        except Exception as exc:
            LOGGER.error("Failed to send SMS: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }

    def send_whatsapp(self, to: str, body: str) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio.

        Args:
            to: Recipient phone number in E.164 format (e.g., +14155551234)
            body: Message body

        Returns:
            Dict with success status and message SID or error
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Twilio not configured",
            }

        if not WHATSAPP_NUMBER:
            return {
                "success": False,
                "error": "TWILIO_WHATSAPP_NUMBER not configured",
            }

        # Ensure recipient number is in whatsapp: format
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"

        try:
            message = self.client.messages.create(
                body=body,
                from_=WHATSAPP_NUMBER,
                to=to,
            )
            LOGGER.info("WhatsApp message sent to %s: %s", to, message.sid)
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
            }
        except Exception as exc:
            LOGGER.error("Failed to send WhatsApp message: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }

    def make_call(
        self, to: str, twiml_url: Optional[str] = None, message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a voice call via Twilio.

        Args:
            to: Recipient phone number in E.164 format
            twiml_url: Optional TwiML URL to use for call instructions
            message: Optional message to speak (will generate TwiML if twiml_url not provided)

        Returns:
            Dict with success status and call SID or error
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Twilio not configured",
            }

        if not FROM_NUMBER:
            return {
                "success": False,
                "error": "TWILIO_FROM_NUMBER not configured",
            }

        # Generate TwiML URL if message provided
        if message and not twiml_url:
            twiml_url = self._generate_twiml_url(message)

        if not twiml_url:
            return {
                "success": False,
                "error": "Either twiml_url or message must be provided",
            }

        try:
            call = self.client.calls.create(
                to=to,
                from_=FROM_NUMBER,
                url=twiml_url,
            )
            LOGGER.info("Call initiated to %s: %s", to, call.sid)
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
            }
        except Exception as exc:
            LOGGER.error("Failed to make call: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }

    def send_tts_call(self, to: str, message: str) -> Dict[str, Any]:
        """
        Make a voice call with text-to-speech message.

        Args:
            to: Recipient phone number in E.164 format
            message: Message to speak via TTS

        Returns:
            Dict with success status and call SID or error
        """
        return self.make_call(to=to, message=message)

    def _generate_twiml_url(self, message: str) -> str:
        """
        Generate a TwiML URL for speaking a message.
        For now, returns a simple TwiML string that can be hosted.
        In production, you'd host this on a webhook endpoint.
        """
        # Escape message for XML
        escaped_message = (
            message.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

        # Generate TwiML
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">{escaped_message}</Say>
    <Pause length="1"/>
    <Say voice="alice" language="en-US">Goodbye.</Say>
</Response>"""

        # Use webhook endpoint on the local server
        # In production, this should be a publicly accessible URL
        # You can also use Twilio TwiML Bins for static TwiML
        base_url = os.getenv("JARVIS_BASE_URL", "http://localhost:8000")
        webhook_url = f"{base_url}/api/communications/twilio/twiml?message={quote(message)}"
        
        LOGGER.info("Using TwiML webhook URL: %s", webhook_url)
        return webhook_url

    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return self.is_configured


# Singleton instance
twilio_service = TwilioService()
