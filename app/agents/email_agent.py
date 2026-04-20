from __future__ import annotations

import asyncio
import json
import logging
from collections import Counter
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

from dotenv import load_dotenv

from app.agents.base import AgentResponse, BaseAgent
from app.services.email_integrations import EmailIntegrationManager, EmailMessage
from app.services.subscription_detector import SubscriptionDetector, Subscription
from app.services.email.gmail_service import gmail_service
from app.services.email.outlook_service import outlook_service

if TYPE_CHECKING:  # pragma: no cover - typing aid
    from app.models.database_models import JarvisDatabase

LOGGER = logging.getLogger(__name__)
ENV_PATH = Path("config") / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:  # pragma: no cover - best effort fallback
    load_dotenv()

URGENT_KEYWORDS = [
    "urgent",
    "asap",
    "dea",
    "deadline",
    "action required",
    "renewal",
    "approval",
    "expiring",
]

ACTION_PATTERNS = [
    r"please\s+(?P<action>.+)",
    r"need\s+you\s+to\s+(?P<action>.+)",
    r"can\s+you\s+(?P<action>.+)",
]


class EmailAgent(BaseAgent):
    """Summarizes unread and urgent emails across providers."""

    data_path = Path("data") / "sample_emails.json"
    description = "Monitors Gmail/Outlook inboxes for unread and urgent messages."
    capabilities = [
        "Count unread emails",
        "Highlight urgent senders",
        "Summarize inbox themes",
        "Extract action items",
        "Search messages",
    ]

    def __init__(self, database: "JarvisDatabase | None" = None) -> None:
        super().__init__()
        self.database = database
        self.manager = EmailIntegrationManager()
        self.subscription_detector = SubscriptionDetector(self.manager)
        # New unified email services
        self.gmail = gmail_service
        self.outlook = outlook_service
        
        # Mailboxes and folders to scan for subscriptions
        self.subscription_mailboxes = [
            "yemaya_3a@hotmail.com",
            "isaalia@gmail.com",
            "bookadoc2u@gmail.com",
            "bookadoc2u@hotmail.com",
        ]
        self.subscription_folders = [
            "inbox",
            "archive",
            "a-recvd",
            "recvd",
            "bills",
            "purchases",
            "orders",
            "subscriptions",
            "receipts",
        ]

    async def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()
        try:
            messages = await self._load_live_messages() or self._load_sample_messages()
        except Exception as exc:
            LOGGER.error(f"Failed to load messages: {exc}", exc_info=True)
            return AgentResponse(
                agent=self.name,
                content=f"Error loading emails: {str(exc)}",
                data={"emails": []},
                status="error",
                warnings=["Email fetch failed. Check logs for details."],
            )
        
        if not messages:
            return AgentResponse(
                agent=self.name,
                content="No email integrations configured yet.",
                data={"emails": []},
                status="warning",
                warnings=["Connect Gmail/Outlook accounts in config/.env."],
            )

        if "urgent" in query_lower:
            return self._summarize_urgent(messages)
        if "action" in query_lower or "todo" in query_lower:
            return self._summarize_action_items(messages)
        if "search" in query_lower:
            return self._search_messages(query, context)
        if "count" in query_lower or "how many" in query_lower:
            return self._unread_count(messages)
        if "subscription" in query_lower and ("scan" in query_lower or "find" in query_lower):
            return self._handle_subscription_scan()

        return self._summarize_inbox(messages)

    # Summaries ----------------------------------------------------------------
    def _summarize_inbox(self, messages: List[EmailMessage]) -> AgentResponse:
        unread_count = len(messages)
        urgent = [msg for msg in messages if self._is_urgent(msg)]
        senders = Counter(msg.sender for msg in messages[:20])

        lines = [
            f"Unread emails: {unread_count}",
            f"Urgent: {len(urgent)}",
            "Top senders:",
        ]
        for sender, count in senders.most_common(3):
            lines.append(f"- {sender}: {count}")

        highlights = urgent[:3] or messages[:3]
        for message in highlights:
            timestamp = message.received.strftime("%a %I:%M %p").lstrip("0")
            urgency = "URGENT" if self._is_urgent(message) else "Unread"
            lines.append(
                f"{urgency}: {message.subject} from {message.sender} ({timestamp})"
            )

        self._persist(messages)
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"emails": [msg.to_dict() for msg in messages]},
        )

    def _summarize_urgent(self, messages: List[EmailMessage]) -> AgentResponse:
        urgent = [msg for msg in messages if self._is_urgent(msg)]
        if not urgent:
            return AgentResponse(
                agent=self.name,
                content="No urgent emails detected.",
                data={"urgent": []},
            )

        lines = ["Urgent items:"]
        for message in urgent[:5]:
            timestamp = message.received.strftime("%a %I:%M %p").lstrip("0")
            lines.append(
                f"- {message.subject} from {message.sender} ({timestamp})"
            )

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"urgent": [msg.to_dict() for msg in urgent]},
        )

    def _summarize_action_items(self, messages: List[EmailMessage]) -> AgentResponse:
        items = self._extract_action_items(messages)
        if not items:
            return AgentResponse(
                agent=self.name,
                content="No action items detected in recent emails.",
                data={"action_items": []},
            )
        lines = ["Action items:"]
        for item in items[:5]:
            lines.append(f"- {item}")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"action_items": items},
        )

    def _unread_count(self, messages: List[EmailMessage]) -> AgentResponse:
        return AgentResponse(
            agent=self.name,
            content=f"You have {len(messages)} unread emails.",
            data={"count": len(messages)},
        )

    def _search_messages(
        self, query: str, context: Dict[str, str] | None
    ) -> AgentResponse:
        search_term = context.get("search") if context else None
        if not search_term:
            # attempt to extract term from query text
            search_term = query.split("search", 1)[-1].strip()
        if not search_term:
            return AgentResponse(
                agent=self.name,
                content="Provide a search term, e.g. 'Search emails for DEA renewals'.",
                status="warning",
                data={"results": []},
            )
        results: List[EmailMessage] = []
        
        # Search new services using a single event loop
        import asyncio
        
        async def search_async():
            nonlocal results
            # Search Gmail
            if self.gmail.is_authorized():
                try:
                    gmail_result = await self.gmail.search(search_term, max_results=20)
                    if gmail_result.get("success"):
                        for msg_data in gmail_result.get("messages", [])[:10]:
                            msg_detail = await self.gmail.get_message(msg_data["id"])
                            if msg_detail.get("success"):
                                msg = msg_detail["message"]
                                payload = msg.get("payload", {})
                                headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
                                results.append(
                                    EmailMessage(
                                        subject=headers.get("Subject", ""),
                                        sender=headers.get("From", ""),
                                        received=datetime.now(timezone.utc),
                                        snippet=msg.get("snippet", ""),
                                        account="gmail",
                                        provider="gmail",
                                        id=msg["id"],
                                    )
                                )
                except Exception as exc:
                    LOGGER.warning("Gmail search failed: %s", exc)
            
            # Search Outlook
            if self.outlook.is_authorized():
                try:
                    outlook_result = await self.outlook.search(search_term, top=20)
                    if outlook_result.get("success"):
                        for msg_data in outlook_result.get("messages", [])[:10]:
                            msg_detail = await self.outlook.get_message(msg_data["id"])
                            if msg_detail.get("success"):
                                msg = msg_detail["message"]
                                from_addr = msg.get("from", {}).get("emailAddress", {})
                                results.append(
                                    EmailMessage(
                                        subject=msg.get("subject", ""),
                                        sender=from_addr.get("address", ""),
                                        received=datetime.now(timezone.utc),
                                        snippet=msg.get("bodyPreview", ""),
                                        account="outlook",
                                        provider="outlook",
                                        id=msg["id"],
                                    )
                                )
                except Exception as exc:
                    LOGGER.warning("Outlook search failed: %s", exc)
        
        # Execute async search using a single event loop
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, search_async())
                        future.result()
                else:
                    loop.run_until_complete(search_async())
            except RuntimeError:
                asyncio.run(search_async())
        except Exception as exc:
            LOGGER.warning("Async search execution failed: %s", exc)
        
        # Fallback to legacy manager
        if not results and self.manager.has_providers():
            results = self.manager.search(search_term, max_results=10)
        elif not results:
            messages = self._load_sample_messages()
            results = [
                msg
                for msg in messages
                if search_term.lower() in (msg.subject + msg.snippet).lower()
            ]
        lines = [f"Search results for '{search_term}':"]
        for message in results[:5]:
            timestamp = message.received.strftime("%b %d %I:%M %p").lstrip("0")
            lines.append(f"- {message.subject} ({timestamp}) from {message.sender}")
        return AgentResponse(
            agent=self.name,
            content="\n".join(lines) if results else "No matching emails found.",
            data={"results": [msg.to_dict() for msg in results]},
        )

    # Helpers ------------------------------------------------------------------
    async def _fetch_gmail_messages(self) -> List[EmailMessage]:
        """Fetch messages from Gmail service."""
        messages: List[EmailMessage] = []
        if not self.gmail.is_authorized():
            return messages
        
        try:
            result = await self.gmail.get_unread_summary()
            if result.get("success"):
                summary = result.get("summary", {})
                for msg_data in summary.get("messages", []):
                    messages.append(
                        EmailMessage(
                            subject=msg_data.get("subject", ""),
                            sender=msg_data.get("from", ""),
                            received=datetime.now(timezone.utc),
                            snippet=msg_data.get("snippet", ""),
                            account="gmail",
                            provider="gmail",
                            id=msg_data.get("id", ""),
                        )
                    )
        except Exception as exc:
            LOGGER.warning("Failed to load from Gmail service: %s", exc)
        
        return messages

    async def _fetch_outlook_messages(self) -> List[EmailMessage]:
        """Fetch messages from Outlook service."""
        messages: List[EmailMessage] = []
        if not self.outlook.is_authorized():
            return messages
        
        try:
            result = await self.outlook.get_unread_summary()
            if result.get("success"):
                summary = result.get("summary", {})
                for msg_data in summary.get("messages", []):
                    messages.append(
                        EmailMessage(
                            subject=msg_data.get("subject", ""),
                            sender=msg_data.get("from", ""),
                            received=datetime.now(timezone.utc),
                            snippet=msg_data.get("snippet", ""),
                            account="outlook",
                            provider="outlook",
                            id=msg_data.get("id", ""),
                        )
                    )
        except Exception as exc:
            LOGGER.warning("Failed to load from Outlook service: %s", exc)
        
        return messages

    async def _load_live_messages_async(self) -> List[EmailMessage]:
        """Load messages from both new services concurrently and legacy manager (async version)."""
        # Fetch from Gmail and Outlook concurrently
        gmail_messages, outlook_messages = await asyncio.gather(
            self._fetch_gmail_messages(),
            self._fetch_outlook_messages(),
            return_exceptions=True
        )
        
        messages: List[EmailMessage] = []
        
        # Handle Gmail results
        if isinstance(gmail_messages, list):
            messages.extend(gmail_messages)
        elif isinstance(gmail_messages, Exception):
            LOGGER.warning("Gmail fetch raised exception: %s", gmail_messages)
        
        # Handle Outlook results
        if isinstance(outlook_messages, list):
            messages.extend(outlook_messages)
        elif isinstance(outlook_messages, Exception):
            LOGGER.warning("Outlook fetch raised exception: %s", outlook_messages)
        
        # Fallback to legacy manager (synchronous, so we can't await it)
        if not messages and self.manager.has_providers():
            messages = self.manager.fetch_unread(max_results=50)
        
        return messages

    def _load_live_messages(self) -> List[EmailMessage]:
        """Load messages from both new services and legacy manager (synchronous wrapper using single event loop)."""
        import asyncio
        try:
            # Use a single event loop for all async operations
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, use a thread with a new event loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._load_live_messages_async())
                        return future.result()
                else:
                    return loop.run_until_complete(self._load_live_messages_async())
            except RuntimeError:
                # No event loop exists, create a new one
                return asyncio.run(self._load_live_messages_async())
        except Exception as exc:
            LOGGER.warning("Failed to load live messages: %s", exc)
            return []

    def _load_sample_messages(self) -> List[EmailMessage]:
        if not self.data_path.exists():
            LOGGER.info("Sample email data not found at %s", self.data_path)
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

        messages: List[EmailMessage] = []
        for entry in data:
            try:
                received = datetime.fromisoformat(entry["received"])
                if received.tzinfo is None:
                    received = received.replace(tzinfo=timezone.utc)
                messages.append(
                    EmailMessage(
                        subject=entry["subject"],
                        sender=entry["sender"],
                        received=received,
                        snippet=entry.get("snippet", ""),
                        account=entry.get("account", entry["sender"]),
                        provider=entry.get("provider", "sample"),
                        id=entry.get("id", entry["subject"]),
                    )
                )
            except Exception as exc:
                LOGGER.debug("Skipping malformed email entry: %s", exc)
        return messages

    def _is_urgent(self, message: EmailMessage) -> bool:
        text = f"{message.subject} {message.snippet}".lower()
        return any(keyword in text for keyword in URGENT_KEYWORDS)

    def _extract_action_items(self, messages: List[EmailMessage]) -> List[str]:
        items: List[str] = []
        for message in messages:
            text = f"{message.subject}. {message.snippet}"
            for pattern in ACTION_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    action = match.group("action").strip().rstrip(".")
                    items.append(f"{message.sender}: {action}")
                    break
        return items

    def _persist(self, messages: List[EmailMessage]) -> None:
        if not self.database or not messages:
            return
        payloads = [msg.to_dict() for msg in messages[:50]]
        try:
            self.database.save_email_summaries(payloads)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to persist email summaries: %s", exc)

    # Subscription scanning -----------------------------------------------------
    def extract_subscription_emails(self) -> List[Dict[str, Any]]:
        """
        Scan all configured email accounts + relevant folders for subscription/billing emails.
        Returns normalized records with:
        - source_email
        - folder
        - merchant
        - amount
        - currency
        - billing_date
        - raw_subject
        - raw_snippet
        """
        if not self.manager.has_providers():
            LOGGER.warning("No email providers configured for subscription scanning")
            return []

        # Use SubscriptionDetector to find subscriptions
        subscriptions = self.subscription_detector.detect_subscriptions_from_emails(
            email_accounts=self.subscription_mailboxes,
            folders=self.subscription_folders,
            days_back=365,  # Scan last year
        )

        # Normalize to the requested format
        records: List[Dict[str, Any]] = []
        for sub in subscriptions:
            records.append(
                {
                    "source_email": sub.email_account,
                    "folder": "unknown",  # Email providers don't expose folder in current implementation
                    "merchant": sub.merchant or sub.name,
                    "amount": sub.amount,
                    "currency": "USD",  # Default, could be extracted from email
                    "billing_date": sub.receipt_date.isoformat() if sub.receipt_date else None,
                    "next_billing": sub.next_billing.isoformat() if sub.next_billing else None,
                    "frequency": sub.frequency,
                    "category": sub.category,
                    "flagged_for_review": sub.flagged_for_review,
                    "raw_subject": sub.name,  # Using name as proxy for subject
                    "raw_snippet": "",  # Not stored in Subscription model
                }
            )

        return records

    def save_subscription_snapshot(self, path: Path) -> None:
        """Save subscription email scan results to JSON file."""
        records = self.extract_subscription_emails()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)
            LOGGER.info("Saved %d subscription records to %s", len(records), path)
        except Exception as exc:
            LOGGER.error("Failed to save subscription snapshot: %s", exc)

    def _handle_subscription_scan(self) -> AgentResponse:
        """Handle subscription scanning request."""
        snapshot_path = Path("data/finance/subscriptions/email_subscriptions.json")
        self.save_subscription_snapshot(snapshot_path)

        records = self.extract_subscription_emails()
        if not records:
            return AgentResponse(
                agent=self.name,
                content="No subscription emails found. Checked mailboxes and folders for billing/receipt emails.",
                data={"subscriptions": []},
                status="warning",
            )

        lines = [f"Found {len(records)} subscription records:"]
        for record in records[:10]:  # Show first 10
            merchant = record.get("merchant", "Unknown")
            amount = record.get("amount")
            amount_str = f"${amount:,.2f}" if amount else "Unknown"
            lines.append(f"  {merchant}: {amount_str} ({record.get('frequency', 'unknown')})")

        if len(records) > 10:
            lines.append(f"  ... and {len(records) - 10} more")

        lines.append(f"\nSaved to: {snapshot_path}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"subscriptions": records, "count": len(records)},
            status="success",
        )
