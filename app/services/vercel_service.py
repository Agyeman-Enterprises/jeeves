"""
Vercel Service — check deployment status for all portfolio apps.

Requires env vars:
  VERCEL_TOKEN  — Vercel API token (vercel.com → Settings → Tokens)

API docs: https://vercel.com/docs/rest-api
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)

VERCEL_API_BASE = "https://api.vercel.com"

# Known status values returned by the Vercel API
DEPLOYMENT_STATUSES = {"READY", "ERROR", "BUILDING", "CANCELED", "QUEUED", "INITIALIZING"}


class VercelService:
    """
    Read-only Vercel integration for deployment health monitoring.
    """

    def __init__(self) -> None:
        self._token: str = os.getenv("VERCEL_TOKEN", "")

        if not self._token:
            LOGGER.warning(
                "VERCEL_TOKEN not set — VercelService disabled. "
                "Create a token at https://vercel.com/account/tokens"
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

    def get_deployment_status(
        self, project_ids: Optional[List[str]] = None, limit: int = 50
    ) -> Dict[str, Dict[str, Any]]:
        """
        Return the most recent deployment status per project.

        Args:
            project_ids: Optional list of project IDs or slugs to filter.
                         If None, returns all accessible deployments.
            limit:       Max deployments to fetch from the API (default: 50)

        Returns:
            {
                project_name: {
                    "status": "READY" | "ERROR" | "BUILDING" | "CANCELED",
                    "url": str,
                    "created_at": str (ISO-8601),
                    "error": str | None,
                }
            }
        """
        if not self.enabled:
            return {}

        try:
            deployments = self._list_deployments(project_ids=project_ids, limit=limit)
        except Exception as exc:
            LOGGER.warning("VercelService.get_deployment_status failed: %s", exc)
            return {}

        # Keep only the most recent deployment per project
        latest: Dict[str, Dict[str, Any]] = {}

        for dep in deployments:
            project_name = (
                dep.get("name")
                or dep.get("projectId", "unknown")
            )
            if project_name in latest:
                continue  # Already have the most recent for this project

            error_info: Optional[str] = None
            if dep.get("errorCode") or dep.get("errorMessage"):
                error_info = dep.get("errorMessage") or dep.get("errorCode")

            # created_at comes back as a Unix ms timestamp
            created_ts = dep.get("createdAt") or dep.get("created")
            created_iso: Optional[str] = None
            if isinstance(created_ts, int):
                try:
                    created_iso = datetime.fromtimestamp(
                        created_ts / 1000, tz=timezone.utc
                    ).isoformat()
                except Exception:
                    created_iso = str(created_ts)
            elif isinstance(created_ts, str):
                created_iso = created_ts

            url = dep.get("url") or dep.get("alias", [None])[0] if dep.get("alias") else None
            if url and not url.startswith("http"):
                url = f"https://{url}"

            latest[project_name] = {
                "status": dep.get("state") or dep.get("readyState") or "UNKNOWN",
                "url": url,
                "created_at": created_iso,
                "error": error_info,
            }

        return latest

    def get_failed_deployments(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Return deployments that errored or were canceled in the last N hours.

        Args:
            hours: Look-back window (default: 24)

        Returns:
            List of {project_name, status, url, created_at, error}
        """
        if not self.enabled:
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            # Fetch a larger batch so we can filter by time
            deployments = self._list_deployments(limit=100)
        except Exception as exc:
            LOGGER.warning("VercelService.get_failed_deployments failed: %s", exc)
            return []

        failed: List[Dict[str, Any]] = []

        for dep in deployments:
            state = dep.get("state") or dep.get("readyState") or ""
            if state not in ("ERROR", "CANCELED"):
                continue

            created_ts = dep.get("createdAt") or dep.get("created")
            if isinstance(created_ts, int):
                try:
                    created_dt = datetime.fromtimestamp(created_ts / 1000, tz=timezone.utc)
                    if created_dt < cutoff:
                        continue
                    created_iso: Optional[str] = created_dt.isoformat()
                except Exception:
                    created_iso = str(created_ts)
            elif isinstance(created_ts, str):
                created_iso = created_ts
                try:
                    created_dt = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
                    if created_dt < cutoff:
                        continue
                except Exception:
                    pass
            else:
                created_iso = None

            project_name = dep.get("name") or dep.get("projectId", "unknown")
            url = dep.get("url")
            if url and not url.startswith("http"):
                url = f"https://{url}"

            failed.append(
                {
                    "project_name": project_name,
                    "status": state,
                    "url": url,
                    "created_at": created_iso,
                    "error": dep.get("errorMessage") or dep.get("errorCode"),
                }
            )

        # Sort newest-first
        failed.sort(key=lambda d: d.get("created_at") or "", reverse=True)
        return failed

    def format_briefing_section(self, hours: int = 24) -> str:
        """Formatted markdown for CEO morning briefing."""
        if not self.enabled:
            return "## Vercel Deployments\n\n_Not configured — set VERCEL_TOKEN._\n"

        status_map = self.get_deployment_status()
        failed = self.get_failed_deployments(hours=hours)

        ready_count = sum(1 for v in status_map.values() if v["status"] == "READY")
        error_count = sum(1 for v in status_map.values() if v["status"] == "ERROR")
        building_count = sum(1 for v in status_map.values() if v["status"] == "BUILDING")

        lines = ["## Vercel Deployment Status", ""]
        lines.append(
            f"**{ready_count} ready** | **{error_count} errored** | {building_count} building"
            f" | **{len(failed)} failed in last {hours}h**"
        )
        lines.append("")

        if failed:
            lines.append(f"### Failed Deployments (last {hours}h)")
            for dep in failed:
                ts = dep.get("created_at", "")[:16] if dep.get("created_at") else "unknown time"
                err = f" — {dep['error']}" if dep.get("error") else ""
                lines.append(f"- **{dep['project_name']}** ({dep['status']}) at {ts}{err}")
            lines.append("")

        errored_projects = [
            (name, info) for name, info in status_map.items() if info["status"] == "ERROR"
        ]
        if errored_projects:
            lines.append("### Projects in Error State")
            for name, info in errored_projects:
                err = f" — {info['error']}" if info.get("error") else ""
                lines.append(f"- **{name}**: {info.get('url', 'no url')}{err}")

        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _list_deployments(
        self,
        project_ids: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch deployments from the Vercel API, optionally filtered by project IDs."""
        if project_ids:
            all_deps: List[Dict[str, Any]] = []
            for pid in project_ids:
                params: Dict[str, Any] = {"projectId": pid, "limit": limit}
                data = self._get("/v6/deployments", params=params)
                all_deps.extend(data.get("deployments", []))
            return all_deps

        params = {"limit": limit}
        data = self._get("/v6/deployments", params=params)
        return data.get("deployments", [])

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{VERCEL_API_BASE}{path}"
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
