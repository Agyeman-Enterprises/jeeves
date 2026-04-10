"""
Schedule Schema — Day plans, interventions, and time blocks.
"""

from __future__ import annotations

from datetime import datetime, time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class InterventionType(str, Enum):
    ASK = "ask"               # Ask a question to learn
    REMIND = "remind"         # Gentle nudge
    RESCHEDULE = "reschedule" # Move something
    ESCALATE = "escalate"     # Urgent flag
    DELEGATE = "delegate"     # Send to Nexus/Ghexit/agent
    STAY_QUIET = "stay_quiet" # Jeeves decides to not bother Akua


class TimeBlock(BaseModel):
    start: datetime
    end: datetime
    label: str
    category: str = "work"  # work, health, creative, admin, rest
    linked_goal: Optional[str] = None
    is_fixed: bool = False  # hospital shifts, appointments = fixed
    source: str = "jeeves"  # jeeves, calendar, amion


class DayPlan(BaseModel):
    date: str  # YYYY-MM-DD
    blocks: List[TimeBlock] = Field(default_factory=list)
    top_priorities: List[str] = Field(default_factory=list)  # goal_ids in order
    what_to_drop: List[str] = Field(default_factory=list)
    what_to_ask: List[str] = Field(default_factory=list)
    energy_profile: str = "unknown"  # post_shift_low, normal, high
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Intervention(BaseModel):
    intervention_type: InterventionType
    target_goal: Optional[str] = None
    message: str
    urgency: float = 0.5  # 0-1
    channel: str = "pwa"  # pwa, sms, push, email
    scheduled_for: Optional[datetime] = None
    delivered: bool = False
    response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
