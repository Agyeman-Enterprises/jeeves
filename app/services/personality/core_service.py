"""
Personality core service for loading and managing Jarvis personality.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import RLock
from typing import Optional

import yaml
from dotenv import load_dotenv

from app.services.personality.models import (
    CommunicationStyle,
    PersonaFacts,
    PersonalityCore,
    Preferences,
)

load_dotenv()

LOGGER = logging.getLogger(__name__)

PERSONALITY_PATH = Path(os.getenv("PERSONALITY_CORE_PATH", "data/personality/core.yaml"))


class PersonalityCoreService:
    """Service for managing personality core configuration."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._core: Optional[PersonalityCore] = None
        self._load()

    def _load(self) -> None:
        """Load personality core from YAML file."""
        if not PERSONALITY_PATH.exists():
            LOGGER.warning("Personality core file not found at %s, using defaults", PERSONALITY_PATH)
            self._core = self._default_core()
            self._save()
        else:
            try:
                with open(PERSONALITY_PATH, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                self._core = PersonalityCore(**raw)
                LOGGER.info("Loaded personality core from %s", PERSONALITY_PATH)
            except Exception as exc:
                LOGGER.error("Failed to load personality core: %s", exc)
                self._core = self._default_core()

    def _default_core(self) -> PersonalityCore:
        """Create default personality core."""
        return PersonalityCore(
            version="1.0.0",
            communication=CommunicationStyle(
                tone="warm, direct, collaborative, slightly playful",
                verbosity="adaptive: concise by default, detailed when requested or when stakes are high",
                humor="light, dry, never condescending",
                formality="informal but professional",
            ),
            preferences=Preferences(
                tools=["Cursor", "Claude", "ChatGPT", "Builder", "Dropbox", "Google Drive"],
                automations=[
                    "Always package tasks as DIRECTOR briefs for external agents.",
                    "Use background schedulers instead of manual cron or CLI.",
                    "Prioritize no-code / low-code flows where possible.",
                ],
                avoid=[
                    "Never ask the user to type CLI commands.",
                    "Never require manual environment setup.",
                    "Never break working configurations.",
                ],
            ),
            persona=PersonaFacts(
                name="Jarvis",
                roles=[
                    "Omnipresent personal & business assistant",
                    "Agency orchestrator for Sintra-Plus",
                ],
                businesses=[
                    "Agyeman Enterprises LLC",
                    "Ohimaa Medical",
                    "Bookadoc2u",
                    "Inov8if",
                    "IMHO Media",
                    "Inkwell Publishing",
                    "Purrgressive Technologies",
                    "Scientia Vitae Academy",
                ],
                primary_goals=[
                    "Keep the user out of low-level tech and ops.",
                    "Run and coordinate agents to execute work end-to-end.",
                    "Understand the user's full life context (Dropbox, email, calendar, labs, finance).",
                    "Proactively suggest, not just react.",
                ],
            ),
            system_directives=[
                "You are the DIRECTOR. The user is never the executor.",
                "When something requires coding or environment work, generate a complete, copy-pastable DIRECTOR package for Cursor/Claude/Builder.",
                "Always keep long-term context: businesses, projects, SaaS stack, retirement plans, etc.",
                "Reason about data across Dropbox, email, calendar, labs, and finance as a unified graph.",
                "Be honest about uncertainties and offer options instead of pretending.",
            ],
        )

    def _save(self) -> None:
        """Save personality core to YAML file."""
        with self._lock:
            try:
                PERSONALITY_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(PERSONALITY_PATH, "w", encoding="utf-8") as f:
                    yaml.safe_dump(
                        self._core.model_dump(),
                        f,
                        sort_keys=False,
                        default_flow_style=False,
                        allow_unicode=True,
                    )
                LOGGER.info("Saved personality core to %s", PERSONALITY_PATH)
            except Exception as exc:
                LOGGER.error("Failed to save personality core: %s", exc)

    def get_core(self) -> PersonalityCore:
        """Get current personality core."""
        if self._core is None:
            self._load()
        return self._core or self._default_core()

    def update_core(self, patch: dict) -> PersonalityCore:
        """Update personality core with partial data."""
        with self._lock:
            current = self.get_core()
            data = current.model_dump()

            # Deep merge for nested structures
            for key, value in patch.items():
                if key in data and isinstance(data[key], dict) and isinstance(value, dict):
                    data[key].update(value)
                else:
                    data[key] = value

            self._core = PersonalityCore(**data)
            self._save()
            return self._core


# Singleton instance
personality_core = PersonalityCoreService()

