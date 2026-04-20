"""
Gmail Inbox Organizer for JARVIS.

Applies Gmail labels to incoming messages based on sender/subject rules,
creating a folder-like structure:
  📁 GMH          — Messages related to Global Medical Holdings (GMH)
  📁 Empower      — WE Empower / UN Women related mail
  📁 Bills        — Invoices, receipts, subscription charges
  📁 JARVIS/Junk  — Promotional / bulk mail (does NOT delete — just labels)

Call via:
  POST /auth/google/gmail/organize?max_messages=200
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)

# ── Label definitions ─────────────────────────────────────────────────────────
# (name, bg_color, text_color)
LABEL_DEFS: Dict[str, Tuple[str, str]] = {
    "GMH":     ("#1565c0", "#ffffff"),   # Blue
    "Empower": ("#6a1b9a", "#ffffff"),   # Purple
    "Bills":   ("#2e7d32", "#ffffff"),   # Green
    "Junk":    ("#757575", "#ffffff"),   # Grey
}

# ── Classification rules ──────────────────────────────────────────────────────
# Each rule: (label_name, [(field, contains_substring), ...])
# field can be "from", "subject", "snippet"
# All patterns are lowercase-matched

GMH_PATTERNS = [
    ("from", "globalmedicalholdingsgroup.com"),
    ("from", "globalmedicalholdingsgroup"),
    ("from", "gmhg"),
    ("subject", "gmh"),
    ("subject", "global medical holdings"),
    ("subject", "nrp"), ("subject", "neonatal resuscitation"),
    ("subject", "brenda sana"),
    ("from", "brenda"),
]

EMPOWER_PATTERNS = [
    ("from", "weempower"),
    ("from", "we-empower"),
    ("from", "unwomen"),
    ("from", "un women"),
    ("subject", "we empower"),
    ("subject", "weempower"),
    ("subject", "un women"),
    ("subject", "empower program"),
]

BILLS_PATTERNS = [
    # Cloud / SaaS
    ("from", "aws.amazon.com"), ("from", "@amazon.com"),
    ("subject", "aws"),
    ("from", "billing@supabase"), ("from", "supabase"),
    ("from", "billing@vercel"), ("from", "vercel.com"),
    ("from", "noreply@github"), ("from", "github"),
    ("from", "billing@anthropic"), ("from", "anthropic"),
    ("from", "stripe.com"), ("from", "stripe"),
    ("from", "shopify"),
    ("from", "google cloud"), ("from", "cloud.google.com"),
    ("from", "cloudflare"),
    ("from", "digitalocean"),
    ("from", "twilio"),
    # Virtual offices / mail
    ("from", "alliancevirtualoffices"), ("from", "alliance virtual"),
    ("from", "ipostal1"), ("from", "ipostal"),
    ("from", "wyoming secretary"), ("from", "start in wyoming"),
    # Other business
    ("from", "osome"),
    ("from", "xero"),
    ("from", "quickbooks"),
    ("from", "burnerapp"), ("from", "burner app"),
    # Generic signals
    ("subject", "invoice"), ("subject", "receipt"),
    ("subject", "payment confirmation"), ("subject", "order confirmation"),
    ("subject", "billing statement"), ("subject", "amount due"),
    ("subject", "subscription renewal"),
]

JUNK_PATTERNS = [
    ("from", "noreply@"), ("from", "no-reply@"),
    ("subject", "newsletter"), ("subject", "weekly digest"),
    ("subject", "unsubscribe"), ("subject", "sale ends"),
    ("subject", "50% off"), ("subject", "limited time"),
    ("subject", "don't miss"), ("subject", "just for you"),
    ("subject", "we miss you"), ("subject", "you're invited"),
]

RULE_SETS = [
    ("GMH",     GMH_PATTERNS),
    ("Empower", EMPOWER_PATTERNS),
    ("Bills",   BILLS_PATTERNS),
]
# Note: Junk is lowest priority — only applied if no other label matches


def _classify_message(subject: str, sender: str, snippet: str) -> Optional[str]:
    """
    Return the label name for this message, or None if no rule matches.
    Priority: GMH > Empower > Bills > Junk
    """
    text_map = {
        "from": sender.lower(),
        "subject": subject.lower(),
        "snippet": snippet.lower(),
    }

    for label_name, patterns in RULE_SETS:
        for field, pattern in patterns:
            if pattern in text_map.get(field, ""):
                return label_name

    # Check junk last
    for field, pattern in JUNK_PATTERNS:
        if pattern in text_map.get(field, ""):
            return "Junk"

    return None


class GmailOrganizerService:
    """
    Fetches messages, classifies them, and applies Gmail labels.
    Creates labels automatically if they don't exist.
    """

    def __init__(self) -> None:
        self._svc = None

    def _get_service(self):
        if self._svc is None:
            from app.services.email.gmail_service import gmail_service
            self._svc = gmail_service
        return self._svc

    def is_available(self) -> bool:
        try:
            return self._get_service().is_authorized()
        except Exception:
            return False

    async def _ensure_labels(self) -> Dict[str, str]:
        """
        Ensure all required labels exist. Return {name: label_id} map.
        """
        svc = self._get_service()
        label_ids: Dict[str, str] = {}
        for name, (bg, text) in LABEL_DEFS.items():
            label_id = await svc.get_or_create_label(name, bg_color=bg, text_color=text)
            if label_id:
                label_ids[name] = label_id
            else:
                LOGGER.warning("Could not get/create label: %s", name)
        return label_ids

    async def organize(self, max_messages: int = 200) -> Dict[str, Any]:
        """
        Scan recent messages, classify them, and apply labels.

        Args:
            max_messages: Max number of messages to process in one run.

        Returns:
            {
                "success": bool,
                "processed": int,
                "labeled": {"GMH": N, "Empower": N, "Bills": N, "Junk": N},
                "skipped": int,
            }
        """
        if not self.is_available():
            return {"success": False, "error": "Gmail not authorized"}

        svc = self._get_service()

        # Step 1: Ensure labels exist
        LOGGER.info("Ensuring Gmail labels exist...")
        label_ids = await self._ensure_labels()
        if not label_ids:
            return {"success": False, "error": "Failed to create Gmail labels"}

        # Step 2: Fetch recent messages (last 90 days for archival sweep)
        LOGGER.info("Fetching messages for organization sweep...")
        result = await svc.list_messages(
            query="in:anywhere -in:trash -in:spam newer_than:90d",
            max_results=max_messages,
        )
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "Failed to fetch messages")}

        message_stubs = result.get("messages", [])
        LOGGER.info("Fetched %d message stubs to classify", len(message_stubs))

        # Step 3: Get metadata + classify
        # Group message IDs by target label
        label_batches: Dict[str, List[str]] = {name: [] for name in LABEL_DEFS}
        processed = 0
        skipped = 0

        # We fetch metadata in bulk using the messages.get endpoint
        import asyncio
        client = await svc._auth_client()
        try:
            for stub in message_stubs:
                try:
                    detail_resp = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{stub['id']}",
                        params={
                            "format": "metadata",
                            "metadataHeaders": ["Subject", "From"],
                        },
                    )
                    if detail_resp.status_code != 200:
                        skipped += 1
                        continue

                    msg = detail_resp.json()
                    headers = {
                        h["name"]: h["value"]
                        for h in msg.get("payload", {}).get("headers", [])
                    }
                    subject = headers.get("Subject", "")
                    sender = headers.get("From", "")
                    snippet = msg.get("snippet", "")

                    label_name = _classify_message(subject, sender, snippet)
                    if label_name and label_name in label_ids:
                        # Only add if not already labeled
                        existing = msg.get("labelIds", [])
                        if label_ids[label_name] not in existing:
                            label_batches[label_name].append(stub["id"])
                    processed += 1

                except Exception as exc:
                    LOGGER.debug("Skipping message %s: %s", stub.get("id"), exc)
                    skipped += 1
        finally:
            await client.aclose()

        # Step 4: Batch apply labels
        labeled: Dict[str, int] = {}
        for label_name, ids in label_batches.items():
            if not ids:
                labeled[label_name] = 0
                continue
            batch_result = await svc.batch_modify_messages(
                message_ids=ids,
                add_label_ids=[label_ids[label_name]],
            )
            count = len(ids) if batch_result.get("success") else 0
            labeled[label_name] = count
            LOGGER.info("Applied label '%s' to %d messages", label_name, count)

        total_labeled = sum(labeled.values())
        LOGGER.info(
            "Inbox organization complete: %d processed, %d labeled, %d skipped",
            processed, total_labeled, skipped,
        )

        return {
            "success": True,
            "processed": processed,
            "labeled": labeled,
            "skipped": skipped,
        }


# Singleton
gmail_organizer_service = GmailOrganizerService()
