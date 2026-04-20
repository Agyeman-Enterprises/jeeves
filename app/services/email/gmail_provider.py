"""
Gmail provider for unified email service.
Uses Google API with OAuth token management.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from app.services.email.models import EmailAddress, EmailMessage, Provider

load_dotenv()

LOGGER = logging.getLogger(__name__)

# Try to import Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    LOGGER.warning("Google API libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Configuration
GMAIL_TOKEN_PATH = Path(os.getenv("GMAIL_TOKEN_PATH", "data/gmail_tokens.json"))
GMAIL_CREDENTIALS_PATH = Path(os.getenv("GMAIL_CREDENTIALS_PATH", "config/gmail_credentials.json"))
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.send"]
LOOKBACK_DAYS = int(os.getenv("EMAIL_SYNC_LOOKBACK_DAYS", "30"))


class GmailProvider:
    """Gmail provider for unified email service."""

    def __init__(self) -> None:
        self.service = None
        self.credentials = None
        self._init_service()

    def _init_service(self) -> None:
        """Initialize Gmail API service with OAuth."""
        if not GOOGLE_API_AVAILABLE:
            LOGGER.warning("Google API libraries not available")
            return

        try:
            creds = None
            if GMAIL_TOKEN_PATH.exists():
                creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    LOGGER.warning("Gmail credentials not found or invalid. Please run OAuth flow.")
                    return

                # Save refreshed credentials
                GMAIL_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(GMAIL_TOKEN_PATH, "w") as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.service = build("gmail", "v1", credentials=creds)
            LOGGER.info("Gmail provider initialized successfully")
        except Exception as exc:
            LOGGER.error("Failed to initialize Gmail provider: %s", exc)

    def _parse_email_address(self, header_value: str) -> EmailAddress:
        """Parse email address from Gmail header."""
        if "<" in header_value and ">" in header_value:
            name = header_value.split("<")[0].strip().strip('"')
            address = header_value.split("<")[1].split(">")[0].strip()
            return EmailAddress(name=name if name else None, address=address)
        return EmailAddress(address=header_value.strip())

    def _parse_address_list(self, header_value: str) -> List[EmailAddress]:
        """Parse list of email addresses from header."""
        if not header_value:
            return []
        addresses = []
        for addr in header_value.split(","):
            addresses.append(self._parse_email_address(addr.strip()))
        return addresses

    def _parse_message(self, msg_data: dict, account: str) -> EmailMessage:
        """Parse Gmail message into unified EmailMessage."""
        payload = msg_data.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        # Extract body
        body_text = ""
        body_html = None

        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                data = part.get("body", {}).get("data", "")
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    if mime_type == "text/plain":
                        body_text = decoded
                    elif mime_type == "text/html":
                        body_html = decoded
        else:
            # Single part message
            mime_type = payload.get("mimeType", "")
            data = payload.get("body", {}).get("data", "")
            if data:
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                if mime_type == "text/html":
                    body_html = decoded
                else:
                    body_text = decoded

        # Parse date
        date_str = headers.get("Date", "")
        try:
            from email.utils import parsedate_to_datetime
            date = parsedate_to_datetime(date_str) if date_str else datetime.now(timezone.utc)
        except Exception:
            date = datetime.now(timezone.utc)

        # Parse labels
        labels = msg_data.get("labelIds", [])

        return EmailMessage(
            id=msg_data["id"],
            thread_id=msg_data.get("threadId"),
            provider="gmail",
            account=account,
            subject=headers.get("Subject", ""),
            body_text=body_text or (msg_data.get("snippet", "") if not body_html else ""),
            body_html=body_html,
            from_=self._parse_email_address(headers.get("From", "")),
            to=self._parse_address_list(headers.get("To", "")),
            cc=self._parse_address_list(headers.get("Cc", "")),
            bcc=self._parse_address_list(headers.get("Bcc", "")),
            date=date,
            is_unread="UNREAD" in labels,
            is_important="IMPORTANT" in labels,
            labels=labels,
            raw_metadata=msg_data,
        )

    def list_messages(self, query: Optional[str] = None, max_results: int = 50) -> List[EmailMessage]:
        """List messages from Gmail."""
        if not self.service:
            LOGGER.warning("Gmail service not initialized")
            return []

        try:
            # Build query with lookback
            lookback_date = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y/%m/%d")
            date_query = f"after:{lookback_date}"
            full_query = f"{date_query} {query}" if query else date_query

            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=full_query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            email_messages = []

            for msg in messages:
                try:
                    msg_data = (
                        self.service.users()
                        .messages()
                        .get(userId="me", id=msg["id"], format="full")
                        .execute()
                    )
                    # Extract account from message (for now, use "me")
                    account = "me"  # Could be enhanced to detect actual email address
                    email_messages.append(self._parse_message(msg_data, account))
                except Exception as exc:
                    LOGGER.warning("Failed to fetch message %s: %s", msg["id"], exc)
                    continue

            return email_messages
        except HttpError as exc:
            LOGGER.error("Gmail API error: %s", exc)
            return []
        except Exception as exc:
            LOGGER.error("Failed to list Gmail messages: %s", exc)
            return []

    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        """Get a specific message by ID."""
        if not self.service:
            return None

        try:
            msg_data = (
                self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
            )
            return self._parse_message(msg_data, "me")
        except Exception as exc:
            LOGGER.error("Failed to get Gmail message %s: %s", message_id, exc)
            return None

    def search(self, query: str, max_results: int = 50) -> List[EmailMessage]:
        """Search messages with Gmail query syntax."""
        return self.list_messages(query=query, max_results=max_results)

    def send_message(
        self,
        from_addr: str,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> str:
        """Send an email via Gmail."""
        if not self.service:
            raise RuntimeError("Gmail service not initialized")

        try:
            message = MIMEMultipart("alternative")
            message["to"] = ", ".join(to)
            message["subject"] = subject
            message["from"] = from_addr

            message.attach(MIMEText(body_text, "plain"))
            if body_html:
                message.attach(MIMEText(body_html, "html"))

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            send_message = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            LOGGER.info("Gmail message sent: %s", send_message["id"])
            return send_message["id"]
        except Exception as exc:
            LOGGER.error("Failed to send Gmail message: %s", exc)
            raise

