"""
Resend Service — send transactional emails via the Resend API.

Requires env vars:
  RESEND_API_KEY    — Resend API key (resend.com → API Keys)
  RESEND_FROM_EMAIL — Sender address (default: jarvis@agyemanenterprises.com)

API docs: https://resend.com/docs/api-reference/emails/send-email
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import requests

LOGGER = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
_DEFAULT_FROM = "JARVIS <onboarding@resend.dev>"


class ResendService:
    """
    Email delivery via Resend.  Falls back to structured logging when
    RESEND_API_KEY is absent — never silently drops messages.
    """

    def __init__(self) -> None:
        self._api_key: str = os.getenv("RESEND_API_KEY", "")
        self._default_from: str = os.getenv("RESEND_FROM_EMAIL", _DEFAULT_FROM)

        if not self._api_key:
            LOGGER.warning(
                "RESEND_API_KEY not set — ResendService will LOG emails instead of sending. "
                "Get a free key at https://resend.com/api-keys"
            )
            self.enabled = False
        else:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }
            )
            self.enabled = True

    def is_enabled(self) -> bool:
        return self.enabled

    # ── Public methods ────────────────────────────────────────────────────────

    def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        from_addr: Optional[str] = None,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a transactional email.

        Args:
            to:        Recipient email address
            subject:   Email subject line
            html:      HTML body of the email
            from_addr: Sender address (defaults to RESEND_FROM_EMAIL env var)
            text:      Plain-text fallback (optional but recommended)
            reply_to:  Reply-to address (optional)

        Returns:
            {"id": str, "success": bool, "error": str | None}
        """
        sender = from_addr or self._default_from

        if not self.enabled:
            LOGGER.info(
                "[ResendService — NO API KEY] EMAIL WOULD HAVE BEEN SENT\n"
                "  From:    %s\n"
                "  To:      %s\n"
                "  Subject: %s\n"
                "  Body:    %s",
                sender,
                to,
                subject,
                html[:500] + ("..." if len(html) > 500 else ""),
            )
            return {"id": None, "success": False, "error": "RESEND_API_KEY not configured"}

        payload: Dict[str, Any] = {
            "from": sender,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if text:
            payload["text"] = text
        if reply_to:
            payload["reply_to"] = reply_to

        try:
            resp = self._session.post(RESEND_API_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            email_id = data.get("id")
            LOGGER.info("Email sent via Resend — id=%s to=%s subject=%s", email_id, to, subject)
            return {"id": email_id, "success": True, "error": None}

        except requests.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.response.json().get("message", exc.response.text)
            except Exception:
                error_body = str(exc)
            LOGGER.error(
                "ResendService.send_email HTTP error %s: %s",
                exc.response.status_code,
                error_body,
            )
            return {"id": None, "success": False, "error": error_body}

        except Exception as exc:
            LOGGER.error("ResendService.send_email failed: %s", exc)
            return {"id": None, "success": False, "error": str(exc)}

    def send_briefing(
        self,
        to: str,
        subject: str,
        body_html: str,
        from_addr: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience wrapper for morning CEO briefings.

        Wraps the HTML body in a minimal responsive email shell so it renders
        cleanly in Gmail/Outlook without any external template dependency.

        Args:
            to:        Recipient email address
            subject:   Email subject (e.g. "JARVIS Daily Briefing — 2026-03-18")
            body_html: Pre-rendered HTML content (markdown → html is caller's job)
            from_addr: Override sender (optional)

        Returns:
            Same as send_email()
        """
        wrapped = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{subject}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #f5f5f5; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 700px; margin: 32px auto; background: #fff;
               border-radius: 8px; padding: 32px 40px;
               box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    h1 {{ font-size: 20px; color: #1a1a1a; margin-bottom: 4px; }}
    h2 {{ font-size: 16px; color: #222; border-bottom: 1px solid #eee;
          padding-bottom: 6px; margin-top: 28px; }}
    h3 {{ font-size: 14px; color: #444; margin-top: 20px; }}
    p, li {{ font-size: 14px; color: #333; line-height: 1.6; }}
    .footer {{ margin-top: 40px; font-size: 12px; color: #999;
               border-top: 1px solid #eee; padding-top: 16px; }}
    code {{ background: #f0f0f0; padding: 2px 5px; border-radius: 3px;
            font-size: 13px; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <h1>{subject}</h1>
    <div class="body-content">
      {body_html}
    </div>
    <div class="footer">
      Generated by JARVIS &mdash; Agyeman Enterprises AI Chief of Staff
    </div>
  </div>
</body>
</html>"""

        return self.send_email(
            to=to,
            subject=subject,
            html=wrapped,
            from_addr=from_addr,
        )
