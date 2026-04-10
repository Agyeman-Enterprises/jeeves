"""
Jeeves Configuration — All env-driven, no local-only assumptions.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration from environment variables."""

    # ── Identity ───────────────────────────────────────────────────────
    app_name: str = "Jeeves"
    version: str = "1.0.0"
    debug: bool = False

    # ── Auth ───────────────────────────────────────────────────────────
    api_key: str = ""  # JEEVES_API_KEY — required for all requests

    # ── Supabase (persistence) ─────────────────────────────────────────
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # ── LLM (thinking) ─────────────────────────────────────────────────
    litellm_base_url: str = "https://ai.agyemanenterprises.com"
    litellm_api_key: str = ""
    litellm_model: str = "ollama/deepseek-r1:32b"
    # Fallback to Anthropic if local is down
    anthropic_api_key: str = ""
    fallback_model: str = "claude-sonnet-4-20250514"

    # ── Aqui (memory) ──────────────────────────────────────────────────
    aqui_base_url: str = "https://aqui.agyemanenterprises.com"
    aqui_api_key: str = ""

    # ── Nexus (business intelligence) ──────────────────────────────────
    nexus_base_url: str = "https://nexus.agyemanenterprises.com"
    nexus_internal_key: str = ""

    # ── Ghexit (communications) ────────────────────────────────────────
    ghexit_base_url: str = "https://ghexit.agyemanenterprises.com"
    ghexit_service_token: str = ""

    # ── Vector (OCR/indexing) ──────────────────────────────────────────
    vector_base_url: str = ""  # Not yet deployed as service

    # ── AlrtMe (SMS) ───────────────────────────────────────────────────
    alrtme_api_key: str = ""
    alrtme_channel: str = "akualrts"
    alrtme_base_url: str = "https://alrtme.co"

    # ── Akua contact ───────────────────────────────────────────────────
    owner_phone: str = "+18083213384"
    owner_email: str = "isaalia@gmail.com"

    # ── Scheduling ─────────────────────────────────────────────────────
    timezone: str = "Pacific/Guam"
    morning_hour: int = 7
    evening_hour: int = 18
    reflection_hour: int = 23

    # ── GitHub (repo scanning) ─────────────────────────────────────────
    github_token: str = ""
    github_org: str = "Agyeman-Enterprises"

    class Config:
        env_prefix = "JEEVES_"
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
