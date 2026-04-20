"""
Unified email models for Gmail and Outlook.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Provider = Literal["gmail", "outlook"]


class EmailAddress(BaseModel):
    """Email address with optional display name."""

    name: Optional[str] = None
    address: str


class EmailMessage(BaseModel):
    """Unified email message model."""

    id: str
    thread_id: Optional[str] = None
    provider: Provider
    account: str  # which actual email address
    subject: str
    body_text: str
    body_html: Optional[str] = None
    from_: EmailAddress = Field(alias="from")
    to: List[EmailAddress] = []
    cc: List[EmailAddress] = []
    bcc: List[EmailAddress] = []
    date: datetime
    is_unread: bool = True
    is_important: bool = False
    labels: List[str] = []
    attachments: List[Dict] = []
    raw_metadata: Dict = {}

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

