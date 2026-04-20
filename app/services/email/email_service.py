"""
Unified email service that combines Gmail and Outlook providers.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from dotenv import load_dotenv

from app.services.email.gmail_provider import GmailProvider
from app.services.email.models import EmailMessage
from app.services.email.outlook_provider import OutlookProvider

load_dotenv()

LOGGER = logging.getLogger(__name__)

PRIMARY_EMAIL_ADDRESSES = [
    addr.strip()
    for addr in os.getenv("PRIMARY_EMAIL_ADDRESSES", "").split(",")
    if addr.strip()
]


class EmailService:
    """Unified email service for Gmail and Outlook."""

    def __init__(self) -> None:
        self.gmail = GmailProvider()
        self.outlook = OutlookProvider()
        self.primary_accounts = PRIMARY_EMAIL_ADDRESSES

    def fetch_recent(self, limit: int = 50) -> List[EmailMessage]:
        """Fetch recent emails from all providers, merge and sort by date."""
        all_messages = []

        # Fetch from Gmail
        try:
            gmail_messages = self.gmail.list_messages(max_results=limit)
            all_messages.extend(gmail_messages)
        except Exception as exc:
            LOGGER.warning("Failed to fetch Gmail messages: %s", exc)

        # Fetch from Outlook (for each primary account)
        for account in self.primary_accounts:
            if "@outlook.com" in account.lower() or "@hotmail.com" in account.lower():
                try:
                    outlook_messages = self.outlook.list_messages(account=account, top=limit)
                    all_messages.extend(outlook_messages)
                except Exception as exc:
                    LOGGER.warning("Failed to fetch Outlook messages for %s: %s", account, exc)

        # Sort by date descending
        all_messages.sort(key=lambda m: m.date, reverse=True)

        # Return top N
        return all_messages[:limit]

    def search(self, query: str, limit: int = 50) -> List[EmailMessage]:
        """Search across all providers and merge results."""
        all_messages = []

        # Search Gmail
        try:
            gmail_messages = self.gmail.search(query, max_results=limit)
            all_messages.extend(gmail_messages)
        except Exception as exc:
            LOGGER.warning("Failed to search Gmail: %s", exc)

        # Search Outlook
        for account in self.primary_accounts:
            if "@outlook.com" in account.lower() or "@hotmail.com" in account.lower():
                try:
                    outlook_messages = self.outlook.search(account=account, query=query, top=limit)
                    all_messages.extend(outlook_messages)
                except Exception as exc:
                    LOGGER.warning("Failed to search Outlook for %s: %s", account, exc)

        # Sort by date descending
        all_messages.sort(key=lambda m: m.date, reverse=True)

        return all_messages[:limit]

    def get_message(self, provider: str, account: str, message_id: str) -> Optional[EmailMessage]:
        """Get a specific message by provider, account, and ID."""
        if provider == "gmail":
            return self.gmail.get_message(message_id)
        elif provider == "outlook":
            return self.outlook.get_message(account, message_id)
        else:
            LOGGER.warning("Unknown provider: %s", provider)
            return None

    def send(
        self,
        from_addr: str,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> str:
        """Send email, routing to appropriate provider based on from_addr."""
        if "@gmail.com" in from_addr.lower():
            return self.gmail.send_message(from_addr, to, subject, body_text, body_html)
        elif "@outlook.com" in from_addr.lower() or "@hotmail.com" in from_addr.lower():
            return self.outlook.send_message(from_addr, to, subject, body_text, body_html)
        else:
            # Default to Gmail if can't determine
            LOGGER.warning("Could not determine provider for %s, defaulting to Gmail", from_addr)
            return self.gmail.send_message(from_addr, to, subject, body_text, body_html)


# Singleton instance
email_service = EmailService()

