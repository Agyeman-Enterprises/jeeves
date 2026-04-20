"""
Enhanced Dropbox service with OAuth token management and file indexing.
Handles Dropbox API operations with automatic token refresh and ChromaDB indexing.
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
TOKENS_PATH = Path(os.getenv("DROPBOX_TOKEN_PATH", "config/dropbox_tokens.json"))
APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")  # Can be set directly or loaded from file

DROPBOX_API_BASE = "https://api.dropboxapi.com/2"
DROPBOX_OAUTH_BASE = "https://www.dropbox.com/oauth2"
TOKEN_URL = f"{DROPBOX_OAUTH_BASE}/token"

# Try to import Dropbox SDK (optional, for advanced features)
try:
    import dropbox
    DROPBOX_SDK_AVAILABLE = True
except ImportError:
    DROPBOX_SDK_AVAILABLE = False
    LOGGER.info("Dropbox SDK not available, using REST API only")


class DropboxTokens:
    """Container for Dropbox OAuth tokens."""

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[float] = None,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at or (time.time() + 14400)  # 4 hours default

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DropboxTokens":
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=data.get("expires_at"),
        )


class DropboxService:
    """Service for Dropbox operations with automatic token management and file indexing."""

    def __init__(self) -> None:
        self._tokens: Optional[DropboxTokens] = None
        self._sdk_client: Optional[Any] = None
        self._load_tokens()
        self._init_sdk_client()

    # ---------- Token management ----------
    def _load_tokens(self) -> None:
        """Load tokens from file or environment."""
        # Try file first
        if TOKENS_PATH.exists():
            try:
                with TOKENS_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tokens = DropboxTokens.from_dict(data)
                LOGGER.info("Loaded Dropbox tokens from %s", TOKENS_PATH)
                return
            except Exception as exc:
                LOGGER.warning("Failed to load Dropbox tokens from file: %s", exc)

        # Fallback to environment variable
        if REFRESH_TOKEN:
            # We'll need to exchange refresh token for access token
            self._tokens = DropboxTokens(
                access_token="",  # Will be refreshed
                refresh_token=REFRESH_TOKEN,
            )
            LOGGER.info("Using Dropbox refresh token from environment")

    def _save_tokens(self, data: Dict[str, Any]) -> None:
        """Save tokens to file."""
        refresh = data.get("refresh_token") or (
            self._tokens.refresh_token if self._tokens else None
        )
        expires_in = data.get("expires_in", 14400)  # 4 hours
        expires_at = time.time() + expires_in - 60

        payload = {
            "access_token": data.get("access_token", ""),
            "refresh_token": refresh,
            "expires_at": expires_at,
        }

        self._tokens = DropboxTokens.from_dict(payload)
        TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with TOKENS_PATH.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        LOGGER.info("Saved Dropbox tokens to %s", TOKENS_PATH)
        self._init_sdk_client()  # Reinitialize SDK client with new token

    def build_auth_url(self, state: str = "jarvis") -> str:
        """Build Dropbox OAuth authorization URL."""
        if not APP_KEY:
            raise ValueError("DROPBOX_APP_KEY not configured")

        from urllib.parse import urlencode

        params = {
            "client_id": APP_KEY,
            "response_type": "code",
            "redirect_uri": "http://localhost:8081/auth/dropbox/callback",
            "state": state,
        }

        return f"{DROPBOX_OAUTH_BASE}/authorize?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> DropboxTokens:
        """Exchange authorization code for tokens."""
        if not APP_KEY or not APP_SECRET:
            raise ValueError("DROPBOX_APP_KEY and DROPBOX_APP_SECRET must be configured")

        payload = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": APP_KEY,
            "client_secret": APP_SECRET,
            "redirect_uri": "http://localhost:8081/auth/dropbox/callback",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(TOKEN_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()

        self._save_tokens(data)
        LOGGER.info("Exchanged code for Dropbox tokens successfully")
        return self._tokens

    async def _refresh_if_needed(self) -> None:
        """Refresh access token if expired."""
        if not self._tokens:
            raise RuntimeError("Dropbox not authorized yet. Please complete OAuth flow first.")

        if time.time() < self._tokens.expires_at:
            return

        if not self._tokens.refresh_token:
            raise RuntimeError("No refresh token available. Please re-authorize Dropbox.")

        if not APP_KEY or not APP_SECRET:
            raise ValueError("DROPBOX_APP_KEY and DROPBOX_APP_SECRET must be configured")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._tokens.refresh_token,
            "client_id": APP_KEY,
            "client_secret": APP_SECRET,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(TOKEN_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()

        # Preserve refresh token if not returned
        if "refresh_token" not in data:
            data["refresh_token"] = self._tokens.refresh_token

        self._save_tokens(data)
        LOGGER.info("Refreshed Dropbox access token")

    def _init_sdk_client(self) -> None:
        """Initialize Dropbox SDK client if available."""
        if not DROPBOX_SDK_AVAILABLE:
            return

        if self._tokens and self._tokens.access_token:
            try:
                self._sdk_client = dropbox.Dropbox(self._tokens.access_token)
            except Exception as exc:
                LOGGER.warning("Failed to initialize Dropbox SDK client: %s", exc)

    async def _auth_client(self) -> httpx.AsyncClient:
        """Get authenticated HTTP client."""
        await self._refresh_if_needed()
        headers = {"Authorization": f"Bearer {self._tokens.access_token}"}
        return httpx.AsyncClient(timeout=30.0, headers=headers)

    # ---------- Dropbox API methods ----------
    async def list_files(self, path: str = "") -> Dict[str, Any]:
        """List files in a Dropbox folder."""
        client = await self._auth_client()

        payload = {"path": path, "recursive": False}

        try:
            resp = await client.post(
                f"{DROPBOX_API_BASE}/files/list_folder", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "entries": data.get("entries", [])}
        except Exception as exc:
            LOGGER.error("Failed to list files: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def download_file(self, path: str) -> Dict[str, Any]:
        """Download file content from Dropbox."""
        client = await self._auth_client()

        payload = {"path": path}

        try:
            resp = await client.post(
                f"{DROPBOX_API_BASE}/files/download",
                json=payload,
                headers={"Dropbox-API-Arg": json.dumps(payload)},
            )
            resp.raise_for_status()

            # Extract filename from response headers
            import re
            filename_match = re.search(r'filename="([^"]+)"', resp.headers.get("content-disposition", ""))

            return {
                "success": True,
                "content": resp.content,
                "text": resp.text if resp.headers.get("content-type", "").startswith("text/") else None,
                "filename": filename_match.group(1) if filename_match else Path(path).name,
            }
        except Exception as exc:
            LOGGER.error("Failed to download file: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def upload_file(
        self, path: str, data: bytes, mode: str = "overwrite"
    ) -> Dict[str, Any]:
        """Upload file to Dropbox."""
        client = await self._auth_client()

        payload = {"path": path, "mode": mode}

        try:
            resp = await client.post(
                f"{DROPBOX_API_BASE}/files/upload",
                content=data,
                headers={
                    "Dropbox-API-Arg": json.dumps(payload),
                    "Content-Type": "application/octet-stream",
                },
            )
            resp.raise_for_status()
            result = resp.json()
            LOGGER.info("Uploaded file to Dropbox: %s", path)
            return {"success": True, "file": result}
        except Exception as exc:
            LOGGER.error("Failed to upload file: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def search(self, query: str, path: str = "") -> Dict[str, Any]:
        """Search files in Dropbox."""
        client = await self._auth_client()

        payload = {"query": query, "path": path, "max_results": 100}

        try:
            resp = await client.post(
                f"{DROPBOX_API_BASE}/files/search_v2", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "matches": data.get("matches", [])}
        except Exception as exc:
            LOGGER.error("Failed to search files: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def get_recent_changes(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Get recent changes in Dropbox."""
        client = await self._auth_client()

        payload = {"cursor": cursor} if cursor else {}

        try:
            resp = await client.post(
                f"{DROPBOX_API_BASE}/files/list_folder/continue" if cursor
                else f"{DROPBOX_API_BASE}/files/list_folder",
                json=payload if cursor else {"path": "", "recursive": True},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "success": True,
                "entries": data.get("entries", []),
                "cursor": data.get("cursor"),
                "has_more": data.get("has_more", False),
            }
        except Exception as exc:
            LOGGER.error("Failed to get recent changes: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    def is_authorized(self) -> bool:
        """Check if Dropbox is authorized."""
        return self._tokens is not None and bool(self._tokens.access_token)


# Singleton instance
dropbox_service = DropboxService()

