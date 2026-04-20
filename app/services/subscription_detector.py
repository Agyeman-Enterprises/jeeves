from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.services.email_integrations import EmailIntegrationManager, EmailMessage

LOGGER = logging.getLogger(__name__)

# Common subscription keywords
SUBSCRIPTION_KEYWORDS = [
    "subscription",
    "renewal",
    "recurring",
    "monthly",
    "annual",
    "yearly",
    "billing",
    "invoice",
    "receipt",
    "payment",
    "charge",
    "auto-renew",
    "auto-renewal",
    "renew",
    "membership",
    "premium",
    "pro",
    "trial",
    "expires",
]

# AI/tech subscription patterns
AI_SUBSCRIPTION_PATTERNS = [
    r"openai",
    r"anthropic",
    r"claude",
    r"chatgpt",
    r"midjourney",
    r"stability",
    r"replicate",
    r"huggingface",
    r"cohere",
    r"perplexity",
    r"notion ai",
    r"grammarly",
    r"copilot",
    r"cursor",
    r"github copilot",
    r"jetbrains",
    r"adobe",
    r"figma",
    r"canva",
]

# Education/arts/crafts subscription patterns
EDUCATION_PATTERNS = [
    r"skillshare",
    r"udemy",
    r"coursera",
    r"masterclass",
    r"creative live",
    r"domestika",
    r"craftsy",
    r"bluprint",
    r"artstation",
    r"procreate",
]


@dataclass
class Subscription:
    name: str
    email_account: str
    amount: Optional[float] = None
    frequency: Optional[str] = None  # monthly, annual, etc.
    next_billing: Optional[datetime] = None
    category: Optional[str] = None  # ai, education, software, etc.
    status: str = "active"  # active, cancelled, expired
    receipt_date: Optional[datetime] = None
    merchant: Optional[str] = None
    flagged_for_review: bool = False

    def to_dict(self) -> Dict[str, any]:
        return {
            "name": self.name,
            "email_account": self.email_account,
            "amount": self.amount,
            "frequency": self.frequency,
            "next_billing": self.next_billing.isoformat() if self.next_billing else None,
            "category": self.category,
            "status": self.status,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "merchant": self.merchant,
            "flagged_for_review": self.flagged_for_review,
        }


class SubscriptionDetector:
    """Detects subscriptions from email receipts and invoices."""

    def __init__(self, email_manager: Optional[EmailIntegrationManager] = None) -> None:
        self.email_manager = email_manager or EmailIntegrationManager()

    def detect_subscriptions_from_emails(
        self,
        email_accounts: Optional[List[str]] = None,
        folders: Optional[List[str]] = None,
        days_back: int = 90,
    ) -> List[Subscription]:
        """
        Scan emails for subscription receipts and invoices.

        Args:
            email_accounts: List of email addresses to scan (None = all configured)
            folders: List of folders to check (e.g., ['a-recvd', 'archive', 'recvd', 'bills'])
            days_back: How many days back to search
        """
        subscriptions: List[Subscription] = []

        if not self.email_manager.has_providers():
            LOGGER.warning("No email providers configured for subscription detection")
            return subscriptions

        # Default folders to check
        if not folders:
            folders = ["a-recvd", "archive", "recvd", "bills", "inbox"]

        # Search for subscription-related emails
        search_queries = [
            "subscription",
            "renewal",
            "billing",
            "invoice",
            "receipt",
            "payment confirmation",
            "auto-renew",
        ]

        for query in search_queries:
            try:
                messages = self.email_manager.search(query, max_results=50)
                for msg in messages:
                    # Filter by email account if specified
                    if email_accounts and msg.account not in email_accounts:
                        continue

                    # Check if message is recent enough
                    if msg.received < datetime.now(msg.received.tzinfo) - timedelta(days=days_back):
                        continue

                    detected = self._parse_subscription_from_email(msg)
                    if detected:
                        subscriptions.append(detected)
            except Exception as exc:
                LOGGER.warning("Error searching for subscriptions: %s", exc)

        # Deduplicate subscriptions
        return self._deduplicate_subscriptions(subscriptions)

    def _parse_subscription_from_email(self, email: EmailMessage) -> Optional[Subscription]:
        """Extract subscription information from an email message."""
        subject_lower = email.subject.lower()
        snippet_lower = email.snippet.lower()
        combined_text = f"{subject_lower} {snippet_lower}"

        # Check if this looks like a subscription email
        if not any(keyword in combined_text for keyword in SUBSCRIPTION_KEYWORDS):
            return None

        # Extract subscription name (usually in subject or from merchant)
        name = self._extract_subscription_name(email.subject, email.snippet)

        # Determine category
        category = self._categorize_subscription(combined_text)

        # Extract amount
        amount = self._extract_amount(combined_text)

        # Extract frequency
        frequency = self._extract_frequency(combined_text)

        # Extract next billing date
        next_billing = self._extract_next_billing_date(combined_text)

        # Flag AI subscriptions for review
        flagged = category == "ai"

        return Subscription(
            name=name,
            email_account=email.account,
            amount=amount,
            frequency=frequency,
            next_billing=next_billing,
            category=category,
            receipt_date=email.received,
            merchant=email.sender,
            flagged_for_review=flagged,
        )

    def _extract_subscription_name(self, subject: str, snippet: str) -> str:
        """Extract the subscription service name."""
        # Try to extract from subject first
        # Common patterns: "Your [Service] subscription", "[Service] - Invoice", etc.
        patterns = [
            r"your\s+([a-z\s]+?)\s+subscription",
            r"([a-z\s]+?)\s+-\s+(?:invoice|receipt|billing)",
            r"([a-z\s]+?)\s+subscription",
        ]

        for pattern in patterns:
            match = re.search(pattern, subject.lower())
            if match:
                return match.group(1).strip().title()

        # Fallback: use sender domain or first part of subject
        if "@" in subject:
            domain = subject.split("@")[-1].split()[0]
            return domain.replace(".com", "").replace(".co", "").title()

        return subject.split("-")[0].split(":")[0].strip()[:50]

    def _categorize_subscription(self, text: str) -> Optional[str]:
        """Categorize subscription based on content."""
        text_lower = text.lower()

        # Check for AI subscriptions
        for pattern in AI_SUBSCRIPTION_PATTERNS:
            if re.search(pattern, text_lower):
                return "ai"

        # Check for education/arts/crafts
        for pattern in EDUCATION_PATTERNS:
            if re.search(pattern, text_lower):
                return "education"

        # Check for software
        if any(kw in text_lower for kw in ["software", "app", "tool", "platform"]):
            return "software"

        # Check for streaming
        if any(kw in text_lower for kw in ["netflix", "spotify", "hulu", "disney", "prime"]):
            return "streaming"

        return "other"

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract subscription amount from text."""
        # Look for patterns like $29.99, $29.99/month, etc.
        patterns = [
            r"\$(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*usd",
            r"amount[:\s]+\$?(\d+\.?\d*)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    return float(matches[-1])  # Take the last match (usually the total)
                except ValueError:
                    continue

        return None

    def _extract_frequency(self, text: str) -> Optional[str]:
        """Extract billing frequency."""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["monthly", "per month", "/month", "every month"]):
            return "monthly"
        elif any(kw in text_lower for kw in ["annual", "yearly", "per year", "/year"]):
            return "annual"
        elif any(kw in text_lower for kw in ["quarterly", "per quarter"]):
            return "quarterly"
        elif any(kw in text_lower for kw in ["weekly", "per week"]):
            return "weekly"

        return None

    def _extract_next_billing_date(self, text: str) -> Optional[datetime]:
        """Extract next billing/renewal date."""
        # Look for patterns like "renews on 2025-04-15", "next billing: 4/15/2025", etc.
        patterns = [
            r"renew[s]?\s+on\s+(\d{4}-\d{2}-\d{2})",
            r"next\s+billing[:\s]+(\d{1,2}/\d{1,2}/\d{4})",
            r"renew[s]?\s+(\d{1,2}/\d{1,2}/\d{4})",
            r"billing\s+date[:\s]+(\d{1,2}/\d{1,2}/\d{4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                date_str = match.group(1)
                try:
                    if "-" in date_str:
                        return datetime.strptime(date_str, "%Y-%m-%d")
                    else:
                        return datetime.strptime(date_str, "%m/%d/%Y")
                except ValueError:
                    continue

        return None

    def _deduplicate_subscriptions(self, subscriptions: List[Subscription]) -> List[Subscription]:
        """Remove duplicate subscriptions based on name and email account."""
        seen = set()
        unique = []

        for sub in subscriptions:
            key = (sub.name.lower(), sub.email_account)
            if key not in seen:
                seen.add(key)
                unique.append(sub)

        return unique

