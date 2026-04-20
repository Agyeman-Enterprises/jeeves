from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.services.plaid_integration import PlaidIntegration, BankAccount, Transaction

LOGGER = logging.getLogger(__name__)


class PlaidService:
    """
    Thin wrapper around PlaidIntegration to fetch accounts, balances, and transactions.
    This service is read-only and used by FinanceAgent.
    """

    def __init__(self) -> None:
        self.plaid = PlaidIntegration()
        # Store access tokens per account (would be loaded from secure storage in production)
        self._access_tokens: Dict[str, str] = {}

    def is_enabled(self) -> bool:
        """Check if Plaid is configured and enabled."""
        return self.plaid.is_configured()

    def add_access_token(self, account_name: str, access_token: str) -> None:
        """Store an access token for a specific account."""
        self._access_tokens[account_name] = access_token

    def fetch_accounts(self) -> List[Dict[str, Any]]:
        """
        Return a normalized list of accounts with:
        - account_id
        - name
        - official_name
        - subtype
        - balances (available, current)
        """
        if not self.is_enabled():
            return []

        all_accounts: List[Dict[str, Any]] = []

        # Fetch accounts for each stored access token
        for account_name, access_token in self._access_tokens.items():
            try:
                plaid_accounts = self.plaid.get_accounts(access_token)
                for acc in plaid_accounts:
                    all_accounts.append(
                        {
                            "account_id": acc.account_id,
                            "name": acc.name,
                            "official_name": acc.name,  # PlaidIntegration doesn't separate these
                            "subtype": acc.account_type,
                            "balance": {
                                "available": acc.balance,
                                "current": acc.balance,
                            },
                            "institution": acc.bank,
                            "currency": acc.currency,
                            "last_updated": acc.last_updated.isoformat() if acc.last_updated else None,
                        }
                    )
            except Exception as exc:
                LOGGER.warning("Failed to fetch accounts for %s: %s", account_name, exc)

        return all_accounts

    def fetch_recent_transactions(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch normalized transactions for the last N days:
        - date
        - amount
        - name/merchant
        - account_id
        - category (if provided)
        """
        if not self.is_enabled():
            return []

        all_transactions: List[Dict[str, Any]] = []
        start_date = date.today() - timedelta(days=days)
        end_date = date.today()

        # Fetch transactions for each stored access token
        for account_name, access_token in self._access_tokens.items():
            try:
                from datetime import datetime
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.max.time())

                plaid_transactions = self.plaid.get_transactions(
                    access_token, start_date=start_dt, end_date=end_dt
                )
                for txn in plaid_transactions:
                    all_transactions.append(
                        {
                            "date": txn.date.isoformat(),
                            "amount": txn.amount,
                            "name": txn.merchant or txn.description,
                            "merchant": txn.merchant,
                            "account_id": txn.account_id,
                            "category": txn.category,
                            "description": txn.description,
                            "pending": txn.pending,
                            "transaction_id": txn.transaction_id,
                        }
                    )
            except Exception as exc:
                LOGGER.warning("Failed to fetch transactions for %s: %s", account_name, exc)

        return all_transactions

