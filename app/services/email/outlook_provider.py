"""
Outlook/Hotmail provider for unified email service.
Uses Microsoft Graph API with MSAL authentication.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import httpx
from dotenv import load_dotenv

from app.services.email.models import EmailAddress, EmailMessage, Provider

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Try to import MSAL
try:
    import msal
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    LOGGER.warning("msal not installed. Install with: pip install msal")

# Legacy single-account config (still supported)
_LEGACY_TOKEN_PATH = Path(os.getenv("OUTLOOK_TOKEN_PATH", "data/outlook_tokens.json"))
_LEGACY_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
_LEGACY_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
_LEGACY_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "common")

SCOPES = ["offline_access", "Mail.Read", "Mail.Send", "User.Read"]
LOOKBACK_DAYS = int(os.getenv("EMAIL_SYNC_LOOKBACK_DAYS", "30"))
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
_CONSUMERS_AUTHORITY = "https://login.microsoftonline.com/consumers"


def _load_indexed_accounts() -> list[dict]:
    """
    Load per-account config from env vars:
      OUTLOOK_1_ADDRESS, OUTLOOK_1_CLIENT_ID, OUTLOOK_1_TOKEN_PATH
      OUTLOOK_2_ADDRESS, OUTLOOK_2_CLIENT_ID, OUTLOOK_2_TOKEN_PATH
      ...
    Returns list of dicts with keys: address, client_id, token_path
    """
    accounts = []
    for i in range(1, 10):
        addr = os.getenv(f"OUTLOOK_{i}_ADDRESS")
        if not addr:
            break
        accounts.append({
            "address": addr,
            "client_id": os.getenv(f"OUTLOOK_{i}_CLIENT_ID") or _LEGACY_CLIENT_ID,
            "token_path": Path(os.getenv(f"OUTLOOK_{i}_TOKEN_PATH", f"config/microsoft_tokens_{i}.json")),
        })
    return accounts


class OutlookAccount:
    """Single Outlook/Hotmail account backed by a Microsoft Graph token file."""

    def __init__(self, address: str, client_id: str, token_path: Path) -> None:
        self.address = address
        self.client_id = client_id
        self.token_path = token_path
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._load()

    def _load(self) -> None:
        if not self.token_path.exists():
            LOGGER.warning("Microsoft token file not found: %s. Run scripts/microsoft_auth.py", self.token_path)
            return
        try:
            with open(self.token_path) as f:
                data = json.load(f)
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
        except Exception as exc:
            LOGGER.warning("Failed to load Microsoft tokens from %s: %s", self.token_path, exc)

    def _refresh(self) -> bool:
        """Refresh the access token using the stored refresh token."""
        if not MSAL_AVAILABLE or not self._refresh_token or not self.client_id:
            return False
        try:
            app = msal.PublicClientApplication(self.client_id, authority=_CONSUMERS_AUTHORITY)
            result = app.acquire_token_by_refresh_token(self._refresh_token, scopes=SCOPES)
            if "access_token" in result:
                self._access_token = result["access_token"]
                if "refresh_token" in result:
                    self._refresh_token = result["refresh_token"]
                # Persist updated tokens
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path) as f:
                    existing = json.load(f)
                existing["access_token"] = result["access_token"]
                if "refresh_token" in result:
                    existing["refresh_token"] = result["refresh_token"]
                with open(self.token_path, "w") as f:
                    json.dump(existing, f, indent=2)
                return True
        except Exception as exc:
            LOGGER.warning("Token refresh failed for %s: %s", self.address, exc)
        return False

    def get_headers(self) -> dict:
        if not self._access_token:
            self._refresh()
        if not self._access_token:
            raise RuntimeError(f"Outlook account {self.address} not authenticated. Run scripts/microsoft_auth.py")
        return {"Authorization": f"Bearer {self._access_token}"}

    def request(self, method: str, url: str, **kwargs) -> "httpx.Response":
        """Make an authenticated Graph API request, auto-refreshing on 401."""
        with httpx.Client() as client:
            resp = getattr(client, method)(url, headers=self.get_headers(), timeout=30.0, **kwargs)
            if resp.status_code == 401 and self._refresh():
                resp = getattr(client, method)(url, headers=self.get_headers(), timeout=30.0, **kwargs)
            return resp


class OutlookProvider:
    """
    Outlook provider for unified email service.

    Supports multiple indexed accounts via env vars:
      OUTLOOK_1_ADDRESS / OUTLOOK_1_CLIENT_ID / OUTLOOK_1_TOKEN_PATH
      OUTLOOK_2_ADDRESS / OUTLOOK_2_CLIENT_ID / OUTLOOK_2_TOKEN_PATH

    After running scripts/microsoft_auth.py for each account, the provider
    auto-discovers and manages them here.

    Legacy single-account mode (OUTLOOK_CLIENT_ID + OUTLOOK_TOKEN_PATH) still
    works via the fallback path.
    """

    def __init__(self) -> None:
        self._accounts: dict[str, OutlookAccount] = {}
        self._init_accounts()

    def _init_accounts(self) -> None:
        """Load all configured Outlook/Hotmail accounts."""
        # Indexed accounts (preferred)
        for cfg in _load_indexed_accounts():
            acct = OutlookAccount(cfg["address"], cfg["client_id"], cfg["token_path"])
            self._accounts[cfg["address"].lower()] = acct
            LOGGER.info("Registered Outlook account: %s", cfg["address"])

        # Legacy single-account fallback
        if not self._accounts and _LEGACY_CLIENT_ID and (_LEGACY_CLIENT_SECRET or _LEGACY_TOKEN_PATH.exists()):
            self._init_legacy()

    def _init_legacy(self) -> None:
        """Initialize the legacy single-account confidential-client mode."""
        if not MSAL_AVAILABLE:
            return
        try:
            app = msal.ConfidentialClientApplication(
                _LEGACY_CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{_LEGACY_TENANT_ID}",
                client_credential=_LEGACY_CLIENT_SECRET,
            )
            accounts = app.get_accounts()
            if accounts:
                result = app.acquire_token_silent(SCOPES, account=accounts[0])
                if result and "access_token" in result:
                    addr = os.getenv("OUTLOOK_1_ADDRESS", "outlook")
                    self._accounts[addr.lower()] = _LegacyAccount(addr, result["access_token"])
        except Exception as exc:
            LOGGER.warning("Legacy Outlook init failed: %s", exc)

    def _account_for(self, address: str) -> Optional["OutlookAccount"]:
        key = address.lower()
        return self._accounts.get(key)

    @property
    def access_token(self) -> Optional[str]:
        """Compat shim: return first account's token."""
        for acct in self._accounts.values():
            try:
                return acct.get_headers()["Authorization"].split(" ", 1)[1]
            except Exception:
                pass
        return None

    def _parse_email_address(self, addr_obj: dict) -> EmailAddress:
        """Parse email address from Graph API response."""
        return EmailAddress(
            name=addr_obj.get("name"),
            address=addr_obj.get("emailAddress", {}).get("address", ""),
        )

    def _parse_message(self, msg_data: dict, account: str) -> EmailMessage:
        """Parse Outlook message into unified EmailMessage."""
        # Parse date
        date_str = msg_data.get("receivedDateTime", "")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            date = datetime.now(timezone.utc)

        # Parse body
        body_text = msg_data.get("body", {}).get("content", "")
        body_html = None
        if msg_data.get("body", {}).get("contentType") == "html":
            body_html = body_text
            # Extract text from HTML (simple version)
            import re
            body_text = re.sub(r"<[^>]+>", "", body_html)

        return EmailMessage(
            id=msg_data["id"],
            thread_id=msg_data.get("conversationId"),
            provider="outlook",
            account=account,
            subject=msg_data.get("subject", ""),
            body_text=body_text,
            body_html=body_html,
            from_=self._parse_email_address(msg_data.get("from", {})),
            to=[self._parse_email_address(addr) for addr in msg_data.get("toRecipients", [])],
            cc=[self._parse_email_address(addr) for addr in msg_data.get("ccRecipients", [])],
            bcc=[self._parse_email_address(addr) for addr in msg_data.get("bccRecipients", [])],
            date=date,
            is_unread=not msg_data.get("isRead", False),
            is_important=msg_data.get("importance", "normal") == "high",
            labels=[],  # Outlook uses categories, could map these
            raw_metadata=msg_data,
        )

    def list_messages(self, account: str, folder: str = "Inbox", top: int = 50) -> List[EmailMessage]:
        """List messages from Outlook."""
        acct = self._account_for(account)
        if not acct:
            LOGGER.warning("Outlook account not found or not authenticated: %s", account)
            return []

        try:
            lookback_date = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).isoformat()
            url = f"{GRAPH_API_BASE}/me/mailFolders/{folder}/messages"
            params = {
                "$top": top,
                "$filter": f"receivedDateTime ge {lookback_date}",
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,isRead,importance,body,conversationId",
            }
            response = acct.request("get", url, params=params)
            response.raise_for_status()
            messages = response.json().get("value", [])
            return [self._parse_message(m, account) for m in messages]
        except Exception as exc:
            LOGGER.error("Failed to list Outlook messages for %s: %s", account, exc)
            return []

    def search(self, account: str, query: str, top: int = 50) -> List[EmailMessage]:
        """Search messages in Outlook."""
        acct = self._account_for(account)
        if not acct:
            return []

        try:
            url = f"{GRAPH_API_BASE}/me/messages"
            params = {
                "$search": f'"{query}"',
                "$top": top,
                "$orderby": "receivedDateTime desc",
            }
            response = acct.request("get", url, params=params)
            response.raise_for_status()
            messages = response.json().get("value", [])
            return [self._parse_message(m, account) for m in messages]
        except Exception as exc:
            LOGGER.error("Failed to search Outlook messages for %s: %s", account, exc)
            return []

    def get_message(self, account: str, message_id: str) -> Optional[EmailMessage]:
        """Get a specific message by ID."""
        acct = self._account_for(account)
        if not acct:
            return None

        try:
            url = f"{GRAPH_API_BASE}/me/messages/{message_id}"
            response = acct.request("get", url)
            response.raise_for_status()
            return self._parse_message(response.json(), account)
        except Exception as exc:
            LOGGER.error("Failed to get Outlook message %s: %s", message_id, exc)
            return None

    def send_message(
        self,
        account: str,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> str:
        """Send an email via Outlook."""
        acct = self._account_for(account)
        if not acct:
            raise RuntimeError(f"Outlook account {account} not configured. Run scripts/microsoft_auth.py")

        try:
            url = f"{GRAPH_API_BASE}/me/sendMail"
            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if body_html else "Text",
                        "content": body_html or body_text,
                    },
                    "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
                },
            }
            response = acct.request("post", url, json=payload)
            response.raise_for_status()

            LOGGER.info("Outlook message sent")
            return "sent"  # Outlook doesn't return message ID immediately
        except Exception as exc:
            LOGGER.error("Failed to send Outlook message: %s", exc)
            raise

