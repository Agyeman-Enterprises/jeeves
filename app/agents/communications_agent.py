from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent
from app.services.communications_integrations import (
    CommunicationMessage,
    CommunicationsIntegrationManager,
)
from app.services.communications import communications_hub

LOGGER = logging.getLogger(__name__)


class CommunicationsAgent(BaseAgent):
    """Summarizes Slack and WhatsApp updates."""

    data_path = Path("data") / "sample_communications.json"
    description = "Monitors Slack/WhatsApp for mentions, DMs, and action items."
    capabilities = [
        "Highlight mentions",
        "Summarize channel chatter",
        "Surface action items",
        "Track unread DMs",
        "Search communications",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.manager = CommunicationsIntegrationManager()
        self._sample_messages = self._load_sample_data()
        # Unified communications hub (Ghexit → Twilio/Pushover fallback)
        self.hub = communications_hub

    def handle(
        self,
        query: str,
        context: Dict[str, str] | None = None,
    ) -> AgentResponse:
        query_lower = query.lower()
        messages = self._load_live_messages() or self._sample_messages
        if not messages:
            return AgentResponse(
                agent=self.name,
                content="No communications integrations configured yet.",
                data={"messages": []},
                status="warning",
                warnings=["Connect Slack/WhatsApp to enable live communications summaries."],
            )

        if "search" in query_lower:
            search_term = context.get("search") if context else None
            if not search_term:
                parts = query.split("search", 1)
                if len(parts) > 1:
                    search_term = parts[1].strip() or None
            return self._handle_search(search_term or "all", messages)

        if "mention" in query_lower:
            return self._handle_mentions(messages)

        if "action" in query_lower or "todo" in query_lower:
            return self._handle_action_items(messages)

        if "urgent" in query_lower:
            urgent = [msg for msg in messages if self._is_urgent(msg)]
            return self._summarize(urgent or messages, title="Urgent updates")

        return self._summarize(messages)

    # Summaries ----------------------------------------------------------------
    def _summarize(self, messages: List[CommunicationMessage], title: str = "Latest communications") -> AgentResponse:
        mentions = [msg for msg in messages if msg.mentions_you]
        by_platform = Counter(msg.platform for msg in messages)
        lines = [title, f"Total messages: {len(messages)}"]
        for platform, count in by_platform.items():
            lines.append(f"- {platform}: {count}")
        highlight = mentions[:3] or messages[:3]
        for msg in highlight:
            timestamp = msg.timestamp.strftime("%a %I:%M %p").lstrip("0")
            prefix = "MENTION" if msg.mentions_you else msg.platform.upper()
            lines.append(f"{prefix} | {msg.channel} - {msg.sender}: {msg.summary} ({timestamp})")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={
                "messages": [msg.to_dict() for msg in messages],
                "mentions": [msg.to_dict() for msg in mentions],
            },
        )

    def _handle_mentions(self, messages: List[CommunicationMessage]) -> AgentResponse:
        mentions = [msg for msg in messages if msg.mentions_you]
        if not mentions:
            return AgentResponse(
                agent=self.name,
                content="No new mentions detected.",
                data={"mentions": []},
            )
        return self._summarize(mentions, title="Mentions")

    def _handle_action_items(self, messages: List[CommunicationMessage]) -> AgentResponse:
        items = []
        for msg in messages:
            text = msg.summary.lower()
            if "need" in text and "you" in text:
                items.append(msg)
            elif "please" in text and any(word in text for word in ["review", "approve", "send"]):
                items.append(msg)
            elif "action" in text or "todo" in text:
                items.append(msg)
        if not items:
            return AgentResponse(
                agent=self.name,
                content="No action items detected in recent communications.",
                data={"action_items": []},
            )
        lines = ["Action items:"]
        for msg in items[:5]:
            timestamp = msg.timestamp.strftime("%a %I:%M %p").lstrip("0")
            lines.append(f"- {msg.summary} ({msg.sender} in {msg.channel} at {timestamp})")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"action_items": [msg.to_dict() for msg in items]},
        )

    def _handle_search(self, term: str, fallback_messages: List[CommunicationMessage]) -> AgentResponse:
        if self.manager.has_providers():
            results = self.manager.search(term, limit=20)
        else:
            results = [
                msg
                for msg in fallback_messages
                if term.lower() in (msg.summary.lower() + msg.sender.lower())
            ]
        if not results:
            return AgentResponse(
                agent=self.name,
                content=f"No communications found for '{term}'.",
                data={"results": []},
            )
        lines = [f"Search results for '{term}':"]
        for msg in results[:5]:
            timestamp = msg.timestamp.strftime("%b %d %I:%M %p").lstrip("0")
            lines.append(f"- {msg.platform} {msg.channel} | {msg.sender}: {msg.summary} ({timestamp})")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"results": [msg.to_dict() for msg in results]},
        )

    # Helpers ------------------------------------------------------------------
    def _load_live_messages(self) -> List[CommunicationMessage]:
        if not self.manager.has_providers():
            return []
        try:
            return self.manager.fetch_messages(limit=50)
        except Exception as exc:
            LOGGER.warning("Communications integrations failed: %s", exc)
            return []

    def _load_sample_data(self) -> List[CommunicationMessage]:
        if not self.data_path.exists():
            LOGGER.info("Sample communications data not found at %s", self.data_path)
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []
        messages: List[CommunicationMessage] = []
        for entry in data:
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                messages.append(
                    CommunicationMessage(
                        id=entry.get("id", entry["timestamp"]),
                        platform=entry.get("platform", "sample"),
                        channel=entry.get("channel", ""),
                        sender=entry.get("sender", ""),
                        summary=entry.get("summary", ""),
                        timestamp=timestamp,
                        mentions_you=bool(entry.get("mentions_you", False)),
                    )
                )
            except Exception as exc:
                LOGGER.debug("Skipping malformed communications entry: %s", exc)
        messages.sort(key=lambda msg: msg.timestamp, reverse=True)
        return messages

    @staticmethod
    def _is_urgent(message: CommunicationMessage) -> bool:
        text = message.summary.lower()
        return any(keyword in text for keyword in ["urgent", "asap", "dea", "deadline"])

    # Notification methods (via CommunicationsHub) --------------------------------
    async def send_sms(self, to: str, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Send SMS via CommunicationsHub (Ghexit → Twilio fallback)."""
        result = await self.hub.send_sms(to=to, body=message)
        if result.get("success"):
            return AgentResponse(
                agent=self.name,
                content=f"SMS sent to {to} via {result.get('provider', 'unknown')}",
                data=result,
            )
        return AgentResponse(
            agent=self.name,
            content=f"Failed to send SMS: {result.get('error', 'Unknown error')}",
            data=result,
            status="error",
        )

    async def send_whatsapp(self, to: str, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Send WhatsApp message via CommunicationsHub."""
        result = await self.hub.send_whatsapp(to=to, body=message)
        if result.get("success"):
            return AgentResponse(
                agent=self.name,
                content=f"WhatsApp message sent to {to}",
                data=result,
            )
        return AgentResponse(
            agent=self.name,
            content=f"Failed to send WhatsApp: {result.get('error', 'Unknown error')}",
            data=result,
            status="error",
        )

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Send email via CommunicationsHub (Ghexit/Resend → Gmail fallback)."""
        result = await self.hub.send_email(to=to, subject=subject, body=body, html=html)
        if result.get("success"):
            return AgentResponse(
                agent=self.name,
                content=f"Email sent to {to} via {result.get('provider', 'unknown')}",
                data=result,
            )
        return AgentResponse(
            agent=self.name,
            content=f"Failed to send email: {result.get('error', 'Unknown error')}",
            data=result,
            status="error",
        )

    async def call_with_message(self, to: str, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Make a voice call with TTS message via CommunicationsHub."""
        result = await self.hub.send_tts_call(to=to, message=message)
        if result.get("success"):
            return AgentResponse(
                agent=self.name,
                content=f"Call initiated to {to} via {result.get('provider', 'unknown')}",
                data=result,
            )
        return AgentResponse(
            agent=self.name,
            content=f"Failed to make call: {result.get('error', 'Unknown error')}",
            data=result,
            status="error",
        )

    async def push_notification(
        self, title: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Send push notification via CommunicationsHub (Pushover)."""
        priority = context.get("priority", 0) if context else 0
        url = context.get("url") if context else None
        url_title = context.get("url_title") if context else None

        result = await self.hub.send_push(
            title=title, message=message, priority=priority, url=url, url_title=url_title
        )
        if result.get("success"):
            return AgentResponse(
                agent=self.name,
                content=f"Push notification sent: {title}",
                data=result,
            )
        return AgentResponse(
            agent=self.name,
            content=f"Failed to send push: {result.get('error', 'Unknown error')}",
            data=result,
            status="error",
        )

    async def smart_alert(self, alert_type: str, payload: Dict[str, Any]) -> AgentResponse:
        """
        Send smart alert based on type and urgency via CommunicationsHub.

        Alert types:
        - calendar_upcoming_appointment
        - finance_anomaly
        - email_important
        - lab_result_available
        - travel_change
        """
        title = payload.get("title", "Jarvis Alert")
        message = payload.get("message", "")
        urgency = payload.get("urgency", "normal")  # normal, urgent, critical
        phone_number = payload.get("phone_number")
        url = payload.get("url")

        # Use CommunicationsHub's smart_alert which handles all channels
        results = await self.hub.smart_alert(
            title=title,
            message=message,
            urgency=urgency,
            phone_number=phone_number,
            url=url
        )

        return AgentResponse(
            agent=self.name,
            content=f"Alert sent via {len(results.get('channels', []))} channel(s): {', '.join(results.get('channels', []))}",
            data={"alert_type": alert_type, "results": results},
        )

    async def handle_communication_request(self, intent: str, data: Dict[str, Any]) -> AgentResponse:
        """
        Handle communication requests from other agents.

        Intents:
        - send_update: Send a normal update (push)
        - send_alert: Send an alert (uses smart_alert)
        - notify_user: Send push notification
        - call_user: Make a voice call
        - send_sms: Send SMS
        - send_email: Send email
        """
        if intent == "send_update":
            return await self.push_notification(
                title=data.get("title", "Update"),
                message=data.get("message", ""),
                context=data.get("context"),
            )
        elif intent == "send_alert":
            return await self.smart_alert(
                alert_type=data.get("alert_type", "general"),
                payload=data.get("payload", {}),
            )
        elif intent == "notify_user":
            return await self.push_notification(
                title=data.get("title", "Notification"),
                message=data.get("message", ""),
                context=data.get("context"),
            )
        elif intent == "call_user":
            return await self.call_with_message(
                to=data.get("to", ""),
                message=data.get("message", ""),
                context=data.get("context"),
            )
        elif intent == "send_sms":
            return await self.send_sms(
                to=data.get("to", ""),
                message=data.get("message", ""),
                context=data.get("context"),
            )
        elif intent == "send_email":
            return await self.send_email(
                to=data.get("to", ""),
                subject=data.get("subject", ""),
                body=data.get("body", data.get("message", "")),
                html=data.get("html"),
                context=data.get("context"),
            )
        else:
            return AgentResponse(
                agent=self.name,
                content=f"Unknown intent: {intent}",
                status="error",
            )

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all communication providers."""
        return self.hub.get_provider_status()

    # Handler methods for query parsing
    def _handle_send_sms(self, query: str, context: Optional[Dict[str, str]]) -> AgentResponse:
        """Parse query for SMS sending."""
        # Extract phone number and message from query
        # Simple parsing - can be enhanced
        parts = query.lower().split("text") or query.lower().split("sms")
        if len(parts) > 1:
            message_part = parts[1].strip()
            # Try to extract phone number (simplified)
            # In production, use NLP or structured input
            return AgentResponse(
                agent=self.name,
                content="SMS sending requires phone number and message. Use API endpoint or structured format.",
                status="warning",
            )
        return AgentResponse(
            agent=self.name,
            content="Please provide phone number and message for SMS.",
            status="warning",
        )

    def _handle_send_whatsapp(self, query: str, context: Optional[Dict[str, str]]) -> AgentResponse:
        """Parse query for WhatsApp sending."""
        return AgentResponse(
            agent=self.name,
            content="WhatsApp sending requires phone number and message. Use API endpoint or structured format.",
            status="warning",
        )

    def _handle_call(self, query: str, context: Optional[Dict[str, str]]) -> AgentResponse:
        """Parse query for voice call."""
        return AgentResponse(
            agent=self.name,
            content="Call requires phone number and message. Use API endpoint or structured format.",
            status="warning",
        )

    def _handle_push_notification(self, query: str, context: Optional[Dict[str, str]]) -> AgentResponse:
        """Parse query for push notification."""
        return AgentResponse(
            agent=self.name,
            content="Push notification requires title and message. Use API endpoint or structured format.",
            status="warning",
        )

    def _handle_alert(self, query: str, context: Optional[Dict[str, str]]) -> AgentResponse:
        """Parse query for alert."""
        return AgentResponse(
            agent=self.name,
            content="Alert requires alert type and payload. Use API endpoint or structured format.",
            status="warning",
        )
