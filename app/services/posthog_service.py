"""
PostHog Service — read analytics data (DAU, top pages) per app.

Requires env vars:
  POSTHOG_API_KEY   — PostHog personal API key (Project Settings → Personal API Keys)
  POSTHOG_HOST      — PostHog host (default: https://app.posthog.com)

API docs: https://posthog.com/docs/api
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)

_DEFAULT_HOST = "https://app.posthog.com"


class PostHogService:
    """
    Read-only PostHog integration for analytics across the app portfolio.
    """

    def __init__(self) -> None:
        self._api_key: str = os.getenv("POSTHOG_API_KEY", "")
        self._host: str = os.getenv("POSTHOG_HOST", _DEFAULT_HOST).rstrip("/")

        if not self._api_key:
            LOGGER.warning(
                "POSTHOG_API_KEY not set — PostHogService disabled. "
                "Create a personal API key at %s/settings/user-api-keys",
                self._host,
            )
            self.enabled = False
            return

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )
        self.enabled = True

    def is_enabled(self) -> bool:
        return self.enabled

    # ── Public methods ────────────────────────────────────────────────────────

    def list_projects(self) -> List[Dict[str, Any]]:
        """Return all PostHog projects accessible with this API key."""
        if not self.enabled:
            return []
        try:
            data = self._get("/api/projects/")
            return data.get("results", []) if isinstance(data, dict) else []
        except Exception as exc:
            LOGGER.warning("PostHogService.list_projects failed: %s", exc)
            return []

    def get_daily_active_users(self, days: int = 7) -> Dict[str, float]:
        """
        Return the average Daily Active Users for each project over the last N days.

        Args:
            days: Number of days to average over (default: 7)

        Returns:
            {project_name: avg_dau}
        """
        if not self.enabled:
            return {}

        projects = self.list_projects()
        if not projects:
            return {}

        result: Dict[str, float] = {}
        date_from = f"-{days}d"

        for project in projects:
            project_id = project.get("id")
            project_name = project.get("name", f"project_{project_id}")
            if not project_id:
                continue

            try:
                insight_data = self._post(
                    f"/api/projects/{project_id}/insights/trend/",
                    json={
                        "events": [{"id": "$pageview", "math": "dau"}],
                        "date_from": date_from,
                        "interval": "day",
                    },
                )
                # Extract the DAU values from the trend results
                results = insight_data.get("result", [])
                if results:
                    data_points = results[0].get("data", [])
                    if data_points:
                        avg_dau = sum(data_points) / len(data_points)
                        result[project_name] = round(avg_dau, 1)
                    else:
                        result[project_name] = 0.0
                else:
                    result[project_name] = 0.0
            except Exception as exc:
                LOGGER.warning(
                    "PostHogService: failed to fetch DAU for project %s (%s): %s",
                    project_name,
                    project_id,
                    exc,
                )
                result[project_name] = 0.0

        return result

    def get_top_pages(self, project_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Return the top N pages by pageview count for a given project.

        Args:
            project_id: PostHog numeric project ID
            limit: Number of top pages to return (default: 5)

        Returns:
            List of {pathname: str, count: int}
        """
        if not self.enabled:
            return []

        try:
            insight_data = self._post(
                f"/api/projects/{project_id}/insights/trend/",
                json={
                    "events": [{"id": "$pageview", "math": "total"}],
                    "breakdown": "$current_url",
                    "date_from": "-7d",
                    "interval": "day",
                },
            )
            results = insight_data.get("result", [])
            pages: List[Dict[str, Any]] = []

            for item in results:
                url = item.get("breakdown_value", "")
                total = sum(item.get("data", []))
                if url and total > 0:
                    # Strip domain — keep only pathname for brevity
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        pathname = parsed.path or url
                    except Exception:
                        pathname = url
                    pages.append({"pathname": pathname, "count": total})

            # Sort descending and trim
            pages.sort(key=lambda x: -x["count"])
            return pages[:limit]

        except Exception as exc:
            LOGGER.warning(
                "PostHogService.get_top_pages failed for project %s: %s", project_id, exc
            )
            return []

    def get_total_dau(self, days: int = 7) -> float:
        """Return summed DAU across all projects — useful for CEO briefing headline."""
        dau_map = self.get_daily_active_users(days=days)
        return round(sum(dau_map.values()), 1)

    def format_briefing_section(self, days: int = 7) -> str:
        """Formatted markdown for CEO morning briefing."""
        if not self.enabled:
            return "## PostHog Analytics\n\n_Not configured — set POSTHOG_API_KEY._\n"

        dau_map = self.get_daily_active_users(days=days)
        total_dau = sum(dau_map.values())

        lines = ["## PostHog Analytics", ""]
        lines.append(f"**Total avg DAU (last {days}d): {round(total_dau, 1)}**")
        lines.append("")

        if dau_map:
            lines.append("### DAU by App")
            for name, avg in sorted(dau_map.items(), key=lambda x: -x[1]):
                lines.append(f"- **{name}**: {avg} avg/day")
        else:
            lines.append("_No project data available._")

        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self._host}{path}"
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self._host}{path}"
        resp = self._session.post(url, json=json, timeout=20)
        resp.raise_for_status()
        return resp.json()
