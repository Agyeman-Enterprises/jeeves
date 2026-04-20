"""
Outlook (Microsoft Graph) service with automatic OAuth token management.
Handles Outlook/Hotmail email operations via Microsoft Graph API.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Configuration from environment
TOKENS_PATH = Path(os.getenv("OUTLOOK_TOKEN_PATH", "config/outlook_tokens.json"))
CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("OUTLOOK_REDIRECT_URI", "http://localhost:8081/auth/outlook/callback")

# Microsoft Graph API scopes
SCOPES = [
    "Mail.ReadWrite",
    "Mail.Send",
    "offline_access",
    "User.Read",
]

TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


class OutlookTokens:
    """Container for Outlook OAuth tokens."""

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        scope: str,
        token_type: str = "Bearer",
        expires_in: int = 3600,
        expires_at: Optional[float] = None,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self.token_type = token_type
        self.expires_in = expires_in
        self.expires_at = expires_at or (time.time() + expires_in - 60)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutlookTokens":
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            scope=data.get("scope", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            expires_at=data.get("expires_at"),
        )


class OutlookService:
    """Service for Outlook operations with automatic token management."""

    def __init__(self) -> None:
        self._tokens: Optional[OutlookTokens] = None
        self._load_tokens()

    # ---------- Token management ----------
    def _load_tokens(self) -> None:
        """Load tokens from file."""
        if TOKENS_PATH.exists():
            try:
                with TOKENS_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tokens = OutlookTokens.from_dict(data)
                LOGGER.info("Loaded Outlook tokens from %s", TOKENS_PATH)
            except Exception as exc:
                LOGGER.warning("Failed to load Outlook tokens: %s", exc)
                self._tokens = None

    def _save_tokens(self, data: Dict[str, Any]) -> None:
        """Save tokens to file."""
        refresh = data.get("refresh_token") or (
            self._tokens.refresh_token if self._tokens else None
        )
        expires_in = data.get("expires_in", 3600)
        expires_at = time.time() + expires_in - 60

        payload = {
            **data,
            "refresh_token": refresh,
            "expires_at": expires_at,
        }

        self._tokens = OutlookTokens.from_dict(payload)
        TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with TOKENS_PATH.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        LOGGER.info("Saved Outlook tokens to %s", TOKENS_PATH)

    def build_auth_url(self, state: str = "jarvis") -> str:
        """Build Outlook OAuth authorization URL."""
        if not CLIENT_ID:
            raise ValueError("OUTLOOK_CLIENT_ID not configured")

        from urllib.parse import urlencode

        params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "response_mode": "query",
            "scope": " ".join(SCOPES),
            "state": state,
        }

        return f"{AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> OutlookTokens:
        """Exchange authorization code for tokens."""
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError("OUTLOOK_CLIENT_ID and OUTLOOK_CLIENT_SECRET must be configured")

        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(TOKEN_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()

        self._save_tokens(data)
        LOGGER.info("Exchanged code for Outlook tokens successfully")
        return self._tokens

    async def _refresh_if_needed(self) -> None:
        """Refresh access token if expired."""
        if not self._tokens:
            raise RuntimeError("Outlook not authorized yet. Please complete OAuth flow first.")

        if time.time() < self._tokens.expires_at:
            return

        if not self._tokens.refresh_token:
            raise RuntimeError("No refresh token available. Please re-authorize Outlook.")

        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": self._tokens.refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(TOKEN_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()

        data["refresh_token"] = self._tokens.refresh_token
        self._save_tokens(data)
        LOGGER.info("Refreshed Outlook access token")

    async def _auth_client(self) -> httpx.AsyncClient:
        """Get authenticated HTTP client."""
        await self._refresh_if_needed()
        headers = {"Authorization": f"Bearer {self._tokens.access_token}"}
        return httpx.AsyncClient(timeout=30.0, headers=headers)

    # ---------- Microsoft Graph API methods ----------
    async def list_messages(
        self, query: Optional[str] = None, top: int = 50
    ) -> Dict[str, Any]:
        """List messages from Outlook."""
        client = await self._auth_client()
        url = f"{GRAPH_API_BASE}/me/messages"
        params = {"$top": top, "$select": "id,subject,from,receivedDateTime,isRead"}
        if query:
            params["$filter"] = query

        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return {"success": True, "messages": resp.json().get("value", [])}
        except Exception as exc:
            LOGGER.error("Failed to list messages: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get full message details by ID."""
        client = await self._auth_client()
        try:
            resp = await client.get(f"{GRAPH_API_BASE}/me/messages/{message_id}")
            resp.raise_for_status()
            return {"success": True, "message": resp.json()}
        except Exception as exc:
            LOGGER.error("Failed to get message: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send an email via Outlook."""
        client = await self._auth_client()

        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body,
                },
                "toRecipients": [{"emailAddress": {"address": to}}],
            },
        }

        try:
            resp = await client.post(
                f"{GRAPH_API_BASE}/me/sendMail", json=payload
            )
            resp.raise_for_status()
            LOGGER.info("Sent email via Outlook to %s", to)
            return {"success": True, "message_id": "sent"}
        except Exception as exc:
            LOGGER.error("Failed to send email: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def search(self, query: str, top: int = 50) -> Dict[str, Any]:
        """Search messages with Microsoft Graph query syntax."""
        # Convert Gmail-style query to Graph filter if needed
        graph_query = query.replace("is:unread", "isRead eq false")
        return await self.list_messages(query=graph_query, top=top)

    async def get_unread_summary(self) -> Dict[str, Any]:
        """Get summary of unread messages."""
        result = await self.list_messages(query="isRead eq false", top=20)
        if not result.get("success"):
            return result

        messages = result.get("messages", [])
        summary = {
            "count": len(messages),
            "messages": [],
        }

        # Get details for first 10
        for msg in messages[:10]:
            msg_detail = await self.get_message(msg["id"])
            if msg_detail.get("success"):
                msg_data = msg_detail["message"]
                from_addr = msg_data.get("from", {}).get("emailAddress", {})
                summary["messages"].append(
                    {
                        "id": msg["id"],
                        "subject": msg_data.get("subject", ""),
                        "from": from_addr.get("address", ""),
                        "snippet": msg_data.get("bodyPreview", ""),
                    }
                )

        return {"success": True, "summary": summary}

    def is_authorized(self) -> bool:
        """Check if Outlook is authorized."""
        return self._tokens is not None and bool(self._tokens.refresh_token)


# Singleton instance
outlook_service = OutlookService()

