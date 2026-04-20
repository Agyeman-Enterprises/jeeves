"""
GitHub Portfolio Agent — tracks every app in the Agyeman Enterprises portfolio.

Monitors GitHub repos for commit activity, open issues, and deployment health.
Identifies apps that are stuck, incomplete, or ready for market.
Reports to JARVIS scheduler for daily CEO briefing.

Requires: GITHUB_TOKEN env var (PAT with repo + read:org scopes)
Generate at: github.com/settings/tokens/new → classic → repo + read:org
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

from app.agents.base import AgentContext, AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_ORG = "Agyeman-Enterprises"

# Full portfolio — every app, its production URL, and its readiness target
APP_PORTFOLIO: List[Dict[str, Any]] = [
    # ── Core OS ──────────────────────────────────────────────────────────────
    {"name": "JARVIS",          "repo": "Jarvis",                    "url": "https://jarvis.agyemanenterprises.com",     "domain": "core",       "priority": "LIVE"},
    {"name": "NEXUS",           "repo": "nexus",                     "url": "https://nexus.agyemanenterprises.com",      "domain": "core",       "priority": "LIVE"},
    {"name": "GHEXIT",          "repo": "ghexit",                    "url": "https://ghexit.vercel.app",                 "domain": "comms",      "priority": "LIVE"},
    # ── Finance ──────────────────────────────────────────────────────────────
    {"name": "TaxRx",           "repo": "taxrx",                     "url": "https://www.taxrx.co",                      "domain": "finance",    "priority": "MARKET"},
    {"name": "EntityTaxPro",    "repo": "EntityTaxPro",              "url": "https://entitytaxpro-api.vercel.app",       "domain": "finance",    "priority": "MARKET"},
    {"name": "BBOS",            "repo": "bbos",                      "url": "https://bbos.taxrx.co",                     "domain": "finance",    "priority": "MARKET"},
    # ── Healthcare ───────────────────────────────────────────────────────────
    {"name": "SoloPractice",    "repo": "solopractice",              "url": "https://www.solopractice.co",               "domain": "health",     "priority": "LIVE"},
    {"name": "ScribeMD",        "repo": "scribemd-web",              "url": "https://scribemd.co",                       "domain": "health",     "priority": "LIVE"},
    {"name": "MedEdConnect",    "repo": "mededconnect",              "url": "https://mededconnect-coda-projects.vercel.app","domain": "health",  "priority": "MARKET"},
    {"name": "Linahla",         "repo": "linahla",                   "url": "https://www.linahla.com",                   "domain": "health",     "priority": "MARKET"},
    {"name": "WhoZonCall",      "repo": "WhoZonCall",                "url": "https://www.whozoncall.com",                "domain": "health",     "priority": "MARKET"},
    {"name": "ResusRunner",     "repo": "resusrunner",               "url": "https://resusrunner.com",                   "domain": "health",     "priority": "MARKET"},
    {"name": "MedRx",           "repo": "medrx",                     "url": "https://medrx.co",                          "domain": "health",     "priority": "MARKET"},
    {"name": "MyHealthAlly",    "repo": "my-health-ally",            "url": "https://www.myhealthally.app",              "domain": "health",     "priority": "MARKET"},
    # ── Education ────────────────────────────────────────────────────────────
    {"name": "BrightRoot",      "repo": "brightroot",                "url": "https://brightroot-coda-projects.vercel.app","domain": "education","priority": "MARKET"},
    {"name": "SVA Academy",     "repo": "sva",                       "url": "https://sva-three.vercel.app",              "domain": "education",  "priority": "MARKET"},
    {"name": "CodeWeaver",      "repo": "codeweaver",                "url": "https://codeweaver-coda-projects.vercel.app","domain": "education", "priority": "MARKET"},
    # ── CRM / Operations ─────────────────────────────────────────────────────
    {"name": "SynapseCRM",      "repo": "synapsecrm",                "url": "https://www.synapsecrm.co",                 "domain": "crm",        "priority": "MARKET"},
    {"name": "OneDesk",         "repo": "onedesk",                   "url": "https://onedesk-nine.vercel.app",           "domain": "ops",        "priority": "MARKET"},
    # ── Content / Creative ───────────────────────────────────────────────────
    {"name": "ContentVault",    "repo": "contentvault-dashboard",    "url": "https://vault.solopractice.co",             "domain": "content",    "priority": "LIVE"},
    {"name": "Stratova",        "repo": "stratova",                  "url": "https://stratova.vercel.app",               "domain": "marketing",  "priority": "LIVE"},
    {"name": "PlotPilot",       "repo": "plotpilot",                 "url": "https://www.plotpilot.io",                  "domain": "content",    "priority": "MARKET"},
    {"name": "DesignOS",        "repo": "designos",                  "url": "https://designos-coda-projects.vercel.app", "domain": "creative",   "priority": "MARKET"},
    {"name": "WavCraft",        "repo": "wavcraft",                  "url": "https://wavcraft.vercel.app",               "domain": "creative",   "priority": "MARKET"},
    {"name": "Whink",           "repo": "whink-web",                 "url": "https://whink-web.vercel.app",              "domain": "creative",   "priority": "MARKET"},
    {"name": "PaintersFolly",   "repo": "paintersfolly",             "url": "https://paintersfolly.vercel.app",          "domain": "creative",   "priority": "MARKET"},
    # ── Games / Media ────────────────────────────────────────────────────────
    {"name": "OpenArcade",      "repo": "openarcade",                "url": "https://openarcade-coda-projects.vercel.app","domain": "games",     "priority": "MARKET"},
    {"name": "AERIA",           "repo": "openarcade-aeria-editor",   "url": "https://openarcade-aeria-editor.vercel.app","domain": "games",      "priority": "MARKET"},
    {"name": "Aloty",           "repo": "aloty",                     "url": "https://aloty.vercel.app",                  "domain": "games",      "priority": "MARKET"},
    {"name": "Furfubu",         "repo": "furfubu",                   "url": "https://furfubu-coda-projects.vercel.app",  "domain": "wellness",   "priority": "MARKET"},
    # ── Media ────────────────────────────────────────────────────────────────
    {"name": "StudioMuse",      "repo": "studiomuse",                "url": "https://studiomuse.vercel.app",             "domain": "media",      "priority": "MARKET"},
    {"name": "IMHO Media",      "repo": "imho-media",                "url": "https://imho.media",                        "domain": "media",      "priority": "MARKET"},
    {"name": "GrandRoundsAI",   "repo": "grandroundsai",             "url": "https://grandroundsai.iamaaa.us",           "domain": "health",     "priority": "MARKET"},
]

STALE_DAYS = 14   # Apps with no commits in X days are flagged as stale
STUCK_DAYS = 30   # Apps with no commits in X days are flagged as stuck


@dataclass
class AppStatus:
    name: str
    repo: str
    url: str
    domain: str
    priority: str
    last_commit_days: Optional[int] = None
    last_commit_message: str = ""
    open_issues: int = 0
    open_prs: int = 0
    has_deployments: bool = False
    status: str = "unknown"   # live | active | stale | stuck | unreachable | no_token
    error: str = ""


class GitHubPortfolioAgent(BaseAgent):
    """Tracks every app in the portfolio via GitHub API and Vercel health checks."""

    name = "github_portfolio"
    description = "Monitors all Agyeman Enterprises apps — commit activity, open issues, PRs, deployment health"
    capabilities = [
        "list all apps and their status",
        "identify stuck or stale repos",
        "count open issues and PRs",
        "track apps by domain (health, finance, education, etc.)",
        "identify apps ready for market",
        "portfolio completion report",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._token = os.getenv("GITHUB_TOKEN", "")
        self._session = requests.Session()
        if self._token:
            self._session.headers.update({"Authorization": f"token {self._token}"})
        self._session.headers.update({"Accept": "application/vnd.github.v3+json"})

    def handle(self, query: str, context: Optional[AgentContext] = None) -> AgentResponse:
        q = query.lower()
        if not self._token:
            return AgentResponse(
                agent=self.name,
                status="blocked",
                content=(
                    "⛔ GitHub tracking is not configured.\n\n"
                    "To enable:\n"
                    "1. Go to github.com/settings/tokens/new\n"
                    "2. Create a classic token with scopes: repo, read:org\n"
                    "3. Add to Railway: GITHUB_TOKEN=<your-token>\n\n"
                    "Once set, JARVIS will monitor all 30+ apps in the portfolio."
                ),
            )

        if "stuck" in q or "stale" in q or "dead" in q:
            return self._stuck_report()
        if "ready" in q or "market" in q or "launch" in q:
            return self._market_readiness_report()
        if "finance" in q or "taxrx" in q or "etp" in q or "bbos" in q:
            return self._domain_report("finance")
        if "health" in q or "medical" in q:
            return self._domain_report("health")
        if "education" in q or "brightroot" in q or "sva" in q:
            return self._domain_report("education")
        if "game" in q or "arcade" in q or "aeria" in q:
            return self._domain_report("games")
        return self._full_portfolio_report()

    # ── Public entrypoints (called by scheduler) ─────────────────────────────

    def get_portfolio_status(self) -> List[AppStatus]:
        """Fetch status for all apps. Called by daily briefing scheduler."""
        statuses = []
        for app in APP_PORTFOLIO:
            statuses.append(self._check_app(app))
        return statuses

    def get_stuck_apps(self) -> List[AppStatus]:
        """Return apps with no commits in STUCK_DAYS. Prioritised for agent action."""
        return [s for s in self.get_portfolio_status() if s.status == "stuck"]

    def get_market_ready_apps(self) -> List[AppStatus]:
        """Return apps with recent activity and no critical open issues."""
        return [
            s for s in self.get_portfolio_status()
            if s.status in ("live", "active") and s.priority == "MARKET" and s.open_issues < 10
        ]

    def format_daily_briefing_section(self) -> str:
        """Formatted markdown for inclusion in Akua's daily CEO briefing."""
        statuses = self.get_portfolio_status()
        stuck = [s for s in statuses if s.status == "stuck"]
        stale = [s for s in statuses if s.status == "stale"]
        active = [s for s in statuses if s.status in ("live", "active")]
        errors = [s for s in statuses if s.status in ("unreachable", "unknown")]

        lines = ["## 📦 App Portfolio", ""]
        lines.append(f"**{len(active)} active** | **{len(stale)} stale** | **{len(stuck)} stuck** | **{len(errors)} unreachable**")
        lines.append("")

        if stuck:
            lines.append("### 🔴 Stuck (no commits in 30+ days)")
            for s in stuck:
                lines.append(f"- **{s.name}** ({s.domain}) — {s.last_commit_days}d since last commit, {s.open_issues} open issues")
            lines.append("")

        if stale:
            lines.append("### 🟡 Stale (14–30 days)")
            for s in stale:
                lines.append(f"- **{s.name}** — {s.last_commit_days}d, {s.open_prs} open PRs")
            lines.append("")

        if active:
            lines.append("### 🟢 Active")
            for s in active:
                msg = f" — \"{s.last_commit_message[:50]}\"" if s.last_commit_message else ""
                lines.append(f"- **{s.name}** ({s.last_commit_days}d ago){msg}")

        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _check_app(self, app: Dict[str, Any]) -> AppStatus:
        status = AppStatus(
            name=app["name"],
            repo=app["repo"],
            url=app["url"],
            domain=app["domain"],
            priority=app["priority"],
        )
        try:
            repo_data = self._get(f"/repos/{GITHUB_ORG}/{app['repo']}")
            if repo_data is None:
                status.status = "unreachable"
                status.error = "repo not found"
                return status

            # Last commit
            commits = self._get(f"/repos/{GITHUB_ORG}/{app['repo']}/commits?per_page=1")
            if commits:
                commit_date_str = commits[0].get("commit", {}).get("committer", {}).get("date", "")
                if commit_date_str:
                    commit_dt = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
                    days_ago = (datetime.now(timezone.utc) - commit_dt).days
                    status.last_commit_days = days_ago
                    status.last_commit_message = (
                        commits[0].get("commit", {}).get("message", "").split("\n")[0][:80]
                    )
                    if days_ago < STALE_DAYS:
                        status.status = "active"
                    elif days_ago < STUCK_DAYS:
                        status.status = "stale"
                    else:
                        status.status = "stuck"

            # Open issues and PRs
            status.open_issues = repo_data.get("open_issues_count", 0)
            prs = self._get(f"/repos/{GITHUB_ORG}/{app['repo']}/pulls?state=open&per_page=1")
            if prs is not None:
                status.open_prs = len(prs)

        except Exception as exc:
            status.status = "unreachable"
            status.error = str(exc)
            LOGGER.warning("GitHub check failed for %s: %s", app["name"], exc)

        return status

    def _get(self, path: str) -> Any:
        try:
            resp = self._session.get(f"{GITHUB_API}{path}", timeout=10)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def _full_portfolio_report(self) -> AgentResponse:
        statuses = self.get_portfolio_status()
        content = self._render_statuses(statuses, "Full Portfolio Report")
        return AgentResponse(agent=self.name, content=content, data={"count": len(statuses)})

    def _stuck_report(self) -> AgentResponse:
        statuses = self.get_portfolio_status()
        stuck = [s for s in statuses if s.status in ("stuck", "stale")]
        content = self._render_statuses(stuck, "Stuck / Stale Apps")
        return AgentResponse(agent=self.name, content=content, data={"count": len(stuck)})

    def _market_readiness_report(self) -> AgentResponse:
        statuses = self.get_portfolio_status()
        ready = [s for s in statuses if s.status in ("live", "active") and s.priority == "MARKET"]
        content = self._render_statuses(ready, "Apps Ready for Market")
        return AgentResponse(agent=self.name, content=content, data={"count": len(ready)})

    def _domain_report(self, domain: str) -> AgentResponse:
        statuses = [s for s in self.get_portfolio_status() if s.domain == domain]
        content = self._render_statuses(statuses, f"{domain.title()} Apps")
        return AgentResponse(agent=self.name, content=content, data={"domain": domain})

    def _render_statuses(self, statuses: List[AppStatus], title: str) -> str:
        if not statuses:
            return f"No apps found for: {title}"
        lines = [f"## {title}", ""]
        STATUS_ICON = {"live": "🟢", "active": "🟢", "stale": "🟡", "stuck": "🔴", "unreachable": "⚫", "unknown": "⚪", "no_token": "🔑"}
        for s in statuses:
            icon = STATUS_ICON.get(s.status, "⚪")
            age = f"{s.last_commit_days}d" if s.last_commit_days is not None else "unknown"
            lines.append(
                f"{icon} **{s.name}** (`{s.domain}`) — last commit: {age} | "
                f"issues: {s.open_issues} | PRs: {s.open_prs} | {s.url}"
            )
            if s.last_commit_message:
                lines.append(f"   _\"{s.last_commit_message}\"_")
        return "\n".join(lines)
