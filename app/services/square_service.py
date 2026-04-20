from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

try:
    from square.client import Client
except ImportError:
    Client = None

LOGGER = logging.getLogger(__name__)


class SquareService:
    """
    Read-only Square integration for POS and product sales.
    """

    def __init__(self) -> None:
        access_token = os.getenv("SQUARE_ACCESS_TOKEN")
        if not access_token:
            LOGGER.warning("SQUARE_ACCESS_TOKEN not set; SquareService disabled.")
            self.client = None
            return

        if not Client:
            LOGGER.warning("squareup library not installed. Install with: pip install squareup")
            self.client = None
            return

        try:
            self.client = Client(
                access_token=access_token,
                environment="production",  # or 'sandbox' if desired
            )
        except Exception as exc:
            LOGGER.error("Failed to initialize Square client: %s", exc)
            self.client = None

    def is_enabled(self) -> bool:
        return self.client is not None

    def fetch_recent_payments(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        try:
            # Example; adapt to actual Square Payments API
            result = self.client.payments.list_payments(limit=limit)
            normalized: List[Dict[str, Any]] = []

            if result.is_success():
                for p in result.body.get("payments", []):
                    normalized.append(
                        {
                            "id": p.get("id"),
                            "amount": int(p["amount_money"]["amount"]) / 100.0,
                            "currency": p["amount_money"]["currency"],
                            "created_at": p.get("created_at"),
                            "status": p.get("status"),
                            "note": p.get("note"),
                        }
                    )
            else:
                LOGGER.warning("Square list_payments error: %s", result.errors)
            return normalized
        except Exception as exc:
            LOGGER.warning("Failed to fetch Square payments: %s", exc)
            return []

