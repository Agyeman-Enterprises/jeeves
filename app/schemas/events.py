"""
Event Schema — Every input becomes a normalized event.
Voice notes, typed logs, OCR, calendar events, emails, SMS, app telemetry.
All flow through this one schema.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventSource(str, Enum):
    VOICE = "voice"
    TEXT = "text"
    SMS = "sms"
    EMAIL = "email"
    CALENDAR = "calendar"
    OCR = "ocr"
    FILE = "file"
    REPO = "repo"
    APP_TELEMETRY = "app_telemetry"
    CHECKIN = "checkin"
    AQUI = "aqui"
    NEXUS = "nexus"
    MANUAL = "manual"


class EventModality(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    STRUCTURED = "structured"


class NormalizedEvent(BaseModel):
    """Every input to Jeeves becomes one of these."""
    id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: EventSource
    modality: EventModality = EventModality.TEXT
    raw_text: str
    structured_payload: Dict[str, Any] = Field(default_factory=dict)
    entities: List[str] = Field(default_factory=list)  # people, projects, apps mentioned
    duration_minutes: Optional[float] = None
    linked_goals: List[str] = Field(default_factory=list)
    valence: float = 0.0  # -1 negative, 0 neutral, 1 positive
    arousal: float = 0.0  # 0 calm, 1 intense
    certainty: float = 0.5  # how sure we are about this event's interpretation
    inferred_tags: List[str] = Field(default_factory=list)
    self_reported_intent: Optional[str] = None
    inferred_intent: Optional[str] = None
