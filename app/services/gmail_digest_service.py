"""
Gmail Urgent Digest Service for JARVIS.

Scans recent unread Gmail messages, categorizes them by urgency,
and sends an HTML digest email to JARVIS_BRIEFING_EMAIL every few hours.

Categories:
  🚨 Needs Action    — payment failures, account at risk, action required
  ⚠️ Professional   — legal, compliance, HR, deadlines, appointments
  💳 Bills           — receipts, invoices, renewals, subscriptions
  📋 FYI             — newsletters, notifications, promotions

Env vars:
  JARVIS_BRIEFING_EMAIL   — digest recipient (default: isaalia@gmail.com)
  GMAIL_DIGEST_SCAN_HOURS — how many hours back to scan (default: 4)
"""

from __future__ import annotations

import base64
import logging
import os
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

# ── Config ────────────────────────────────────────────────────────────────────
DIGEST_RECIPIENT = os.getenv("JARVIS_BRIEFING_EMAIL", "isaalia@gmail.com")
DIGEST_SCAN_HOURS = int(os.getenv("GMAIL_DIGEST_SCAN_HOURS", "4"))

# ── Classification keyword patterns ──────────────────────────────────────────
URGENT_PATTERNS = [
    "payment failed", "payment decline", "past due", "overdue", "declined",
    "account suspended", "account at risk", "service disruption", "action required",
    "unable to charge", "failed to charge", "card declined", "payment unsuccessful",
    "could not process", "your payment was not", "your payment could not",
    "verification required", "verify your account", "confirm your",
    "important notice", "legal notice", "compliance", "kyc", "id verification",
    "reappointment", "renewal required", "respond by", "respond before",
    "urgent", "immediately", "as soon as possible",
    "your service will be", "deactivated", "blocked", "restricted", "final notice",
    "last chance", "will be suspended", "access revoked",
]

PROFESSIONAL_PATTERNS = [
    "interview", "application", "offer letter", "contract", "reappointment",
    "notice period", "employment", "onboarding", "human resources",
    "legal", "court", "attorney", "lawsuit", "regulation", "regulatory",
    "compliance", "kyc", "audit", "inspection", "certification",
    "approval needed", "requires your attention", "response required",
    "please review", "sign here", "notary", "official notice",
    "credentialing", "privileging", "medical staff", "license renewal",
    "board", "bylaws", "privileged", "peer review",
    "devin", "github permissions", "organization invite",
]

BILL_PATTERNS = [
    "invoice", "receipt", "payment confirmation", "order confirmation",
    "subscription renewal", "billing statement", "your statement", "amount due",
    "balance due", "new charge", "your charge", "charged to",
    "aws", "amazon web services", "google cloud", "supabase", "shopify",
    "anthropic", "vercel", "github", "digitalocean", "cloudflare",
    "stripe", "twilio", "sendgrid", "hubspot",
    "alliance virtual", "ipostal", "burner app", "start in wyoming",
    "osome", "xero", "quickbooks", "irs", "tax return",
    "comcast", "verizon", "at&t", "t-mobile", "utility bill",
]


class GmailDigestService:
    """
    Scans Gmail for unread messages, categorizes by urgency,
    and emails a clean HTML digest.
    """

    def __init__(self) -> None:
        self._svc = None  # Lazy import to avoid circular dependency

    def _get_service(self):
        """Lazily load the gmail_service singleton."""
        if self._svc is None:
            from app.services.email.gmail_service import gmail_service
            self._svc = gmail_service
        return self._svc

    def is_available(self) -> bool:
        """Return True if Gmail OAuth tokens are loaded and not expired."""
        try:
            return self._get_service().is_authorized()
        except Exception:
            return False

    # ── Classification ────────────────────────────────────────────────────────

    def _classify(self, subject: str, snippet: str, sender: str) -> str:
        """
        Classify a message into: urgent | professional | bill | fyi

        Checks subject + snippet + sender against keyword lists in priority order.
        """
        text = f"{subject} {snippet} {sender}".lower()
        for pat in URGENT_PATTERNS:
            if pat in text:
                return "urgent"
        for pat in PROFESSIONAL_PATTERNS:
            if pat in text:
                return "professional"
        for pat in BILL_PATTERNS:
            if pat in text:
                return "bill"
        return "fyi"

    # ── Gmail API helpers ─────────────────────────────────────────────────────

    async def _fetch_unread_recent(self, hours: int) -> List[Dict]:
        """
        Return metadata for unread messages received in the last `hours` hours.
        Uses Gmail search: is:unread newer_than:{hours}h
        """
        svc = self._get_service()
        client = await svc._auth_client()
        results = []

        try:
            list_resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/messages",
                params={"q": f"is:unread newer_than:{hours}h", "maxResults": 50},
            )
            list_resp.raise_for_status()
            stubs = list_resp.json().get("messages", [])
            LOGGER.debug("Found %d unread stubs", len(stubs))

            for stub in stubs:
                try:
                    detail = await client.get(
                        f"{GMAIL_API_BASE}/users/me/messages/{stub['id']}",
                        params={
                            "format": "metadata",
                            "metadataHeaders": ["Subject", "From", "Date"],
                        },
                    )
                    if detail.status_code == 200:
                        results.append(detail.json())
                except Exception as exc:
                    LOGGER.debug("Skipping msg %s: %s", stub.get("id"), exc)

        except Exception as exc:
            LOGGER.error("Gmail fetch_unread_recent error: %s", exc)
        finally:
            await client.aclose()

        return results

    @staticmethod
    def _parse_meta(msg: Dict) -> Dict[str, str]:
        """Extract display fields from a raw Gmail metadata response."""
        headers = {
            h["name"]: h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }
        return {
            "id": msg.get("id", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        }

    # ── HTML builder ──────────────────────────────────────────────────────────

    @staticmethod
    def _email_row(m: Dict) -> str:
        subj = m["subject"][:80]
        sender = m["from"][:60]
        snip = m["snippet"][:130]
        url = f"https://mail.google.com/mail/u/0/#inbox/{m['id']}"
        return (
            f"<tr>"
            f"<td style='padding:9px 10px;border-bottom:1px solid #f0f0f0'>"
            f"<a href='{url}' style='color:#1a73e8;font-weight:600;"
            f"text-decoration:none;font-size:13px'>{subj}</a>"
            f"<br><span style='color:#555;font-size:12px'>{sender}</span>"
            f"<br><span style='color:#888;font-size:12px'>{snip}</span>"
            f"</td></tr>"
        )

    def _section_html(
        self, emoji: str, title: str, color: str, items: List[Dict]
    ) -> str:
        if not items:
            return ""
        rows = "".join(self._email_row(m) for m in items)
        return (
            f"<div style='margin-bottom:28px'>"
            f"<h2 style='font-size:14px;font-weight:700;color:{color};"
            f"margin:0 0 10px 0;border-left:4px solid {color};"
            f"padding-left:10px;line-height:1.4'>"
            f"{emoji} {title} &nbsp;<span style='font-weight:400;opacity:0.7'>"
            f"({len(items)})</span></h2>"
            f"<table style='width:100%;border-collapse:collapse'>{rows}</table>"
            f"</div>"
        )

    def _build_html(
        self,
        urgent: List,
        professional: List,
        bills: List,
        fyi: List,
        generated_at: str,
        hours: int,
    ) -> str:
        total = len(urgent) + len(professional) + len(bills) + len(fyi)

        sections = (
            self._section_html("🚨", "Needs Action — Fix These First", "#c62828", urgent)
            + self._section_html("⚠️", "Professional / Time-Sensitive", "#e65100", professional)
            + self._section_html("💳", "Bills & Subscriptions", "#1565c0", bills)
            + self._section_html("📋", "FYI", "#555", fyi)
        )

        if not sections:
            sections = (
                "<p style='color:#888;font-size:14px;text-align:center;padding:20px 0'>"
                "✅ Inbox clear — no new unread messages in the last scan window.</p>"
            )

        urgent_badge = (
            f"<span style='background:#c62828;color:#fff;border-radius:12px;"
            f"padding:2px 8px;font-size:11px;margin-left:8px'>"
            f"{len(urgent)} urgent</span>"
            if urgent
            else ""
        )

        return f"""<!DOCTYPE html>
<html>
<head><meta charset='utf-8'><meta name='viewport' content='width=device-width'></head>
<body style='font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
             max-width:700px;margin:0 auto;padding:20px 16px;
             color:#333;background:#f5f5f5'>

  <!-- Header -->
  <div style='background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);
              color:#fff;padding:20px 24px;border-radius:10px;margin-bottom:24px'>
    <div style='font-size:20px;font-weight:800;letter-spacing:-0.5px'>
      ⚡ JARVIS Inbox Digest {urgent_badge}
    </div>
    <div style='font-size:12px;opacity:0.6;margin-top:6px'>
      {generated_at} &nbsp;·&nbsp; Scanned last {hours}h
      &nbsp;·&nbsp; {total} new messages
    </div>
  </div>

  <!-- Body -->
  <div style='background:#fff;border-radius:8px;padding:24px 20px;
              box-shadow:0 1px 3px rgba(0,0,0,0.08)'>
    {sections}
  </div>

  <!-- Footer -->
  <div style='text-align:center;font-size:11px;color:#bbb;margin-top:18px'>
    JARVIS Auto-Digest · Runs every {hours}h
    &nbsp;·&nbsp;
    <a href='https://mail.google.com' style='color:#bbb'>Open Gmail</a>
  </div>

</body>
</html>"""

    # ── Send email ────────────────────────────────────────────────────────────

    async def _send_digest_email(self, subject: str, html: str) -> bool:
        """Build a MIME HTML message and send it via Gmail API."""
        svc = self._get_service()
        client = await svc._auth_client()
        try:
            msg = MIMEMultipart("alternative")
            msg["to"] = DIGEST_RECIPIENT
            msg["from"] = f"JARVIS <{DIGEST_RECIPIENT}>"
            msg["subject"] = subject
            msg.attach(MIMEText("Please view this in an HTML-capable mail client.", "plain"))
            msg.attach(MIMEText(html, "html"))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/messages/send",
                json={"raw": raw},
            )
            resp.raise_for_status()
            LOGGER.info(
                "Gmail digest sent to %s (id: %s)",
                DIGEST_RECIPIENT,
                resp.json().get("id"),
            )
            return True
        except Exception as exc:
            LOGGER.error("Failed to send Gmail digest email: %s", exc)
            return False
        finally:
            await client.aclose()

    # ── Public entrypoint ─────────────────────────────────────────────────────

    async def run_digest(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch unread messages for the last `hours` hours, categorize,
        build HTML digest, and send it to DIGEST_RECIPIENT.

        Args:
            hours: Hours to scan back. Falls back to GMAIL_DIGEST_SCAN_HOURS env var.

        Returns:
            {
                "success": bool,
                "sent_to": str,
                "total": int,
                "categories": {"urgent": int, "professional": int, "bills": int, "fyi": int}
            }
        """
        if not self.is_available():
            LOGGER.warning("Gmail digest skipped — not authorized")
            return {
                "success": False,
                "error": "Gmail not authorized. Complete OAuth flow at /auth/gmail/init",
            }

        hours = hours or DIGEST_SCAN_HOURS

        # 1. Fetch
        raw_messages = await self._fetch_unread_recent(hours=hours)
        LOGGER.info("Digest: %d unread messages fetched (last %dh)", len(raw_messages), hours)

        # 2. Parse + classify
        urgent, professional, bills, fyi = [], [], [], []
        for raw in raw_messages:
            meta = self._parse_meta(raw)
            category = self._classify(meta["subject"], meta["snippet"], meta["from"])
            if category == "urgent":
                urgent.append(meta)
            elif category == "professional":
                professional.append(meta)
            elif category == "bill":
                bills.append(meta)
            else:
                fyi.append(meta)

        total = len(urgent) + len(professional) + len(bills) + len(fyi)

        # 3. Build email
        now = datetime.now(timezone.utc)
        generated_at = now.strftime("%d %b %Y %H:%M UTC")

        urgency_prefix = f"🚨 {len(urgent)} urgent — " if urgent else ""
        subject = (
            f"⚡ JARVIS Digest — {urgency_prefix}{total} total "
            f"— {now.strftime('%d %b %H:%M')}"
        )

        html = self._build_html(urgent, professional, bills, fyi, generated_at, hours)

        # 4. Send
        sent = await self._send_digest_email(subject, html)

        return {
            "success": sent,
            "sent_to": DIGEST_RECIPIENT,
            "total": total,
            "categories": {
                "urgent": len(urgent),
                "professional": len(professional),
                "bills": len(bills),
                "fyi": len(fyi),
            },
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
gmail_digest_service = GmailDigestService()
