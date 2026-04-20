"""
Sentry Service — read error counts and new issues across all portfolio apps.

Requires env vars:
  SENTRY_AUTH_TOKEN  — Sentry auth token (Settings → Auth Tokens)
  SENTRY_ORG         — Sentry organization slug (e.g. "agyeman-enterprises")

API docs: https://docs.sentry.io/api/
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)

SENTRY_API_BASE = "https://sentry.io/api/0"


class SentryService:
    """
    Read-only Sentry integration for error monitoring across the app portfolio.
    """

    def __init__(self) -> None:
        self._token: str = os.getenv("SENTRY_AUTH_TOKEN", "")
        self._org: str = os.getenv("SENTRY_ORG", "")

        if not self._token:
            LOGGER.warning(
                "SENTRY_AUTH_TOKEN not set — SentryService disabled. "
                "Generate a token at https://sentry.io/settings/account/api/auth-tokens/"
            )
            self.enabled = False
            return

        if not self._org:
            LOGGER.warning(
                "SENTRY_ORG not set — SentryService disabled. "
                "Set SENTRY_ORG to your organization slug (e.g. 'agyeman-enterprises')."
            )
            self.enabled = False
            return

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            }
        )
        self.enabled = True

    def is_enabled(self) -> bool:
        return self.enabled

    # ── Public methods ────────────────────────────────────────────────────────

    def get_error_summary(self) -> Dict[str, Dict[str, int]]:
        """
        Return error counts per project, bucketed by level.

        Returns:
            {
                "project-slug": {
                    "critical_count": int,
                    "error_count": int,
                    "warning_count": int,
                }
            }
        """
        if not self.enabled:
            return {}

        try:
            projects = self._get_projects()
        except Exception as exc:
            LOGGER.warning("SentryService.get_error_summary failed to list projects: %s", exc)
            return {}

        summary: Dict[str, Dict[str, int]] = {}

        for project in projects:
            slug = project.get("slug", "unknown")
            try:
                issues = self._get_issues(slug)
                counts: Dict[str, int] = {"critical_count": 0, "error_count": 0, "warning_count": 0}
                for issue in issues:
                    level = issue.get("level", "error").lower()
                    if level == "critical" or level == "fatal":
                        counts["critical_count"] += 1
                    elif level == "error":
                        counts["error_count"] += 1
                    elif level in ("warning", "warn"):
                        counts["warning_count"] += 1
                summary[slug] = counts
            except Exception as exc:
                LOGGER.warning("SentryService: failed to fetch issues for project %s: %s", slug, exc)
                summary[slug] = {"critical_count": 0, "error_count": 0, "warning_count": 0}

        return summary

    def get_new_issues(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Return issues first seen within the last N hours across all projects.

        Args:
            hours: Look back window in hours (default: 24)

        Returns:
            List of issue dicts with keys: id, title, project, level, count, first_seen, last_seen
        """
        if not self.enabled:
            return []

        try:
            projects = self._get_projects()
        except Exception as exc:
            LOGGER.warning("SentryService.get_new_issues failed to list projects: %s", exc)
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        new_issues: List[Dict[str, Any]] = []

        for project in projects:
            slug = project.get("slug", "unknown")
            try:
                issues = self._get_issues(slug, query="firstSeen:>-{}h".format(hours))
                for issue in issues:
                    first_seen_str = issue.get("firstSeen", "")
                    if first_seen_str:
                        try:
                            first_seen = datetime.fromisoformat(
                                first_seen_str.replace("Z", "+00:00")
                            )
                            if first_seen < cutoff:
                                continue
                        except ValueError:
                            pass  # Include if we can't parse the date

                    new_issues.append(
                        {
                            "id": issue.get("id"),
                            "title": issue.get("title", "(no title)"),
                            "project": slug,
                            "level": issue.get("level", "error"),
                            "count": issue.get("count", 0),
                            "first_seen": issue.get("firstSeen"),
                            "last_seen": issue.get("lastSeen"),
                            "permalink": issue.get("permalink"),
                        }
                    )
            except Exception as exc:
                LOGGER.warning("SentryService: failed to fetch new issues for %s: %s", slug, exc)

        # Sort by level severity then recency
        level_order = {"fatal": 0, "critical": 1, "error": 2, "warning": 3, "info": 4, "debug": 5}
        new_issues.sort(key=lambda i: (level_order.get(i["level"], 99), i.get("first_seen") or ""))

        return new_issues

    def format_briefing_section(self, hours: int = 24) -> str:
        """Formatted markdown for CEO morning briefing."""
        if not self.enabled:
            return "## Sentry Errors\n\n_Not configured — set SENTRY_AUTH_TOKEN and SENTRY_ORG._\n"

        summary = self.get_error_summary()
        new_issues = self.get_new_issues(hours=hours)

        total_critical = sum(v["critical_count"] for v in summary.values())
        total_errors = sum(v["error_count"] for v in summary.values())
        total_warnings = sum(v["warning_count"] for v in summary.values())

        lines = ["## Sentry Error Summary", ""]
        lines.append(
            f"**{total_critical} critical** | **{total_errors} errors** | {total_warnings} warnings "
            f"| **{len(new_issues)} new in last {hours}h**"
        )
        lines.append("")

        if new_issues:
            lines.append(f"### New Issues (last {hours}h)")
            for issue in new_issues[:10]:
                level = issue["level"].upper()
                lines.append(f"- [{level}] **{issue['project']}** — {issue['title']} (seen {issue['count']}x)")

        projects_with_criticals = [
            (slug, counts) for slug, counts in summary.items() if counts["critical_count"] > 0
        ]
        if projects_with_criticals:
            lines.append("")
            lines.append("### Projects with Critical Errors")
            for slug, counts in sorted(projects_with_criticals, key=lambda x: -x[1]["critical_count"]):
                lines.append(f"- **{slug}**: {counts['critical_count']} critical, {counts['error_count']} errors")

        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{SENTRY_API_BASE}{path}"
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _get_projects(self) -> List[Dict[str, Any]]:
        """List all projects in the organisation."""
        return self._get(f"/organizations/{self._org}/projects/") or []

    def _get_issues(
        self, project_slug: str, query: str = "is:unresolved", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch open issues for a project."""
        params = {
            "query": query,
            "limit": limit,
            "project": project_slug,
        }
        result = self._get(f"/organizations/{self._org}/issues/", params=params)
        return result if isinstance(result, list) else []
