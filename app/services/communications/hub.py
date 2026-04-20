"""
CommunicationsHub - Unified communications gateway for JARVIS.
Tries Ghexit first, falls back to direct providers (Twilio/Resend/Pushover).
Emits GEM events for all operations via JarvisCoreWriter.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.communications.ghexit_service import ghexit_service
from app.services.communications.twilio_service import twilio_service
from app.services.communications.pushover_service import pushover_service
from app.services.communications.email_service import email_service
from app.services.jarviscore_client import JarvisCoreWriter

LOGGER = logging.getLogger(__name__)

# Singleton GEM writer
_gem_writer: Optional[JarvisCoreWriter] = None


def _get_gem_writer() -> JarvisCoreWriter:
    """Get or create GEM event writer singleton."""
    global _gem_writer
    if _gem_writer is None:
        _gem_writer = JarvisCoreWriter()
    return _gem_writer


class CommunicationsHub:
    """
    Unified communications gateway.

    Priority order:
    1. Ghexit (if available via ports.json discovery)
    2. Direct providers (Twilio, Resend, Pushover)

    All operations emit GEM events for tracking.
    """

    def __init__(self, workspace_id: str = "default", user_id: str = "system"):
        self.workspace_id = workspace_id
        self.user_id = user_id

    def set_context(self, workspace_id: str, user_id: str) -> None:
        """Set workspace and user context for event emission."""
        self.workspace_id = workspace_id
        self.user_id = user_id

    async def _emit_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        subject_id: Optional[str] = None
    ) -> None:
        """Emit a GEM event via JarvisCoreWriter."""
        try:
            writer = _get_gem_writer()
            writer.emit_event(
                event_type=event_type,
                source="agent.communications",
                payload={
                    "workspaceId": self.workspace_id,
                    "userId": self.user_id,
                    **payload
                },
                workspace_id=self.workspace_id if self.workspace_id != "default" else None,
                subject_id=subject_id,
            )
        except Exception as e:
            LOGGER.warning("Failed to emit GEM event %s: %s", event_type, e)

    # ==================== SMS ====================

    async def send_sms(
        self,
        to: str,
        body: str,
        from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS via Ghexit (preferred) or Twilio (fallback).

        Args:
            to: Recipient phone number in E.164 format
            body: Message body
            from_number: Optional sender number

        Returns:
            Dict with success status, message_id, and provider used
        """
        provider_used = "unknown"
        result: Dict[str, Any] = {}
        message_id = str(uuid.uuid4())

        # Try Ghexit first
        if ghexit_service.is_available():
            LOGGER.info("Sending SMS via Ghexit to %s", to)
            result = ghexit_service.send_sms(to=to, body=body, from_number=from_number)
            provider_used = "ghexit"
        else:
            # Fallback to Twilio
            LOGGER.info("Ghexit unavailable, falling back to Twilio for SMS to %s", to)
            result = twilio_service.send_sms(to=to, body=body)
            provider_used = "twilio"
            if result.get("message_sid"):
                message_id = result["message_sid"]

        # Add metadata
        result["provider"] = provider_used
        result["message_id"] = message_id

        # Emit GEM event
        if result.get("success"):
            await self._emit_event(
                "ghexit.sms.sent",
                {
                    "messageId": message_id,
                    "to": to,
                    "body": body[:100] + "..." if len(body) > 100 else body,
                    "provider": provider_used,
                },
                subject_id=message_id
            )
        else:
            await self._emit_event(
                "ghexit.sms.failed",
                {
                    "to": to,
                    "error": result.get("error", "Unknown error"),
                    "provider": provider_used,
                }
            )

        return result

    # ==================== WhatsApp ====================

    async def send_whatsapp(
        self,
        to: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio.
        (Ghexit doesn't support WhatsApp yet)

        Args:
            to: Recipient phone number in E.164 format
            body: Message body

        Returns:
            Dict with success status and message details
        """
        message_id = str(uuid.uuid4())
        result = twilio_service.send_whatsapp(to=to, body=body)

        if result.get("message_sid"):
            message_id = result["message_sid"]

        result["provider"] = "twilio"
        result["message_id"] = message_id

        # Emit GEM event (using sms event type for now)
        if result.get("success"):
            await self._emit_event(
                "ghexit.sms.sent",
                {
                    "messageId": message_id,
                    "to": to,
                    "body": body[:100] + "..." if len(body) > 100 else body,
                    "provider": "twilio-whatsapp",
                },
                subject_id=message_id
            )
        else:
            await self._emit_event(
                "ghexit.sms.failed",
                {
                    "to": to,
                    "error": result.get("error", "Unknown error"),
                    "provider": "twilio-whatsapp",
                }
            )

        return result

    # ==================== Voice Calls ====================

    async def make_call(
        self,
        to: str,
        message: Optional[str] = None,
        twiml_url: Optional[str] = None,
        from_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make a voice call via Ghexit (preferred) or Twilio (fallback).

        Args:
            to: Recipient phone number in E.164 format
            message: Optional TTS message to speak
            twiml_url: Optional TwiML URL
            from_number: Optional caller ID

        Returns:
            Dict with success status and call details
        """
        provider_used = "unknown"
        result: Dict[str, Any] = {}
        call_id = str(uuid.uuid4())

        # Try Ghexit first
        if ghexit_service.is_available():
            LOGGER.info("Making call via Ghexit to %s", to)
            result = ghexit_service.make_call(
                to=to,
                message=message,
                from_number=from_number
            )
            provider_used = "ghexit"
        else:
            # Fallback to Twilio
            LOGGER.info("Ghexit unavailable, falling back to Twilio for call to %s", to)
            result = twilio_service.make_call(
                to=to,
                message=message,
                twiml_url=twiml_url
            )
            provider_used = "twilio"
            if result.get("call_sid"):
                call_id = result["call_sid"]

        result["provider"] = provider_used
        result["call_id"] = call_id

        # Emit GEM event
        if result.get("success"):
            await self._emit_event(
                "ghexit.call.initiated",
                {
                    "callId": call_id,
                    "to": to,
                    "purpose": message[:50] + "..." if message and len(message) > 50 else (message or "TwiML"),
                    "provider": provider_used,
                },
                subject_id=call_id
            )
        else:
            # No specific failed event for calls, use generic error logging
            LOGGER.error("Call failed to %s: %s", to, result.get("error"))

        return result

    async def send_tts_call(self, to: str, message: str) -> Dict[str, Any]:
        """
        Make a voice call with TTS message.

        Args:
            to: Recipient phone number
            message: Message to speak via TTS

        Returns:
            Dict with success status and call details
        """
        return await self.make_call(to=to, message=message)

    # ==================== Email ====================

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        html: Optional[str] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send email via Ghexit (Resend) or direct email service.

        Args:
            to: Recipient email address (or comma-separated list)
            subject: Email subject
            body: Plain text body
            from_email: Optional sender email
            html: Optional HTML body
            template: Optional template name

        Returns:
            Dict with success status and email details
        """
        provider_used = "unknown"
        result: Dict[str, Any] = {}
        email_id = str(uuid.uuid4())

        # Parse recipients
        recipients = [r.strip() for r in to.split(",")]

        # Try Ghexit first
        if ghexit_service.is_available():
            LOGGER.info("Sending email via Ghexit to %s", to)
            result = ghexit_service.send_email(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                html=html
            )
            provider_used = "resend"  # Ghexit uses Resend
        else:
            # Fallback to direct email service (Gmail/Outlook)
            LOGGER.info("Ghexit unavailable, falling back to email service for %s", to)
            result = email_service.send_email(
                to=recipients[0],  # email_service takes single recipient
                subject=subject,
                body=body,
                html=bool(html)
            )
            provider_used = "gmail"  # Default fallback
            if result.get("message_id"):
                email_id = result["message_id"]

        result["provider"] = provider_used
        result["email_id"] = email_id

        # Emit GEM event
        if result.get("success"):
            await self._emit_event(
                "ghexit.email.sent",
                {
                    "emailId": email_id,
                    "to": recipients,
                    "subject": subject,
                    "template": template,
                    "provider": provider_used,
                },
                subject_id=email_id
            )
        else:
            await self._emit_event(
                "ghexit.email.failed",
                {
                    "to": recipients,
                    "subject": subject,
                    "error": result.get("error", "Unknown error"),
                    "provider": provider_used,
                }
            )

        return result

    # ==================== Push Notifications ====================

    async def send_push(
        self,
        title: str,
        message: str,
        priority: int = 0,
        url: Optional[str] = None,
        url_title: Optional[str] = None,
        sound: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification via Pushover.

        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (-2 to 2)
            url: Optional URL to include
            url_title: Optional title for the URL
            sound: Optional sound to play

        Returns:
            Dict with success status and notification details
        """
        notification_id = str(uuid.uuid4())

        result = pushover_service.send_notification(
            title=title,
            message=message,
            priority=priority,
            url=url,
            url_title=url_title,
            sound=sound
        )

        if result.get("request_id"):
            notification_id = result["request_id"]

        result["provider"] = "pushover"
        result["notification_id"] = notification_id

        # Emit GEM event
        if result.get("success"):
            await self._emit_event(
                "ghexit.push.sent",
                {
                    "notificationId": notification_id,
                    "title": title,
                    "priority": priority,
                    "provider": "pushover",
                },
                subject_id=notification_id
            )

        return result

    async def send_critical_push(self, title: str, message: str) -> Dict[str, Any]:
        """Send a high-priority push notification."""
        return await self.send_push(
            title=title,
            message=message,
            priority=1,
            sound="persistent"
        )

    async def send_emergency_push(self, title: str, message: str) -> Dict[str, Any]:
        """Send an emergency push notification (requires acknowledgment)."""
        return await self.send_push(
            title=title,
            message=message,
            priority=2,
            sound="persistent"
        )

    # ==================== Smart Alerts ====================

    async def smart_alert(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        phone_number: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send smart alert based on urgency level.

        Urgency levels:
        - normal: Push notification only
        - urgent: Push + SMS
        - critical: Push + SMS + Voice call

        Args:
            title: Alert title
            message: Alert message
            urgency: "normal", "urgent", or "critical"
            phone_number: Phone number for SMS/call (required for urgent/critical)
            url: Optional URL to include in push

        Returns:
            Dict with results from each channel
        """
        results: Dict[str, Any] = {
            "urgency": urgency,
            "channels": []
        }

        if urgency == "critical":
            # Critical: Push + SMS + Call
            results["push"] = await self.send_emergency_push(title, message)
            results["channels"].append("push")

            if phone_number:
                results["sms"] = await self.send_sms(
                    to=phone_number,
                    body=f"[CRITICAL] {title}: {message}"
                )
                results["channels"].append("sms")

                results["call"] = await self.send_tts_call(
                    to=phone_number,
                    message=f"Critical alert from Jarvis. {title}. {message}"
                )
                results["channels"].append("call")

        elif urgency == "urgent":
            # Urgent: Push + SMS
            results["push"] = await self.send_critical_push(title, message)
            results["channels"].append("push")

            if phone_number:
                results["sms"] = await self.send_sms(
                    to=phone_number,
                    body=f"[URGENT] {title}: {message}"
                )
                results["channels"].append("sms")

        else:
            # Normal: Push only
            results["push"] = await self.send_push(
                title=title,
                message=message,
                url=url,
                priority=0
            )
            results["channels"].append("push")

        # Determine overall success
        results["success"] = any(
            results.get(ch, {}).get("success", False)
            for ch in ["push", "sms", "call"]
        )

        return results

    # ==================== Status & Health ====================

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all communication providers."""
        return {
            "ghexit": {
                "available": ghexit_service.is_available(),
                "discovered": bool(ghexit_service.base_url),
                "base_url": ghexit_service.base_url,
            },
            "twilio": {
                "configured": twilio_service.is_configured,
            },
            "pushover": {
                "configured": pushover_service.is_configured,
            },
            "email": {
                "gmail_available": email_service.gmail_available,
                "outlook_available": email_service.outlook_available,
            },
            "primary_sms": "ghexit" if ghexit_service.is_available() else "twilio",
            "primary_email": "ghexit" if ghexit_service.is_available() else "gmail",
        }

    def refresh_discovery(self) -> Dict[str, Any]:
        """Re-discover Ghexit from ports.json."""
        ghexit_service.refresh_discovery()
        return self.get_provider_status()


# Singleton instance
communications_hub = CommunicationsHub()
