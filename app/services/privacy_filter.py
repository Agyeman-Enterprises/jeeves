from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, List

LOGGER = logging.getLogger(__name__)

SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EIN_PATTERN = re.compile(r"\b\d{2}-\d{7}\b")
LICENSE_PATTERN = re.compile(r"\b[A-Z]{1,2}\d{6,8}\b")
ACCOUNT_PATTERN = re.compile(r"\b\d{8,12}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+1[-\s.]?)?\(?\d{3}\)?[-\s.]?\d{3}[-\s.]?\d{4}\b")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

SENSITIVE_KEYWORDS = [
    "phi",
    "patient",
    "ssn",
    "social security",
    "driver license",
    "dea",
    "license number",
    "api key",
    "password",
    "routing number",
    "account number",
    "bank account",
    "hipaa",
    "pii",
]


class PrivacyViolation(Exception):
    """Raised when content fails privacy validation."""


class PrivacyFilter:
    """
    Lightweight privacy scanner that keeps PHI/PII from leaving the machine.
    """

    def __init__(self, custom_keywords: Iterable[str] | None = None) -> None:
        self.keywords = set(SENSITIVE_KEYWORDS)
        if custom_keywords:
            self.keywords.update(kw.lower() for kw in custom_keywords)

    def contains_sensitive(self, text: str) -> bool:
        lowered = text.lower()
        for keyword in self.keywords:
            if keyword in lowered:
                return True
        for pattern in (
            SSN_PATTERN,
            EIN_PATTERN,
            LICENSE_PATTERN,
            ACCOUNT_PATTERN,
            PHONE_PATTERN,
            EMAIL_PATTERN,
        ):
            if pattern.search(text):
                return True
        return False

    def scrub(self, text: str) -> str:
        scrubbed = SSN_PATTERN.sub("[REDACTED-SSN]", text)
        scrubbed = EIN_PATTERN.sub("[REDACTED-EIN]", scrubbed)
        scrubbed = LICENSE_PATTERN.sub("[REDACTED-LICENSE]", scrubbed)
        scrubbed = ACCOUNT_PATTERN.sub("[REDACTED-ACCOUNT]", scrubbed)
        scrubbed = PHONE_PATTERN.sub("[REDACTED-PHONE]", scrubbed)
        scrubbed = EMAIL_PATTERN.sub("[REDACTED-EMAIL]", scrubbed)
        return scrubbed

    def validate_payload(self, payload: Dict[str, Any]) -> None:
        for value in self._walk_payload(payload):
            if isinstance(value, str) and self.contains_sensitive(value):
                LOGGER.warning("Payload blocked by privacy filter")
                raise PrivacyViolation("Payload contains sensitive data.")

    def _walk_payload(self, payload: Any) -> Iterable[str]:
        if isinstance(payload, dict):
            for value in payload.values():
                yield from self._walk_payload(value)
        elif isinstance(payload, list):
            for item in payload:
                yield from self._walk_payload(item)
        elif isinstance(payload, str):
            yield payload


