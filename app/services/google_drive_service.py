"""
Google Drive service with automatic OAuth token management.
Handles authentication, token refresh, and Drive API operations.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Configuration from environment
TOKENS_PATH = Path(
    os.getenv("GOOGLE_DRIVE_TOKENS_PATH", "config/google_drive_tokens.json")
)
CLIENT_ID = os.getenv("GOOGLE_DRIVE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET")
REDIRECT_URI = os.getenv(
    "GOOGLE_DRIVE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
)

# Parse scopes from environment
_scope_string = os.getenv(
    "GOOGLE_DRIVE_SCOPES",
    "https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/userinfo.email",
)
SCOPES = _scope_string.split() if _scope_string else []

TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
USERINFO_API = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleTokens:
    """Container for Google OAuth tokens."""

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
    def from_dict(cls, data: Dict[str, Any]) -> "GoogleTokens":
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            scope=data.get("scope", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            expires_at=data.get("expires_at"),
        )


class GoogleDriveService:
    """Service for Google Drive operations with automatic token management."""

    def __init__(self) -> None:
        self._tokens: Optional[GoogleTokens] = None
        self._load_tokens()

    # ---------- Token storage ----------
    def _load_tokens(self) -> None:
        """Load tokens from file."""
        if TOKENS_PATH.exists():
            try:
                with TOKENS_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tokens = GoogleTokens.from_dict(data)
                LOGGER.info("Loaded Google Drive tokens from %s", TOKENS_PATH)
            except Exception as exc:
                LOGGER.warning("Failed to load Google Drive tokens: %s", exc)
                self._tokens = None
        else:
            LOGGER.info("Google Drive tokens file not found: %s", TOKENS_PATH)

    def _save_tokens(self, data: Dict[str, Any]) -> None:
        """Save tokens to file, preserving refresh_token if not in new data."""
        # Google only returns refresh_token on first consent; preserve if missing
        refresh = data.get("refresh_token") or (
            self._tokens.refresh_token if self._tokens else None
        )

        expires_in = data.get("expires_in", 3600)
        expires_at = time.time() + expires_in - 60  # Refresh 1 min early

        payload = {
            **data,
            "refresh_token": refresh,
            "expires_at": expires_at,
        }

        self._tokens = GoogleTokens.from_dict(payload)
        TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with TOKENS_PATH.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        LOGGER.info("Saved Google Drive tokens to %s", TOKENS_PATH)

    # ---------- OAuth flows ----------
    def build_auth_url(self, state: str = "jarvis") -> str:
        """Build Google OAuth authorization URL."""
        if not CLIENT_ID:
            raise ValueError("GOOGLE_DRIVE_CLIENT_ID not configured")

        from urllib.parse import urlencode

        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",  # Force consent to get refresh_token
            "state": state,
        }

        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    async def exchange_code_for_tokens(self, code: str) -> GoogleTokens:
        """Exchange authorization code for access and refresh tokens."""
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError(
                "GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET must be configured"
            )

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
        LOGGER.info("Exchanged code for Google Drive tokens successfully")
        return self._tokens

    async def _refresh_if_needed(self) -> None:
        """Refresh access token if expired or about to expire."""
        if not self._tokens:
            raise RuntimeError(
                "Google Drive not authorized yet. Please complete OAuth flow first."
            )

        if time.time() < self._tokens.expires_at:
            return  # Token still valid

        if not self._tokens.refresh_token:
            raise RuntimeError(
                "No refresh token available. Please re-authorize Google Drive."
            )

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

        # Google often omits refresh_token on refresh -> preserve existing
        data["refresh_token"] = self._tokens.refresh_token
        self._save_tokens(data)
        LOGGER.info("Refreshed Google Drive access token")

    # ---------- API helpers ----------
    async def _auth_client(self) -> httpx.AsyncClient:
        """Get authenticated HTTP client with valid access token."""
        await self._refresh_if_needed()
        headers = {"Authorization": f"Bearer {self._tokens.access_token}"}
        return httpx.AsyncClient(timeout=20.0, headers=headers)

    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user's Google account info."""
        client = await self._auth_client()
        try:
            resp = await client.get(USERINFO_API)
            resp.raise_for_status()
            return {"success": True, "user": resp.json()}
        except Exception as exc:
            LOGGER.error("Failed to get user info: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def list_files(
        self, query: Optional[str] = None, page_size: int = 20
    ) -> Dict[str, Any]:
        """List files in Google Drive."""
        client = await self._auth_client()
        params = {
            "pageSize": page_size,
            "fields": "files(id,name,mimeType,modifiedTime,webViewLink)",
        }
        if query:
            params["q"] = query

        try:
            resp = await client.get(f"{DRIVE_API_BASE}/files", params=params)
            resp.raise_for_status()
            return {"success": True, "files": resp.json().get("files", [])}
        except Exception as exc:
            LOGGER.error("Failed to list files: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata by ID."""
        client = await self._auth_client()
        params = {"fields": "id,name,mimeType,modifiedTime,webViewLink,size"}
        try:
            resp = await client.get(f"{DRIVE_API_BASE}/files/{file_id}", params=params)
            resp.raise_for_status()
            return {"success": True, "file": resp.json()}
        except Exception as exc:
            LOGGER.error("Failed to get file: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def download_file(self, file_id: str) -> Dict[str, Any]:
        """Download file content by ID."""
        client = await self._auth_client()
        try:
            # First get file metadata
            metadata_resp = await client.get(
                f"{DRIVE_API_BASE}/files/{file_id}",
                params={"fields": "name,mimeType"},
            )
            metadata_resp.raise_for_status()
            metadata = metadata_resp.json()

            # Download file content
            download_resp = await client.get(
                f"{DRIVE_API_BASE}/files/{file_id}?alt=media"
            )
            download_resp.raise_for_status()

            return {
                "success": True,
                "name": metadata.get("name"),
                "mime_type": metadata.get("mimeType"),
                "content": download_resp.content,
                "text": download_resp.text if "text" in metadata.get("mimeType", "") else None,
            }
        except Exception as exc:
            LOGGER.error("Failed to download file: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def upload_note(
        self, name: str, content: str, folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a text file (note) to Google Drive."""
        client = await self._auth_client()

        # Create file metadata
        file_metadata = {
            "name": name,
            "mimeType": "text/plain",
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]

        try:
            # Create multipart upload
            files = {
                "metadata": (
                    None,
                    json.dumps(file_metadata),
                    "application/json; charset=UTF-8",
                ),
                "file": (name, content.encode("utf-8"), "text/plain"),
            }

            resp = await client.post(
                f"{DRIVE_API_BASE}/files?uploadType=multipart",
                files=files,
            )
            resp.raise_for_status()

            file_data = resp.json()
            LOGGER.info("Uploaded note to Drive: %s (ID: %s)", name, file_data.get("id"))
            return {"success": True, "file": file_data}
        except Exception as exc:
            LOGGER.error("Failed to upload note: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    async def create_folder(self, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a folder in Google Drive."""
        client = await self._auth_client()

        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        try:
            resp = await client.post(
                f"{DRIVE_API_BASE}/files",
                json=file_metadata,
            )
            resp.raise_for_status()

            folder_data = resp.json()
            LOGGER.info("Created folder in Drive: %s (ID: %s)", name, folder_data.get("id"))
            return {"success": True, "folder": folder_data}
        except Exception as exc:
            LOGGER.error("Failed to create folder: %s", exc)
            return {"success": False, "error": str(exc)}
        finally:
            await client.aclose()

    def is_authorized(self) -> bool:
        """Check if Google Drive is authorized (has tokens)."""
        return self._tokens is not None and bool(self._tokens.refresh_token)


# Singleton instance
google_drive_service = GoogleDriveService()

