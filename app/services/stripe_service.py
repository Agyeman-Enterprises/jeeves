from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

try:
    import stripe
except ImportError:
    stripe = None

LOGGER = logging.getLogger(__name__)


class StripeService:
    """
    Read-only Stripe integration for revenue tracking across businesses.
    """

    def __init__(self) -> None:
        api_key = os.getenv("STRIPE_API_KEY")
        if not api_key:
            LOGGER.warning("STRIPE_API_KEY not set; StripeService disabled.")
            self.enabled = False
            return

        if not stripe:
            LOGGER.warning("stripe library not installed. Install with: pip install stripe")
            self.enabled = False
            return

        stripe.api_key = api_key
        self.enabled = True

    def is_enabled(self) -> bool:
        return self.enabled

    def fetch_recent_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []

        try:
            charges = stripe.Charge.list(limit=limit)
            normalized: List[Dict[str, Any]] = []

            for ch in charges.auto_paging_iter():
                normalized.append(
                    {
                        "id": ch.id,
                        "amount": ch.amount / 100.0,
                        "currency": ch.currency,
                        "created": ch.created,
                        "description": ch.description,
                        "paid": ch.paid,
                        "refunded": ch.refunded,
                        "customer": ch.customer,
                    }
                )
            return normalized
        except Exception as exc:
            LOGGER.warning("Failed to fetch Stripe charges: %s", exc)
            return []

