from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

try:
    import plaid
    from plaid.api import plaid_api
    from plaid.model.transactions_get_request import TransactionsGetRequest
    from plaid.model.accounts_get_request import AccountsGetRequest
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
except ImportError:
    plaid = None
    plaid_api = None
    TransactionsGetRequest = None
    AccountsGetRequest = None
    ItemPublicTokenExchangeRequest = None
    Configuration = None
    ApiClient = None

LOGGER = logging.getLogger(__name__)


@dataclass
class BankAccount:
    account_id: str
    name: str
    bank: str
    account_type: str  # checking, savings, credit, loan
    balance: Optional[float] = None
    currency: str = "USD"
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, any]:
        return {
            "account_id": self.account_id,
            "name": self.name,
            "bank": self.bank,
            "account_type": self.account_type,
            "balance": self.balance,
            "currency": self.currency,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class Transaction:
    transaction_id: str
    account_id: str
    amount: float
    date: datetime
    merchant: Optional[str] = None
    category: Optional[str] = None
    description: str = ""
    pending: bool = False

    def to_dict(self) -> Dict[str, any]:
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "amount": self.amount,
            "date": self.date.isoformat(),
            "merchant": self.merchant,
            "category": self.category,
            "description": self.description,
            "pending": self.pending,
        }


class PlaidIntegration:
    """Manages Plaid API connections for bank account aggregation."""

    def __init__(self) -> None:
        self.client_id = os.getenv("PLAID_CLIENT_ID")
        self.secret = os.getenv("PLAID_SECRET")
        self.environment = os.getenv("PLAID_ENVIRONMENT", "sandbox")  # sandbox, development, production
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Plaid API client if credentials are available."""
        if not plaid:
            LOGGER.warning("plaid-python library not installed. Install with: pip install plaid-python")
            return

        if not self.client_id or not self.secret:
            LOGGER.warning("Plaid credentials not configured. Set PLAID_CLIENT_ID and PLAID_SECRET in .env")
            return

        try:
            configuration = Configuration(
                host=plaid.Environment[self.environment.upper()],
                api_key={
                    "clientId": self.client_id,
                    "secret": self.secret,
                },
            )
            api_client = ApiClient(configuration)
            self.client = plaid_api.PlaidApi(api_client)
            LOGGER.info("Plaid client initialized for environment: %s", self.environment)
        except Exception as exc:
            LOGGER.error("Failed to initialize Plaid client: %s", exc)
            self.client = None

    def is_configured(self) -> bool:
        """Check if Plaid is properly configured."""
        return self.client is not None

    def exchange_public_token(self, public_token: str) -> Optional[str]:
        """Exchange a public token for an access token."""
        if not self.client:
            LOGGER.error("Plaid client not initialized")
            return None

        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            return response["access_token"]
        except Exception as exc:
            LOGGER.error("Failed to exchange public token: %s", exc)
            return None

    def get_accounts(self, access_token: str) -> List[BankAccount]:
        """Fetch all accounts for a given access token."""
        if not self.client:
            return []

        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            accounts = []

            for account in response["accounts"]:
                accounts.append(
                    BankAccount(
                        account_id=account["account_id"],
                        name=account["name"],
                        bank=account.get("institution_id", "Unknown"),
                        account_type=account["type"],
                        balance=account.get("balances", {}).get("available"),
                        currency=account.get("balances", {}).get("iso_currency_code", "USD"),
                        last_updated=datetime.now(),
                    )
                )
            return accounts
        except Exception as exc:
            LOGGER.error("Failed to fetch accounts from Plaid: %s", exc)
            return []

    def get_transactions(
        self,
        access_token: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_ids: Optional[List[str]] = None,
    ) -> List[Transaction]:
        """Fetch transactions for given accounts and date range."""
        if not self.client:
            return []

        if not start_date:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                account_ids=account_ids,
            )
            response = self.client.transactions_get(request)
            transactions = []

            for txn in response["transactions"]:
                transactions.append(
                    Transaction(
                        transaction_id=txn["transaction_id"],
                        account_id=txn["account_id"],
                        amount=txn["amount"],
                        date=datetime.fromisoformat(txn["date"]),
                        merchant=txn.get("merchant_name"),
                        category=", ".join(txn.get("category", [])),
                        description=txn.get("name", ""),
                        pending=txn.get("pending", False),
                    )
                )
            return transactions
        except Exception as exc:
            LOGGER.error("Failed to fetch transactions from Plaid: %s", exc)
            return []

