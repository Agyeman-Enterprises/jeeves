from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)


class CommunicationsProviderError(RuntimeError):
    pass


@dataclass
class CommunicationMessage:
    id: str
    platform: str
    channel: str
    sender: str
    summary: str
    timestamp: datetime
    mentions_you: bool

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "platform": self.platform,
            "channel": self.channel,
            "sender": self.sender,
            "summary": self.summary,
            "timestamp": self.timestamp.isoformat(),
            "mentions_you": self.mentions_you,
        }


class BaseCommunicationsProvider:
    name = "communications"

    def fetch_messages(self, limit: int = 50) -> List[CommunicationMessage]:
        raise NotImplementedError

    def search_messages(self, query: str, limit: int = 50) -> List[CommunicationMessage]:
        raise NotImplementedError


class SlackProvider(BaseCommunicationsProvider):
    name = "slack"

    def __init__(
        self,
        bot_token: str,
        channel_ids: Optional[List[str]] = None,
        mention_keywords: Optional[List[str]] = None,
    ) -> None:
        self.bot_token = bot_token
        self.channel_ids = channel_ids or []
        self.mention_keywords = [kw.lower() for kw in (mention_keywords or [])]
        if not self.channel_ids:
            self.channel_ids = self._fetch_channel_ids()

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": "Bearer " + self.bot_token}

    def _fetch_channel_ids(self) -> List[str]:
        url = "https://slack.com/api/conversations.list"
        try:
            response = requests.get(url, headers=self._headers(), timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise CommunicationsProviderError(data.get("error", "Slack API error"))
            return [channel["id"] for channel in data.get("channels", [])[:10]]
        except Exception as exc:
            LOGGER.warning("Slack channel fetch failed: %s", exc)
            return []

    def fetch_messages(self, limit: int = 50) -> List[CommunicationMessage]:
        messages: List[CommunicationMessage] = []
        per_channel = max(1, limit // max(1, len(self.channel_ids)))
        for channel_id in self.channel_ids:
            url = "https://slack.com/api/conversations.history"
            params = {"channel": channel_id, "limit": per_channel}
            try:
                response = requests.get(url, headers=self._headers(), params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                if not data.get("ok"):
                    LOGGER.warning("Slack history error: %s", data.get("error"))
                    continue
                for item in data.get("messages", []):
                    ts = float(item.get("ts", 0))
                    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)
                    text = item.get("text", "")
                    messages.append(
                        CommunicationMessage(
                            id=item.get("client_msg_id") or item.get("ts", ""),
                            platform="slack",
                            channel=channel_id,
                            sender=item.get("user", "unknown"),
                            summary=text[:280],
                            timestamp=timestamp,
                            mentions_you=self._detect_mention(text),
                        )
                    )
            except Exception as exc:
                LOGGER.warning("Slack fetch failed for %s: %s", channel_id, exc)
        messages.sort(key=lambda msg: msg.timestamp, reverse=True)
        return messages[:limit]

    def search_messages(self, query: str, limit: int = 50) -> List[CommunicationMessage]:
        url = "https://slack.com/api/search.messages"
        params = {"query": query, "count": limit}
        try:
            response = requests.get(url, headers=self._headers(), params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise CommunicationsProviderError(data.get("error", "Slack search error"))
            matches = data.get("messages", {}).get("matches", [])
            results: List[CommunicationMessage] = []
            for match in matches:
                ts = float(match.get("ts", 0))
                timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)
                results.append(
                    CommunicationMessage(
                        id=match.get("iid", match.get("ts", "")),
                        platform="slack",
                        channel=match.get("channel", {}).get("name", "channel"),
                        sender=match.get("username", "unknown"),
                        summary=match.get("text", "")[:280],
                        timestamp=timestamp,
                        mentions_you=self._detect_mention(match.get("text", "")),
                    )
                )
            return results[:limit]
        except Exception as exc:
            LOGGER.warning("Slack search failed: %s", exc)
            return []

    def _detect_mention(self, text: str) -> bool:
        if not text:
            return False
        lowered = text.lower()
        if self.mention_keywords and any(keyword in lowered for keyword in self.mention_keywords):
            return True
        return "<@" in text


class WhatsAppProvider(BaseCommunicationsProvider):
    name = "whatsapp"

    def __init__(self, account_sid: str, auth_token: str, business_number: Optional[str] = None) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.business_number = business_number

    def fetch_messages(self, limit: int = 50) -> List[CommunicationMessage]:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        params = {"PageSize": limit}
        try:
            response = requests.get(
                url,
                params=params,
                auth=(self.account_sid, self.auth_token),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            messages: List[CommunicationMessage] = []
            for item in data.get("messages", []):
                date_str = item.get("date_sent") or item.get("date_created")
                timestamp = (
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    if date_str
                    else datetime.now(timezone.utc)
                )
                body = item.get("body", "")
                messages.append(
                    CommunicationMessage(
                        id=item.get("sid", ""),
                        platform="whatsapp",
                        channel=self.business_number or item.get("to", "WhatsApp"),
                        sender=item.get("from", ""),
                        summary=body[:280],
                        timestamp=timestamp,
                        mentions_you="urgent" in body.lower() or "@" in body,
                    )
                )
            messages.sort(key=lambda msg: msg.timestamp, reverse=True)
            return messages[:limit]
        except Exception as exc:
            LOGGER.warning("WhatsApp fetch failed: %s", exc)
            return []

    def search_messages(self, query: str, limit: int = 50) -> List[CommunicationMessage]:
        query_lower = query.lower()
        return [
            msg for msg in self.fetch_messages(limit=100) if query_lower in msg.summary.lower()
        ][:limit]


class CommunicationsIntegrationManager:
    """Auto-configures communications providers from environment variables."""

    def __init__(self) -> None:
        self.providers: List[BaseCommunicationsProvider] = []
        self._configure_slack()
        self._configure_whatsapp()

    def _configure_slack(self) -> None:
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        if not bot_token:
            return
        channel_ids = os.getenv("SLACK_CHANNEL_IDS")
        mention_keywords = os.getenv("SLACK_MENTION_KEYWORDS")
        provider = SlackProvider(
            bot_token=bot_token,
            channel_ids=[cid.strip() for cid in channel_ids.split(",") if cid.strip()] if channel_ids else None,
            mention_keywords=[kw.strip() for kw in mention_keywords.split(",") if kw.strip()] if mention_keywords else None,
        )
        self.providers.append(provider)

    def _configure_whatsapp(self) -> None:
        account_sid = os.getenv("WHATSAPP_TWILIO_SID")
        auth_token = os.getenv("WHATSAPP_TWILIO_TOKEN")
        business_number = os.getenv("WHATSAPP_TWILIO_NUMBER")
        if not (account_sid and auth_token):
            return
        provider = WhatsAppProvider(
            account_sid=account_sid,
            auth_token=auth_token,
            business_number=business_number,
        )
        self.providers.append(provider)

    def has_providers(self) -> bool:
        return bool(self.providers)

    def fetch_messages(self, limit: int = 50) -> List[CommunicationMessage]:
        messages: List[CommunicationMessage] = []
        for provider in self.providers:
            try:
                messages.extend(provider.fetch_messages(limit=limit))
            except CommunicationsProviderError as exc:
                LOGGER.warning("%s provider error: %s", provider.name, exc)
            except Exception as exc:
                LOGGER.warning("%s provider failed: %s", provider.name, exc)
        messages.sort(key=lambda msg: msg.timestamp, reverse=True)
        return messages[:limit]

    def search(self, query: str, limit: int = 50) -> List[CommunicationMessage]:
        results: List[CommunicationMessage] = []
        for provider in self.providers:
            try:
                results.extend(provider.search_messages(query, limit))
            except Exception as exc:
                LOGGER.warning("%s search failed: %s", provider.name, exc)
        results.sort(key=lambda msg: msg.timestamp, reverse=True)
        return results[:limit]
