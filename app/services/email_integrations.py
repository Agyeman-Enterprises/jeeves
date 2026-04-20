from __future__ import annotations

import email as email_lib
import imaplib
import logging
import os
import re
import smtplib
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Dict, Iterable, List, Optional

import requests

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover - optional dependency
    Request = None  # type: ignore
    Credentials = None  # type: ignore
    build = None  # type: ignore

try:
    import msal
except ImportError:  # pragma: no cover - optional dependency
    msal = None  # type: ignore

LOGGER = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",  # For sending briefings
    "https://www.googleapis.com/auth/calendar.readonly",
]

GRAPH_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"


class EmailProviderError(RuntimeError):
    pass


@dataclass
class EmailMessage:
    subject: str
    sender: str
    received: datetime
    snippet: str
    account: str
    provider: str
    id: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "subject": self.subject,
            "sender": self.sender,
            "received": self.received.isoformat(),
            "snippet": self.snippet,
            "account": self.account,
            "provider": self.provider,
            "id": self.id,
        }


@dataclass
class OAuthCredentials:
    address: str
    client_id: str
    client_secret: str
    refresh_token: str


class BaseEmailProvider:
    name = "email"

    def __init__(self, credentials: OAuthCredentials) -> None:
        self.credentials = credentials

    def fetch_unread(self, max_results: int = 25) -> List[EmailMessage]:
        raise NotImplementedError

    def search(self, query: str, max_results: int = 25) -> List[EmailMessage]:
        raise NotImplementedError

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email. Returns True on success, False on failure."""
        raise NotImplementedError


class GmailProvider(BaseEmailProvider):
    name = "gmail"

    def __init__(self, credentials: OAuthCredentials) -> None:
        super().__init__(credentials)
        self._service = None

    def _service_client(self):
        if self._service:
            return self._service
        if not Credentials or not Request or not build:
            raise EmailProviderError(
                "google-api-python-client and google-auth libraries are required. "
                "Install with: pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib"
            )
        creds = Credentials(
            token=None,
            refresh_token=self.credentials.refresh_token,
            client_id=self.credentials.client_id,
            client_secret=self.credentials.client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=GMAIL_SCOPES,
        )
        if not creds.valid or creds.expired:
            creds.refresh(Request())
        self._service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        return self._service

    def fetch_unread(self, max_results: int = 25) -> List[EmailMessage]:
        service = self._service_client()
        try:
            response = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=["INBOX", "UNREAD"],
                    maxResults=max_results,
                )
                .execute()
            )
        except Exception as exc:
            raise EmailProviderError(f"Gmail fetch failed: {exc}") from exc

        messages = response.get("messages", [])
        return [self._fetch_message(service, msg["id"]) for msg in messages]

    def search(self, query: str, max_results: int = 25) -> List[EmailMessage]:
        service = self._service_client()
        try:
            response = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
        except Exception as exc:
            raise EmailProviderError(f"Gmail search failed: {exc}") from exc

        return [
            self._fetch_message(service, msg["id"]) for msg in response.get("messages", [])
        ]

    def _fetch_message(self, service, message_id: str) -> EmailMessage:
        try:
            message = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except Exception as exc:
            LOGGER.warning(f"Failed to fetch message {message_id}: {exc}")
            # Return a minimal message on error
            return EmailMessage(
                subject="(error fetching message)",
                sender=self.credentials.address,
                received=datetime.now(timezone.utc),
                snippet="",
                account=self.credentials.address,
                provider=self.name,
                id=message_id,
            )
        
        headers = {h["name"].lower(): h["value"] for h in message.get("payload", {}).get("headers", [])}

        subject = headers.get("subject", "(no subject)")
        sender = headers.get("from", self.credentials.address)
        received = headers.get("date")
        
        # Parse date with multiple format support
        received_dt = datetime.now(timezone.utc)
        if received:
            try:
                # Try standard format first
                received_dt = datetime.strptime(received, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                try:
                    # Try format without timezone
                    received_dt = datetime.strptime(received, "%a, %d %b %Y %H:%M:%S")
                    received_dt = received_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    try:
                        # Try RFC 2822 format variations
                        from email.utils import parsedate_to_datetime
                        received_dt = parsedate_to_datetime(received)
                    except (ValueError, TypeError):
                        LOGGER.warning(f"Could not parse date '{received}', using current time")
                        received_dt = datetime.now(timezone.utc)

        snippet = message.get("snippet", "")
        return EmailMessage(
            subject=subject,
            sender=sender,
            received=received_dt,
            snippet=snippet,
            account=self.credentials.address,
            provider=self.name,
            id=message_id,
        )

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email via Gmail API."""
        import base64
        from email.mime.text import MIMEText

        service = self._service_client()
        try:
            message = MIMEText(body)
            message["to"] = to
            message["from"] = self.credentials.address
            message["subject"] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            send_message = {"raw": raw_message}

            service.users().messages().send(userId="me", body=send_message).execute()
            LOGGER.info("Email sent successfully to %s: %s", to, subject)
            return True
        except Exception as exc:
            LOGGER.error("Failed to send email to %s: %s", to, exc)
            return False


class OutlookProvider(BaseEmailProvider):
    name = "outlook"

    def fetch_unread(self, max_results: int = 25) -> List[EmailMessage]:
        token = self._refresh_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"$top": max_results, "$select": "subject,from,receivedDateTime,bodyPreview"}
        try:
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages",
                headers=headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            raise EmailProviderError(f"Outlook fetch failed: {exc}") from exc

        return [self._to_message(item) for item in response.json().get("value", [])]

    def search(self, query: str, max_results: int = 25) -> List[EmailMessage]:
        token = self._refresh_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "ConsistencyLevel": "eventual",
        }
        params = {
            "$search": f"\"{query}\"",
            "$top": max_results,
            "$select": "subject,from,receivedDateTime,bodyPreview",
        }
        try:
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers=headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            raise EmailProviderError(f"Outlook search failed: {exc}") from exc

        return [self._to_message(item) for item in response.json().get("value", [])]

    def _refresh_access_token(self) -> str:
        if msal is None:
            raise EmailProviderError("msal is required. Install with: pip install msal")
        app = msal.ConfidentialClientApplication(
            self.credentials.client_id,
            authority="https://login.microsoftonline.com/common",
            client_credential=self.credentials.client_secret,
        )
        result = app.acquire_token_by_refresh_token(
            self.credentials.refresh_token,
            scopes=["https://graph.microsoft.com/.default"],
        )
        if "access_token" not in result:
            raise EmailProviderError(
                f"Outlook token refresh failed: {result.get('error_description', 'unknown error')}"
            )
        return result["access_token"]

    def _to_message(self, item: Dict[str, str]) -> EmailMessage:
        received = item.get("receivedDateTime")
        received_dt = (
            datetime.fromisoformat(received.replace("Z", "+00:00"))
            if received
            else datetime.now(timezone.utc)
        )
        sender = (
            item.get("from", {})
            .get("emailAddress", {})
            .get("address", self.credentials.address)
        )
        return EmailMessage(
            subject=item.get("subject", "(no subject)"),
            sender=sender,
            received=received_dt,
            snippet=item.get("bodyPreview", "")[:400],
            account=self.credentials.address,
            provider=self.name,
            id=item.get("id", ""),
        )

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email via Microsoft Graph API."""
        if not msal:
            LOGGER.error("msal library not installed. Cannot send email via Outlook.")
            return False

        try:
            # Get access token
            app = msal.ConfidentialClientApplication(
                client_id=self.credentials.client_id,
                client_secret=self.credentials.client_secret,
                authority="https://login.microsoftonline.com/common",
            )
            result = app.acquire_token_silent(
                scopes=["https://graph.microsoft.com/Mail.Send"], account=None
            )
            if not result:
                result = app.acquire_token_for_client(
                    scopes=["https://graph.microsoft.com/Mail.Send"]
                )

            if "access_token" not in result:
                LOGGER.error("Failed to acquire token for Outlook email send")
                return False

            # Send email via Graph API
            headers = {
                "Authorization": f"Bearer {result['access_token']}",
                "Content-Type": "application/json",
            }
            payload = {
                "message": {
                    "subject": subject,
                    "body": {"contentType": "Text", "content": body},
                    "toRecipients": [{"emailAddress": {"address": to}}],
                },
                "saveToSentItems": True,
            }

            response = requests.post(
                f"https://graph.microsoft.com/v1.0/users/{self.credentials.address}/sendMail",
                headers=headers,
                json=payload,
            )
            if response.status_code == 202:
                LOGGER.info("Email sent successfully to %s: %s", to, subject)
                return True
            else:
                LOGGER.error(
                    "Failed to send email via Outlook: %s %s",
                    response.status_code,
                    response.text,
                )
                return False
        except Exception as exc:
            LOGGER.error("Failed to send email to %s: %s", to, exc)
            return False


@dataclass
class ImapCredentials:
    address: str
    password: str
    imap_server: str = "outlook.office365.com"
    imap_port: int = 993
    smtp_server: str = "smtp.office365.com"
    smtp_port: int = 587


# IMAP server defaults by domain
_IMAP_DEFAULTS: Dict[str, Dict] = {
    "hotmail.com":  {"imap_server": "outlook.office365.com", "imap_port": 993, "smtp_server": "smtp.office365.com", "smtp_port": 587},
    "outlook.com":  {"imap_server": "outlook.office365.com", "imap_port": 993, "smtp_server": "smtp.office365.com", "smtp_port": 587},
    "live.com":     {"imap_server": "outlook.office365.com", "imap_port": 993, "smtp_server": "smtp.office365.com", "smtp_port": 587},
    "gmail.com":    {"imap_server": "imap.gmail.com",        "imap_port": 993, "smtp_server": "smtp.gmail.com",        "smtp_port": 587},
    "yahoo.com":    {"imap_server": "imap.mail.yahoo.com",   "imap_port": 993, "smtp_server": "smtp.mail.yahoo.com",   "smtp_port": 587},
}


def _imap_defaults_for(address: str) -> Dict:
    domain = address.split("@")[-1].lower() if "@" in address else ""
    return _IMAP_DEFAULTS.get(domain, {"imap_server": "outlook.office365.com", "imap_port": 993, "smtp_server": "smtp.office365.com", "smtp_port": 587})


class ImapProvider(BaseEmailProvider):
    """Read/send email via IMAP/SMTP — works with any provider using an app password."""

    name = "imap"

    def __init__(self, credentials: ImapCredentials) -> None:
        # Wrap into a compatible OAuthCredentials-like object so parent __init__ works
        self._imap_creds = credentials
        self.credentials = type("_Compat", (), {"address": credentials.address})()

    def _connect(self) -> imaplib.IMAP4_SSL:
        ctx = ssl.create_default_context()
        # Outlook's cert chain has a non-critical Basic Constraints extension that
        # Python 3.14's stricter OpenSSL rejects. Disable hostname+cert checks only
        # for known Outlook servers; the TLS channel is still encrypted.
        if "office365" in self._imap_creds.imap_server or "outlook" in self._imap_creds.imap_server:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        conn = imaplib.IMAP4_SSL(
            self._imap_creds.imap_server,
            self._imap_creds.imap_port,
            ssl_context=ctx,
        )
        # Outlook servers advertise AUTH=PLAIN but not LOGIN; use AUTHENTICATE PLAIN
        # conn.capabilities is a tuple of strings (decoded), not bytes
        # Note: imaplib.authenticate() base64-encodes the return value itself,
        # so we must pass raw bytes (not pre-encoded).
        if "AUTH=PLAIN" in conn.capabilities:
            creds = f"\x00{self._imap_creds.address}\x00{self._imap_creds.password}".encode()
            typ, data = conn.authenticate("PLAIN", lambda _: creds)
            if typ != "OK":
                raise imaplib.IMAP4.error(data)
        else:
            conn.login(self._imap_creds.address, self._imap_creds.password)
        return conn

    def fetch_unread(self, max_results: int = 25) -> List[EmailMessage]:
        try:
            conn = self._connect()
            conn.select("INBOX")
            _, data = conn.search(None, "UNSEEN")
            uids = data[0].split() if data[0] else []
            uids = uids[-max_results:]  # most recent first
            messages = [self._fetch_one(conn, uid) for uid in reversed(uids)]
            conn.logout()
            return [m for m in messages if m is not None]
        except Exception as exc:
            raise EmailProviderError(f"IMAP fetch failed ({self._imap_creds.address}): {exc}") from exc

    def search(self, query: str, max_results: int = 25) -> List[EmailMessage]:
        # IMAP search on subject — handles multi-word queries
        try:
            conn = self._connect()
            conn.select("INBOX")
            # Search subject and body separately, combine results
            results = set()
            for field_name in ("SUBJECT", "BODY"):
                # IMAP requires each word as a separate criterion or use quoted string
                safe_query = query.replace('"', "")
                _, data = conn.search(None, f'{field_name} "{safe_query}"')
                if data[0]:
                    results.update(data[0].split())
            uids = list(results)[-max_results:]
            messages = [self._fetch_one(conn, uid) for uid in uids]
            conn.logout()
            msgs = [m for m in messages if m is not None]
            msgs.sort(key=lambda m: m.received, reverse=True)
            return msgs
        except Exception as exc:
            raise EmailProviderError(f"IMAP search failed ({self._imap_creds.address}): {exc}") from exc

    def _fetch_one(self, conn: imaplib.IMAP4_SSL, uid: bytes) -> Optional[EmailMessage]:
        try:
            _, msg_data = conn.fetch(uid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject = email_lib.header.decode_header(msg.get("Subject", "(no subject)"))
            subject_str = "".join(
                part.decode(enc or "utf-8") if isinstance(part, bytes) else part
                for part, enc in subject
            )

            sender = msg.get("From", self._imap_creds.address)
            date_str = msg.get("Date", "")
            try:
                from email.utils import parsedate_to_datetime
                received_dt = parsedate_to_datetime(date_str)
            except Exception:
                received_dt = datetime.now(timezone.utc)

            # Extract plain-text snippet
            snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            snippet = payload.decode("utf-8", errors="replace")[:300]
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    snippet = payload.decode("utf-8", errors="replace")[:300]

            return EmailMessage(
                subject=subject_str.strip(),
                sender=sender,
                received=received_dt,
                snippet=snippet.strip(),
                account=self._imap_creds.address,
                provider=self.name,
                id=uid.decode(),
            )
        except Exception as exc:
            LOGGER.warning("IMAP failed to parse message %s: %s", uid, exc)
            return None

    def send_email(self, to: str, subject: str, body: str) -> bool:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self._imap_creds.address
            msg["To"] = to

            ctx = ssl.create_default_context()
            if "office365" in self._imap_creds.smtp_server or "outlook" in self._imap_creds.smtp_server:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            with smtplib.SMTP(self._imap_creds.smtp_server, self._imap_creds.smtp_port) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ctx)
                smtp.login(self._imap_creds.address, self._imap_creds.password)
                smtp.sendmail(self._imap_creds.address, [to], msg.as_string())

            LOGGER.info("IMAP/SMTP email sent to %s: %s", to, subject)
            return True
        except Exception as exc:
            LOGGER.error("IMAP/SMTP send failed: %s", exc)
            return False


def _real(value: Optional[str]) -> bool:
    """Return True only if value is a real credential (non-empty, not an inline .env comment)."""
    return bool(value) and not value.startswith("#")


class EmailIntegrationManager:
    """Loads Gmail/Outlook/IMAP providers from environment variables."""

    MAX_GMAIL_ACCOUNTS = 20
    MAX_OUTLOOK_ACCOUNTS = 12
    MAX_IMAP_ACCOUNTS = 12

    def __init__(self) -> None:
        self.providers: List[BaseEmailProvider] = []
        self._configure_gmail()
        self._configure_outlook()
        self._configure_imap()

    def _configure_gmail(self) -> None:
        for idx in range(1, self.MAX_GMAIL_ACCOUNTS + 1):
            address = os.getenv(f"GMAIL_{idx}_ADDRESS")
            client_id = os.getenv(f"GMAIL_{idx}_CLIENT_ID")
            client_secret = os.getenv(f"GMAIL_{idx}_CLIENT_SECRET")
            refresh_token = os.getenv(f"GMAIL_{idx}_REFRESH_TOKEN")
            if all([_real(address), _real(client_id), _real(client_secret), _real(refresh_token)]):
                creds = OAuthCredentials(
                    address=address,
                    client_id=client_id,
                    client_secret=client_secret,
                    refresh_token=refresh_token,
                )
                self.providers.append(GmailProvider(creds))

    def _configure_outlook(self) -> None:
        for idx in range(1, self.MAX_OUTLOOK_ACCOUNTS + 1):
            address = os.getenv(f"OUTLOOK_{idx}_ADDRESS")
            client_id = os.getenv(f"OUTLOOK_{idx}_CLIENT_ID")
            client_secret = os.getenv(f"OUTLOOK_{idx}_CLIENT_SECRET")
            refresh_token = os.getenv(f"OUTLOOK_{idx}_REFRESH_TOKEN")
            if all([_real(address), _real(client_id), _real(client_secret), _real(refresh_token)]):
                creds = OAuthCredentials(
                    address=address,
                    client_id=client_id,
                    client_secret=client_secret,
                    refresh_token=refresh_token,
                )
                self.providers.append(OutlookProvider(creds))

    def _configure_imap(self) -> None:
        for idx in range(1, self.MAX_IMAP_ACCOUNTS + 1):
            address = os.getenv(f"IMAP_{idx}_ADDRESS")
            password = os.getenv(f"IMAP_{idx}_PASSWORD")
            if not (_real(address) and _real(password)):
                continue
            defaults = _imap_defaults_for(address)
            creds = ImapCredentials(
                address=address,
                password=password,
                imap_server=os.getenv(f"IMAP_{idx}_SERVER", defaults["imap_server"]),
                imap_port=int(os.getenv(f"IMAP_{idx}_PORT", defaults["imap_port"])),
                smtp_server=os.getenv(f"IMAP_{idx}_SMTP_SERVER", defaults["smtp_server"]),
                smtp_port=int(os.getenv(f"IMAP_{idx}_SMTP_PORT", defaults["smtp_port"])),
            )
            self.providers.append(ImapProvider(creds))
            LOGGER.info("IMAP provider loaded: %s", address)

    def has_providers(self) -> bool:
        return bool(self.providers)

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email using the first available provider.
        Returns True if sent successfully, False otherwise.
        """
        if not self.providers:
            LOGGER.warning("No email providers configured. Cannot send email.")
            return False

        # Try each provider until one succeeds
        for provider in self.providers:
            try:
                if provider.send_email(to, subject, body):
                    return True
            except Exception as exc:
                LOGGER.warning("Provider %s failed to send email: %s", provider.name, exc)
                continue

        LOGGER.error("All email providers failed to send email to %s", to)
        return False

    def fetch_unread(self, max_results: int = 25) -> List[EmailMessage]:
        messages: List[EmailMessage] = []
        for provider in self.providers:
            try:
                provider_messages = provider.fetch_unread(max_results=max_results)
                messages.extend(provider_messages)
            except EmailProviderError as exc:
                LOGGER.warning("%s fetch failed: %s", provider.name, exc)
            except Exception as exc:
                LOGGER.error("%s fetch failed with unexpected error: %s", provider.name, exc, exc_info=True)
        messages.sort(key=lambda msg: msg.received, reverse=True)
        return messages

    def search(self, query: str, max_results: int = 25) -> List[EmailMessage]:
        messages: List[EmailMessage] = []
        for provider in self.providers:
            try:
                messages.extend(provider.search(query, max_results=max_results))
            except EmailProviderError as exc:
                LOGGER.warning("%s search failed: %s", provider.name, exc)
        messages.sort(key=lambda msg: msg.received, reverse=True)
        return messages


