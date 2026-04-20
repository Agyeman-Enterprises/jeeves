"""
LinkedIn service for JARVIS.

Handles posting to the ScribeMD company page via the LinkedIn UGC Posts API.
Tokens are loaded from config/linkedin_tokens.json (written by scripts/linkedin_auth.py).
LinkedIn access tokens last ~60 days — no refresh token flow exists for LinkedIn OAuth.
When the token expires, re-run: python scripts/linkedin_auth.py
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

# ── Config ──────────────────────────────────────────────────────────────────
TOKENS_PATH = Path(os.getenv("LINKEDIN_TOKEN_PATH", "config/linkedin_tokens.json"))
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8082/auth/linkedin/callback")
PAGE_ID_ENV = os.getenv("LINKEDIN_SCRIBEMD_PAGE_ID", "")

# LinkedIn API endpoints
UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
ORG_ACLS_URL = "https://api.linkedin.com/v2/organizationAcls"

# Scopes available with current LinkedIn app products:
# - "Sign In with LinkedIn using OpenID Connect" -> openid, profile, email
# - "Share on LinkedIn" -> w_member_social
# NOTE: w_organization_social (company page posting) requires "Community Management API"
#       which needs LinkedIn review. Pending approval.
SCOPES = ["openid", "profile", "email", "w_member_social"]


class LinkedInTokens:
    """Container for LinkedIn OAuth tokens."""

    def __init__(
        self,
        access_token: str,
        expires_at: Optional[float] = None,
        member_id: Optional[str] = None,
        member_name: Optional[str] = None,
        scribemd_page_id: Optional[str] = None,
    ) -> None:
        self.access_token = access_token
        self.expires_at = expires_at or (time.time() + 5_183_944)  # ~60 days
        self.member_id = member_id
        self.member_name = member_name
        self.scribemd_page_id = scribemd_page_id

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "expires_at": self.expires_at,
            "member_id": self.member_id,
            "member_name": self.member_name,
            "scribemd_page_id": self.scribemd_page_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinkedInTokens":
        return cls(
            access_token=data["access_token"],
            expires_at=data.get("expires_at"),
            member_id=data.get("member_id"),
            member_name=data.get("member_name"),
            scribemd_page_id=data.get("scribemd_page_id"),
        )


class LinkedInService:
    """Service for posting to the ScribeMD LinkedIn company page."""

    def __init__(self) -> None:
        self._tokens: Optional[LinkedInTokens] = None
        self._load_tokens()

    # ── Token management ────────────────────────────────────────────────────

    def _load_tokens(self) -> None:
        """Load tokens from config/linkedin_tokens.json."""
        if TOKENS_PATH.exists():
            try:
                with TOKENS_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tokens = LinkedInTokens.from_dict(data)
                LOGGER.info("Loaded LinkedIn tokens from %s", TOKENS_PATH)
            except Exception as exc:
                LOGGER.warning("Failed to load LinkedIn tokens: %s", exc)

    def _save_tokens(self, data: Dict[str, Any]) -> None:
        """Persist token data to disk."""
        expires_in = data.get("expires_in", 5_183_944)
        payload = {
            "access_token": data["access_token"],
            "expires_at": time.time() + expires_in - 60,
            "member_id": data.get("member_id") or (self._tokens.member_id if self._tokens else None),
            "member_name": data.get("member_name") or (self._tokens.member_name if self._tokens else None),
            "scribemd_page_id": data.get("scribemd_page_id") or self._get_page_id(),
        }
        TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TOKENS_PATH.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        self._tokens = LinkedInTokens.from_dict(payload)
        LOGGER.info("LinkedIn tokens saved to %s", TOKENS_PATH)

    # ── Auth helpers ─────────────────────────────────────────────────────────

    def build_auth_url(self, state: str = "jarvis") -> str:
        """Build LinkedIn OAuth authorization URL."""
        if not CLIENT_ID:
            raise ValueError("LINKEDIN_CLIENT_ID not configured")

        from urllib.parse import urlencode
        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "scope": " ".join(SCOPES),
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> LinkedInTokens:
        """Exchange OAuth authorization code for tokens."""
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be configured")

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()

        if "error" in data:
            raise RuntimeError(f"LinkedIn token error: {data.get('error_description', data['error'])}")

        # Fetch member profile
        access_token = data["access_token"]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                profile_resp = await client.get(
                    USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if profile_resp.status_code == 200:
                    profile = profile_resp.json()
                    data["member_name"] = profile.get("name")
                    data["member_id"] = profile.get("sub")
        except Exception as exc:
            LOGGER.warning("Could not fetch LinkedIn profile: %s", exc)

        # Auto-detect ScribeMD page ID
        page_id = await self._fetch_scribemd_page_id(access_token)
        if page_id:
            data["scribemd_page_id"] = page_id

        self._save_tokens(data)
        LOGGER.info("LinkedIn authorization complete — member: %s", data.get("member_name"))
        return self._tokens  # type: ignore[return-value]

    async def _fetch_scribemd_page_id(self, access_token: str) -> Optional[str]:
        """Fetch the ScribeMD LinkedIn page ID via Organization ACLs API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{ORG_ACLS_URL}?q=roleAssignee&role=ADMINISTRATOR"
                    "&projection=(elements*(organization~(id,localizedName)))",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "X-Restli-Protocol-Version": "2.0.0",
                    },
                )
                if resp.status_code != 200:
                    return None

                orgs = resp.json()
                elements = orgs.get("elements", [])
                for el in elements:
                    org = el.get("organization~", {})
                    name = org.get("localizedName", "")
                    org_id = str(org.get("id", ""))
                    if "scribe" in name.lower() or "scribemd" in name.lower():
                        LOGGER.info("Auto-detected ScribeMD page ID: %s", org_id)
                        return org_id
                # Fallback: first org
                if elements:
                    first = elements[0].get("organization~", {})
                    return str(first.get("id", ""))
        except Exception as exc:
            LOGGER.warning("Could not auto-detect ScribeMD page ID: %s", exc)
        return None

    def _get_page_id(self) -> Optional[str]:
        """Return page ID from tokens or env."""
        if self._tokens and self._tokens.scribemd_page_id:
            return self._tokens.scribemd_page_id
        return PAGE_ID_ENV or None

    def _get_author_urn(self) -> Optional[str]:
        """
        Return the best available author URN for posting.
        Prefers company page (organization URN) when available.
        Falls back to personal member URN (w_member_social only).
        """
        page_id = self._get_page_id()
        if page_id:
            return f"urn:li:organization:{page_id}"
        if self._tokens and self._tokens.member_id:
            return f"urn:li:person:{self._tokens.member_id}"
        return None

    # ── Post methods ─────────────────────────────────────────────────────────

    def _auth_headers(self) -> Dict[str, str]:
        if not self._tokens or not self._tokens.access_token:
            raise RuntimeError(
                "LinkedIn not authorized. Run: python scripts/linkedin_auth.py"
            )
        if self._tokens.is_expired():
            raise RuntimeError(
                "LinkedIn access token expired (~60 days). "
                "Re-run: python scripts/linkedin_auth.py"
            )
        return {
            "Authorization": f"Bearer {self._tokens.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    async def post_text(self, text: str) -> Dict[str, Any]:
        """
        Post a plain text update to LinkedIn.

        Posts as the ScribeMD company page if page_id is configured (requires
        w_organization_social / Community Management API). Falls back to posting
        as the authorized member (Akua Agyeman) using w_member_social.

        Args:
            text: The post body (LinkedIn supports up to ~3,000 chars for UGC posts)

        Returns:
            {"success": True, "post_id": "urn:li:ugcPost:...", "url": "...", "author": "..."}
        """
        author_urn = self._get_author_urn()
        if not author_urn:
            return {
                "success": False,
                "error": "LinkedIn not authorized. Run: python scripts/linkedin_auth.py",
            }

        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    UGC_POSTS_URL,
                    json=body,
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()

            post_id = resp.headers.get("x-restli-id", "")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else ""
            LOGGER.info("LinkedIn text post published: %s (author: %s)", post_id, author_urn)
            return {"success": True, "post_id": post_id, "url": post_url, "author": author_urn}

        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            LOGGER.error("LinkedIn post failed %s: %s", exc.response.status_code, error_body)
            return {"success": False, "error": f"HTTP {exc.response.status_code}: {error_body}"}
        except Exception as exc:
            LOGGER.error("LinkedIn post error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def post_article_link(
        self,
        text: str,
        url: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Post a link/article share to LinkedIn.

        Posts as the ScribeMD company page if configured, otherwise as the
        authorized member.

        Args:
            text:        Post commentary text
            url:         Link URL to share
            title:       Optional link title (auto-scraped by LinkedIn if omitted)
            description: Optional link description

        Returns:
            {"success": True, "post_id": "...", "url": "..."}
        """
        author_urn = self._get_author_urn()
        if not author_urn:
            return {
                "success": False,
                "error": "LinkedIn not authorized. Run: python scripts/linkedin_auth.py",
            }

        media: Dict[str, Any] = {"status": "READY", "originalUrl": url}
        if title:
            media["title"] = {"text": title}
        if description:
            media["description"] = {"text": description}

        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [media],
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    UGC_POSTS_URL,
                    json=body,
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()

            post_id = resp.headers.get("x-restli-id", "")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else ""
            LOGGER.info("LinkedIn article post published: %s (author: %s)", post_id, author_urn)
            return {"success": True, "post_id": post_id, "url": post_url}

        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            LOGGER.error("LinkedIn article post failed %s: %s", exc.response.status_code, error_body)
            return {"success": False, "error": f"HTTP {exc.response.status_code}: {error_body}"}
        except Exception as exc:
            LOGGER.error("LinkedIn article post error: %s", exc)
            return {"success": False, "error": str(exc)}

    async def get_page_posts(self, count: int = 10) -> Dict[str, Any]:
        """
        Fetch recent posts from the ScribeMD company page.

        Args:
            count: Number of posts to retrieve (max 50)

        Returns:
            {"success": True, "posts": [...]}
        """
        page_id = self._get_page_id()
        if not page_id:
            return {"success": False, "error": "ScribeMD page ID not configured."}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{UGC_POSTS_URL}?q=authors&authors=List(urn%3Ali%3Aorganization%3A{page_id})"
                    f"&count={min(count, 50)}",
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()
                data = resp.json()

            posts = data.get("elements", [])
            return {"success": True, "posts": posts, "total": len(posts)}

        except httpx.HTTPStatusError as exc:
            LOGGER.error("LinkedIn get posts failed %s: %s", exc.response.status_code, exc.response.text)
            return {"success": False, "error": f"HTTP {exc.response.status_code}"}
        except Exception as exc:
            LOGGER.error("LinkedIn get posts error: %s", exc)
            return {"success": False, "error": str(exc)}

    def is_authorized(self) -> bool:
        """Return True if tokens exist and are not expired."""
        return (
            self._tokens is not None
            and bool(self._tokens.access_token)
            and not self._tokens.is_expired()
        )

    def status(self) -> Dict[str, Any]:
        """Return authorization status info."""
        if not self._tokens:
            return {
                "authorized": False,
                "reason": "No tokens found. Run: python scripts/linkedin_auth.py",
            }
        if self._tokens.is_expired():
            return {
                "authorized": False,
                "reason": "Token expired. Re-run: python scripts/linkedin_auth.py",
                "expired_at": self._tokens.expires_at,
            }
        days_left = int((self._tokens.expires_at - time.time()) / 86400)
        return {
            "authorized": True,
            "member": self._tokens.member_name,
            "page_id": self._tokens.scribemd_page_id,
            "token_expires_in_days": days_left,
        }


# Singleton instance
linkedin_service = LinkedInService()
