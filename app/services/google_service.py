"""
Google Service — Gmail + Calendar integration for JJ.

JJ reads AAA's email to:
- Surface what needs a response
- Learn from communication patterns
- Detect schedule changes, deadlines, opportunities

JJ reads Calendar to:
- Know when shifts are
- Protect recovery time
- Suggest schedule reshuffles
- Build energy profile for the day

Auth: Uses stored OAuth refresh token from environment.
Tokens are refreshed automatically.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from app.config import get_settings

LOGGER = logging.getLogger(__name__)

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1"
_CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"


class GoogleService:
    """
    Handles Gmail and Google Calendar on behalf of AAA.
    All calls are read-only by default — JJ observes and suggests,
    never modifies without explicit approval.
    """

    def __init__(self):
        s = get_settings()
        self._client_id = s.google_client_id
        self._client_secret = s.google_client_secret
        self._refresh_token = s.google_refresh_token
        self._calendar_id = s.google_calendar_id
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    # ── Auth ───────────────────────────────────────────────────────────

    async def _get_access_token(self) -> Optional[str]:
        """Refresh and return a valid access token."""
        if not self._refresh_token:
            LOGGER.warning("[Google] No refresh token configured.")
            return None

        # Return cached token if still valid (with 60s buffer)
        if (
            self._access_token
            and self._token_expiry
            and datetime.now(tz=timezone.utc) < self._token_expiry - timedelta(seconds=60)
        ):
            return self._access_token

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    _GOOGLE_TOKEN_URL,
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "refresh_token": self._refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
                LOGGER.info("[Google] Access token refreshed. Expires in %ds.", expires_in)
                return self._access_token
        except Exception as exc:
            LOGGER.error("[Google] Token refresh failed: %s", exc)
            return None

    def _auth_headers(self, token: str) -> Dict:
        return {"Authorization": f"Bearer {token}"}

    # ── Gmail ──────────────────────────────────────────────────────────

    async def get_unread_emails(
        self, max_results: int = 20, hours_back: int = 24
    ) -> List[Dict]:
        """
        Fetch unread emails from the last N hours.
        Returns summarised metadata — JJ never stores full email body.
        """
        token = await self._get_access_token()
        if not token:
            return []

        try:
            # Build query: unread, recent
            after_epoch = int(
                (datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)).timestamp()
            )
            query = f"is:unread after:{after_epoch}"

            async with httpx.AsyncClient(timeout=20) as client:
                # List message IDs
                list_resp = await client.get(
                    f"{_GMAIL_BASE}/users/me/messages",
                    headers=self._auth_headers(token),
                    params={"q": query, "maxResults": max_results},
                )
                list_resp.raise_for_status()
                messages = list_resp.json().get("messages", [])

                if not messages:
                    return []

                # Fetch metadata for each message
                emails = []
                for msg in messages[:max_results]:
                    try:
                        detail_resp = await client.get(
                            f"{_GMAIL_BASE}/users/me/messages/{msg['id']}",
                            headers=self._auth_headers(token),
                            params={"format": "metadata",
                                    "metadataHeaders": ["From", "Subject", "Date"]},
                        )
                        detail_resp.raise_for_status()
                        data = detail_resp.json()
                        headers = {
                            h["name"]: h["value"]
                            for h in data.get("payload", {}).get("headers", [])
                        }
                        snippet = data.get("snippet", "")
                        emails.append({
                            "id": msg["id"],
                            "from": headers.get("From", "Unknown"),
                            "subject": headers.get("Subject", "(no subject)"),
                            "date": headers.get("Date", ""),
                            "snippet": snippet[:200],
                            "labels": data.get("labelIds", []),
                        })
                    except Exception as exc:
                        LOGGER.warning("[Google] Email detail fetch failed: %s", exc)
                        continue

                LOGGER.info("[Google] Fetched %d unread emails.", len(emails))
                return emails

        except Exception as exc:
            LOGGER.warning("[Google] Gmail fetch failed: %s", exc)
            return []

    async def get_emails_needing_response(self, hours_back: int = 48) -> List[Dict]:
        """
        Surface emails that likely need a response.
        Filters: unread + from a real person (not automated).
        """
        all_unread = await self.get_unread_emails(hours_back=hours_back)
        # Filter out automated senders
        skip_patterns = [
            "noreply", "no-reply", "donotreply", "notifications@",
            "alerts@", "newsletter", "unsubscribe", "mailer-daemon",
        ]
        needs_response = []
        for email in all_unread:
            sender = email.get("from", "").lower()
            if not any(p in sender for p in skip_patterns):
                needs_response.append(email)

        return needs_response

    # ── Calendar ───────────────────────────────────────────────────────

    async def get_todays_events(self) -> List[Dict]:
        """Get today's calendar events in Guam time."""
        return await self.get_events_for_range(days_ahead=0, days_back=0)

    async def get_events_for_range(
        self, days_back: int = 0, days_ahead: int = 7
    ) -> List[Dict]:
        """
        Fetch calendar events for a date range.
        Used for schedule awareness, shift detection, free time identification.
        """
        token = await self._get_access_token()
        if not token:
            return []

        try:
            now = datetime.now(tz=timezone.utc)
            time_min = (now - timedelta(days=days_back)).isoformat()
            time_max = (now + timedelta(days=days_ahead)).isoformat()

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{_CALENDAR_BASE}/calendars/{self._calendar_id}/events",
                    headers=self._auth_headers(token),
                    params={
                        "timeMin": time_min,
                        "timeMax": time_max,
                        "singleEvents": True,
                        "orderBy": "startTime",
                        "maxResults": 50,
                    },
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])

                events = []
                for item in items:
                    start = item.get("start", {})
                    end = item.get("end", {})
                    events.append({
                        "id": item.get("id", ""),
                        "summary": item.get("summary", "(untitled)"),
                        "description": item.get("description", "")[:200],
                        "start": start.get("dateTime", start.get("date", "")),
                        "end": end.get("dateTime", end.get("date", "")),
                        "location": item.get("location", ""),
                        "is_all_day": "date" in start and "dateTime" not in start,
                    })

                LOGGER.info("[Google] Fetched %d calendar events.", len(events))
                return events

        except Exception as exc:
            LOGGER.warning("[Google] Calendar fetch failed: %s", exc)
            return []

    def detect_shifts(self, events: List[Dict]) -> List[Dict]:
        """
        Identify hospital shifts from calendar events.
        Looks for GMH, shift, hospital, call keywords.
        """
        shift_keywords = ["gmh", "shift", "hospital", "call", "on call", "guam memorial"]
        return [
            e for e in events
            if any(kw in e.get("summary", "").lower() for kw in shift_keywords)
            or any(kw in e.get("description", "").lower() for kw in shift_keywords)
        ]

    def get_free_blocks(
        self, events: List[Dict], min_hours: float = 1.5
    ) -> List[Dict]:
        """
        Identify free blocks of time between events.
        Used for: swim suggestions, creative work, meals, rest.
        """
        if not events:
            return [{"start": "09:00", "end": "21:00", "hours": 12.0, "label": "Open day"}]

        # Parse and sort by start time
        parsed = []
        for e in events:
            start_str = e.get("start", "")
            end_str = e.get("end", "")
            if "T" in start_str:
                try:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    parsed.append((start_dt, end_dt, e.get("summary", "")))
                except ValueError:
                    continue

        parsed.sort(key=lambda x: x[0])

        # Find gaps
        free_blocks = []
        for i in range(len(parsed) - 1):
            gap_start = parsed[i][1]
            gap_end = parsed[i + 1][0]
            gap_hours = (gap_end - gap_start).total_seconds() / 3600
            if gap_hours >= min_hours:
                free_blocks.append({
                    "start": gap_start.strftime("%H:%M"),
                    "end": gap_end.strftime("%H:%M"),
                    "hours": round(gap_hours, 1),
                    "label": f"Free {round(gap_hours, 1)}h block",
                })

        return free_blocks

    async def health(self) -> bool:
        """Check if Google credentials are valid."""
        token = await self._get_access_token()
        return token is not None
