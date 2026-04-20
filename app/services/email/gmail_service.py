"""
Gmail service with automatic OAuth token management.
Handles Gmail API operations with automatic token refresh.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Configuration from environment
TOKENS_PATH = Path(os.getenv("GMAIL_TOKEN_PATH", "config/gmail_tokens.json"))
CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8081/auth/gmail/callback")

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
]

TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
USERINFO_API = "https://www.googleapis.com/oauth2/v2/userinfo"


class GmailTokens:
    """Container for Gmail OAuth tokens."""

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
    def from_dict(cls, data: Dict[str, Any]) -> "GmailTokens":
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            scope=data.get("scope", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            expires_at=data.get("expires_at"),
        )


class GmailService:
    """Service for Gmail operations with automatic token management."""

    def __init__(self) -> None:
        self._tokens: Optional[GmailTokens] = None
        self._load_tokens()

    # ---------- Token management ----------
    def _load_tokens(self) -> None:
        """Load tokens from file."""
        if TOKENS_PATH.exists():
            try:
                with TOKENS_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tokens = GmailTokens.from_dict(data)
                LOGGER.info("Loaded Gmail tokens from %s", TOKENS_PATH)
            except Exception as exc:
                LOGGER.warning("Failed to load Gmail tokens: %s", exc)
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

        self._tokens = GmailTokens.from_dict(payload)
        TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with TOKENS_PATH.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        LOGGER.info("Saved Gmail tokens to %s", TOKENS_PATH)

    def build_auth_url(self, state: str = "jarvis") -> str:
        """Build Gmail OAuth authorization URL."""
        if not CLIENT_ID:
            raise ValueError("GMAIL_CLIENT_ID not configured")

        from urllib.parse import urlencode

        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": state,
        }

        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    async def exchange_code_for_tokens(self, code: str) -> GmailTokens:
        """Exchange authorization code for tokens."""
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError("GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be configured")

        payload = {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(TOKEN_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()

        self._save_tokens(data)
        LOGGER.info("Exchanged code for Gmail tokens successfully")
        return self._tokens

    async def _refresh_if_needed(self) -> None:
        """Refresh access token if expired."""
        if not self._tokens:
            raise RuntimeError("Gmail not authorized yet. Please complete OAuth flow first.")

        if time.time() < self._tokens.expires_at:
            return

        if not self._tokens.refresh_token:
            raise RuntimeError("No refresh token available. Please re-authorize Gmail.")

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
        LOGGER.info("Refreshed Gmail access token")

    async def _auth_client(self) -> httpx.AsyncClient:
        """Get authenticated HTTP client."""
        await self._refresh_if_needed()
        headers = {"Authorization": f"Bearer {self._tokens.access_token}"}
        return httpx.AsyncClient(timeout=30.0, headers=headers)

    # ---------- Gmail API methods ----------
    async def list_messages(
        self, query: Optional[str] = None, max_results: int = 50
    ) -> Dict[str, Any]:
        """List messages from Gmail."""
        client = await self._auth_client()
        params = {"maxResults": max_results}
        if query:
            params["q"] = query

        try:
            resp = await client.get(f"{GMAIL_API_BASE}/users/me/messages", params=params)
            resp.raise_for_status()
            return {"success": True, "messages": resp.json().get("messages", [])}
        except Exception as exc:
            LOGGER.error("Failed to list messages: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get full message details by ID."""
        client = await self._auth_client()
        try:
            resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
                params={"format": "full"},
            )
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
        """Send an email via Gmail."""
        client = await self._auth_client()

        # Create message
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        payload = {"raw": raw_message}

        try:
            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/messages/send", json=payload
            )
            resp.raise_for_status()
            result = resp.json()
            LOGGER.info("Sent email via Gmail: %s", result.get("id"))
            return {"success": True, "message_id": result.get("id")}
        except Exception as exc:
            LOGGER.error("Failed to send email: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def search(self, query: str, max_results: int = 50) -> Dict[str, Any]:
        """Search messages with Gmail query syntax."""
        return await self.list_messages(query=query, max_results=max_results)

    async def get_unread_summary(self) -> Dict[str, Any]:
        """Get summary of unread messages."""
        result = await self.search("is:unread", max_results=20)
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
                payload = msg_data.get("payload", {})
                headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
                summary["messages"].append(
                    {
                        "id": msg["id"],
                        "subject": headers.get("Subject", ""),
                        "from": headers.get("From", ""),
                        "snippet": msg_data.get("snippet", ""),
                    }
                )

        return {"success": True, "summary": summary}

    # ---------- Label management ----------

    async def list_labels(self) -> Dict[str, Any]:
        """List all Gmail labels."""
        client = await self._auth_client()
        try:
            resp = await client.get(f"{GMAIL_API_BASE}/users/me/labels")
            resp.raise_for_status()
            return {"success": True, "labels": resp.json().get("labels", [])}
        except Exception as exc:
            LOGGER.error("Failed to list labels: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def create_label(
        self,
        name: str,
        bg_color: str = "#ffffff",
        text_color: str = "#000000",
    ) -> Dict[str, Any]:
        """
        Create a Gmail label (folder).

        Args:
            name:       Display name (e.g. "GMH", "Empower", "Bills")
            bg_color:   Background hex color  (default white)
            text_color: Text hex color        (default black)

        Returns:
            {"success": True, "label_id": "Label_xxx", "name": "..."}
        """
        client = await self._auth_client()
        try:
            body = {
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
                "color": {"backgroundColor": bg_color, "textColor": text_color},
            }
            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/labels", json=body
            )
            resp.raise_for_status()
            data = resp.json()
            LOGGER.info("Created Gmail label: %s (%s)", name, data.get("id"))
            return {"success": True, "label_id": data.get("id"), "name": data.get("name")}
        except Exception as exc:
            LOGGER.error("Failed to create label %s: %s", name, exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def get_or_create_label(self, name: str, bg_color: str = "#ffffff", text_color: str = "#000000") -> Optional[str]:
        """
        Return existing label ID by name, or create it if not found.

        Returns label_id string or None on error.
        """
        labels_result = await self.list_labels()
        if labels_result.get("success"):
            for lbl in labels_result.get("labels", []):
                if lbl.get("name", "").lower() == name.lower():
                    return lbl["id"]
        # Not found — create it
        create_result = await self.create_label(name, bg_color=bg_color, text_color=text_color)
        if create_result.get("success"):
            return create_result.get("label_id")
        return None

    async def modify_message(
        self,
        message_id: str,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Add or remove labels on a single message.

        Returns {"success": True} on success.
        """
        client = await self._auth_client()
        try:
            body: Dict[str, List[str]] = {}
            if add_label_ids:
                body["addLabelIds"] = add_label_ids
            if remove_label_ids:
                body["removeLabelIds"] = remove_label_ids

            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/messages/{message_id}/modify",
                json=body,
            )
            resp.raise_for_status()
            return {"success": True}
        except Exception as exc:
            LOGGER.error("Failed to modify message %s: %s", message_id, exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def batch_modify_messages(
        self,
        message_ids: List[str],
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Apply label changes to multiple messages in one API call.

        Returns {"success": True, "count": N}
        """
        if not message_ids:
            return {"success": True, "count": 0}

        client = await self._auth_client()
        try:
            body: Dict[str, Any] = {"ids": message_ids}
            if add_label_ids:
                body["addLabelIds"] = add_label_ids
            if remove_label_ids:
                body["removeLabelIds"] = remove_label_ids

            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/messages/batchModify",
                json=body,
            )
            resp.raise_for_status()
            LOGGER.info("Batch-modified %d messages", len(message_ids))
            return {"success": True, "count": len(message_ids)}
        except Exception as exc:
            LOGGER.error("Batch modify failed: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    def is_authorized(self) -> bool:
        """Check if Gmail is authorized."""
        return self._tokens is not None and bool(self._tokens.refresh_token)


# Singleton instance
gmail_service = GmailService()

