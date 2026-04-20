"""
ContentVault service for JARVIS.

Read-only direct Supabase connector to ContentVault's database.
Provides content pipeline status and engagement metrics for CEO briefing.

Required env vars:
  CONTENTVAULT_SUPABASE_URL       e.g. https://uqggxmcdiwtgahkckkus.supabase.co
  CONTENTVAULT_SERVICE_ROLE_KEY   Supabase service role key (bypasses RLS)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)

CV_URL = os.getenv("CONTENTVAULT_SUPABASE_URL", "").rstrip("/")
CV_KEY = os.getenv("CONTENTVAULT_SERVICE_ROLE_KEY", "")


class ContentVaultService:
    """Read-only Supabase client for ContentVault content pipeline data."""

    def __init__(self) -> None:
        self._configured = bool(CV_URL and CV_KEY)
        if not self._configured:
            LOGGER.warning(
                "ContentVault not configured. "
                "Set CONTENTVAULT_SUPABASE_URL and CONTENTVAULT_SERVICE_ROLE_KEY in .env"
            )

    def is_configured(self) -> bool:
        return self._configured

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": CV_KEY,
            "Authorization": f"Bearer {CV_KEY}",
            "Content-Type": "application/json",
        }

    def _get(self, table: str, params: List[tuple]) -> List[Dict[str, Any]]:
        if not self._configured:
            return []
        try:
            url = f"{CV_URL}/rest/v1/{table}"
            with httpx.Client(timeout=10) as client:
                resp = client.get(url, headers=self._headers(), params=params)
                if resp.is_success:
                    return resp.json() or []
                LOGGER.warning("ContentVault query failed %s: %s", resp.status_code, resp.text[:200])
                return []
        except Exception as exc:
            LOGGER.error("ContentVault query error on %s: %s", table, exc)
            return []

    # ── Pipeline status ────────────────────────────────────────────────────────

    def get_pending_review(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Content items awaiting approval."""
        return self._get("content_items", [
            ("approval_status", "eq.pending_review"),
            ("order", "created_at.desc"),
            ("limit", str(limit)),
            ("select", "id,title,brand,source_type,created_at"),
        ])

    def get_recent_published(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Recently published posts."""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        return self._get("publish_log", [
            ("status", "eq.success"),
            ("published_at", f"gte.{since}"),
            ("order", "published_at.desc"),
            ("limit", str(limit)),
            ("select", "id,brand,platform,published_at,url"),
        ])

    def get_pipeline_counts(self) -> Dict[str, int]:
        """Count items at each pipeline stage."""
        stages = {
            "pending_review": "approval_status=eq.pending_review",
            "approved": "approval_status=eq.approved",
            "published": "approval_status=eq.published",
        }
        counts: Dict[str, int] = {}
        for stage, filter_str in stages.items():
            key, val = filter_str.split("=", 1)
            rows = self._get("content_items", [
                (key, val),
                ("select", "id"),
                ("limit", "1000"),
            ])
            counts[stage] = len(rows)
        return counts

    def get_top_performing(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Top performing published posts by engagement rate."""
        return self._get("post_metrics_latest", [
            ("engagement_rate", "gt.0"),
            ("order", "engagement_rate.desc"),
            ("limit", str(limit)),
            ("select", "brand,platform,url,engagement_rate,impressions,likes,published_at"),
        ])

    def get_radar_topics(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Hot content radar topics (trending suggestions)."""
        return self._get("content_radar", [
            ("status", "eq.new"),
            ("order", "trend_score.desc"),
            ("limit", str(limit)),
            ("select", "brand,topic,trend_score,suggested_platforms,expires_at"),
        ])

    # ── CEO briefing summary ───────────────────────────────────────────────────

    def get_briefing_summary(self) -> str:
        """One-paragraph ContentVault snapshot for CEO morning briefing."""
        if not self._configured:
            return "ContentVault: not configured."
        try:
            counts = self.get_pipeline_counts()
            pending = counts.get("pending_review", 0)
            approved = counts.get("approved", 0)
            published_total = counts.get("published", 0)

            recent = self.get_recent_published(days=7)
            top = self.get_top_performing(limit=3)

            lines = [f"ContentVault pipeline: {pending} pending review, {approved} approved ready, {published_total} total published."]

            if recent:
                platforms = list({r.get("platform", "") for r in recent if r.get("platform")})
                lines.append(f"  Published last 7 days: {len(recent)} posts across {', '.join(platforms[:4])}.")

            if top:
                best = top[0]
                rate = float(best.get("engagement_rate") or 0)
                lines.append(f"  Top performer: {best.get('brand','?')} on {best.get('platform','?')} at {rate:.1%} engagement.")

            return " ".join(lines)
        except Exception as exc:
            LOGGER.error("ContentVault briefing error: %s", exc)
            return "ContentVault: error fetching summary."

    def health_check(self) -> bool:
        """Return True if Supabase is reachable."""
        if not self._configured:
            return False
        rows = self._get("content_items", [("limit", "1"), ("select", "id")])
        return isinstance(rows, list)


# Singleton
contentvault_service = ContentVaultService()
