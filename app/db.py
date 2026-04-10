"""
Database layer — Supabase client.
Single connection, used by all modules.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


@lru_cache()
def get_db() -> Optional[Client]:
    """Get Supabase client. Returns None if not configured."""
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_role_key:
        LOGGER.warning("Supabase not configured — running in memory-only mode")
        return None
    try:
        return create_client(s.supabase_url, s.supabase_service_role_key)
    except Exception as exc:
        LOGGER.error("Failed to create Supabase client: %s", exc)
        return None
