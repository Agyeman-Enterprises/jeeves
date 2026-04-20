"""
Personality core models for Jarvis.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class CommunicationStyle(BaseModel):
    """Communication style preferences."""

    tone: str
    verbosity: str
    humor: str
    formality: str


class Preferences(BaseModel):
    """User preferences for tools and automations."""

    tools: List[str]
    automations: List[str]
    avoid: List[str]


class PersonaFacts(BaseModel):
    """Persona and identity facts."""

    name: str
    roles: List[str]
    businesses: List[str]
    primary_goals: List[str]


class PersonalityCore(BaseModel):
    """Complete personality core configuration."""

    version: str
    communication: CommunicationStyle
    preferences: Preferences
    persona: PersonaFacts
    system_directives: List[str]

