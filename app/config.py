"""
Jeeves/JJ Configuration — All env-driven, no local-only assumptions.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration from environment variables."""

    # ── Identity ───────────────────────────────────────────────────────
    app_name: str = "JJ"
    version: str = "2.0.0"
    debug: bool = False

    # ── Auth ───────────────────────────────────────────────────────────
    api_key: str = ""  # JEEVES_API_KEY — required for all requests

    # ── Supabase (JJ state + preferences) ─────────────────────────────
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # ── LLM (thinking) ─────────────────────────────────────────────────
    litellm_base_url: str = "https://ai.agyemanenterprises.com"
    litellm_api_key: str = ""
    litellm_model: str = "ollama/deepseek-r1:32b"
    anthropic_api_key: str = ""
    fallback_model: str = "claude-sonnet-4-20250514"

    # ── Aqui (memory) ──────────────────────────────────────────────────
    aqui_base_url: str = "https://aqui.agyemanenterprises.com"
    aqui_api_key: str = ""

    # ── Nexus (business intelligence) ──────────────────────────────────
    nexus_base_url: str = "https://nexus-eight-gold.vercel.app"
    nexus_internal_key: str = ""

    # ── Ghexit (communications) ────────────────────────────────────────
    ghexit_base_url: str = "https://ghexit.agyemanenterprises.com"
    ghexit_service_token: str = ""

    # ── AlrtMe (push notifications) ────────────────────────────────────
    alrtme_api_key: str = ""
    alrtme_channel: str = "akualrts"
    alrtme_base_url: str = "https://alrtme.co"

    # ── Google (Gmail + Calendar) ──────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    google_calendar_id: str = "primary"

    # ── AAA contact ────────────────────────────────────────────────────
    owner_phone: str = "+18083213384"
    owner_email: str = "isaalia@gmail.com"

    # ── Scheduling (Guam timezone) ─────────────────────────────────────
    timezone: str = "Pacific/Guam"
    morning_hour: int = 7
    checkin_hour: int = 18   # 6pm check-in
    reflection_hour: int = 23

    # ── GitHub ─────────────────────────────────────────────────────────
    github_token: str = ""
    github_org: str = "Agyeman-Enterprises"

    class Config:
        env_prefix = "JEEVES_"
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
