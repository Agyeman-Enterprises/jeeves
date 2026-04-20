"""
JARVIS Executor — CEO Decision Execution Engine
================================================
Converts JARVIS recommendations into REAL actions.

Decision levels:
  Level 1 (auto-execute): reports, status checks, email summaries, calendar reads
  Level 2 (execute with audit log): GitHub issues/PRs, DNS updates, Vercel checks
  Level 3 (wait for approval): deploys to prod, data deletion, financial transactions

Usage:
    executor = JarvisExecutor()
    result = await executor.execute(decision)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DecisionLevel(int, Enum):
    AUTO = 1          # fire-and-forget, always execute
    AUDIT = 2         # execute and log, no human gate
    APPROVAL = 3      # queue for human approval before executing


class ActionType(str, Enum):
    # Level 1 — information & communication
    SEND_BRIEFING_EMAIL = "send_briefing_email"
    SEND_EMAIL = "send_email"
    READ_CALENDAR = "read_calendar"
    CHECK_SERVICE_HEALTH = "check_service_health"
    FETCH_NEXUS_BRIEFING = "fetch_nexus_briefing"

    # Level 2 — execution with audit trail
    CREATE_GITHUB_ISSUE = "create_github_issue"
    CREATE_GITHUB_PR_COMMENT = "create_github_pr_comment"
    CHECK_VERCEL_DEPLOYMENT = "check_vercel_deployment"
    UPDATE_CLOUDFLARE_DNS = "update_cloudflare_dns"
    SEND_SMS_VIA_GHEXIT = "send_sms_via_ghexit"

    # Level 3 — requires explicit approval
    DEPLOY_TO_PRODUCTION = "deploy_to_production"
    DELETE_DATA = "delete_data"
    FINANCIAL_TRANSACTION = "financial_transaction"
    BULK_EMAIL_CAMPAIGN = "bulk_email_campaign"


# Map each action to its decision level
ACTION_LEVELS: Dict[ActionType, DecisionLevel] = {
    ActionType.SEND_BRIEFING_EMAIL:     DecisionLevel.AUTO,
    ActionType.SEND_EMAIL:              DecisionLevel.AUTO,
    ActionType.READ_CALENDAR:           DecisionLevel.AUTO,
    ActionType.CHECK_SERVICE_HEALTH:    DecisionLevel.AUTO,
    ActionType.FETCH_NEXUS_BRIEFING:    DecisionLevel.AUTO,

    ActionType.CREATE_GITHUB_ISSUE:     DecisionLevel.AUDIT,
    ActionType.CREATE_GITHUB_PR_COMMENT: DecisionLevel.AUDIT,
    ActionType.CHECK_VERCEL_DEPLOYMENT: DecisionLevel.AUDIT,
    ActionType.UPDATE_CLOUDFLARE_DNS:   DecisionLevel.AUDIT,
    ActionType.SEND_SMS_VIA_GHEXIT:     DecisionLevel.AUDIT,

    ActionType.DEPLOY_TO_PRODUCTION:    DecisionLevel.APPROVAL,
    ActionType.DELETE_DATA:             DecisionLevel.APPROVAL,
    ActionType.FINANCIAL_TRANSACTION:   DecisionLevel.APPROVAL,
    ActionType.BULK_EMAIL_CAMPAIGN:     DecisionLevel.APPROVAL,
}


@dataclass
class Decision:
    action: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    requested_by: str = "jarvis"
    decision_id: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d%H%M%S"))


@dataclass
class ExecutionResult:
    decision_id: str
    action: ActionType
    level: DecisionLevel
    success: bool
    output: Any = None
    error: Optional[str] = None
    pending_approval: bool = False
    executed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action": self.action.value,
            "level": self.level.value,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "pending_approval": self.pending_approval,
            "executed_at": self.executed_at,
        }


class JarvisExecutor:
    """
    Main executor. Instantiate once; call execute() per decision.
    All heavy imports are lazy so the executor starts fast even if
    optional service clients are missing.
    """

    def __init__(self) -> None:
        self._resend: Any = None
        self._github: Any = None
        self._vercel: Any = None
        self._cloudflare: Any = None
        self._approval_queue: List[Decision] = []

    # ── Public API ────────────────────────────────────────────────────────────

    async def execute(self, decision: Decision) -> ExecutionResult:
        level = ACTION_LEVELS.get(decision.action, DecisionLevel.APPROVAL)

        if level == DecisionLevel.APPROVAL:
            self._approval_queue.append(decision)
            LOGGER.info(
                "[JARVIS-EXECUTOR] Level 3 — queued for approval: %s (id=%s)",
                decision.action.value, decision.decision_id,
            )
            return ExecutionResult(
                decision_id=decision.decision_id,
                action=decision.action,
                level=level,
                success=False,
                pending_approval=True,
                output={"message": f"Action '{decision.action.value}' requires Akua's approval before executing."},
            )

        try:
            output = await self._dispatch(decision)
            if level == DecisionLevel.AUDIT:
                self._audit_log(decision, output)
            return ExecutionResult(
                decision_id=decision.decision_id,
                action=decision.action,
                level=level,
                success=True,
                output=output,
            )
        except Exception as exc:
            LOGGER.error("[JARVIS-EXECUTOR] %s failed: %s", decision.action.value, exc)
            return ExecutionResult(
                decision_id=decision.decision_id,
                action=decision.action,
                level=level,
                success=False,
                error=str(exc),
            )

    def pending_approvals(self) -> List[Decision]:
        return list(self._approval_queue)

    def approve_and_execute_sync(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Used by the approval endpoint to run a previously queued Level 3 action."""
        import asyncio
        for i, d in enumerate(self._approval_queue):
            if d.decision_id == decision_id:
                self._approval_queue.pop(i)
                loop = asyncio.new_event_loop()
                try:
                    output = loop.run_until_complete(self._dispatch(d))
                    self._audit_log(d, output)
                    return {"success": True, "output": output}
                finally:
                    loop.close()
        return None

    # ── Dispatch ──────────────────────────────────────────────────────────────

    async def _dispatch(self, decision: Decision) -> Any:
        action = decision.action
        p = decision.params

        if action == ActionType.SEND_BRIEFING_EMAIL:
            return await self._send_briefing_email(p)
        if action == ActionType.SEND_EMAIL:
            return await self._send_email(p)
        if action == ActionType.CHECK_SERVICE_HEALTH:
            return await self._check_service_health(p)
        if action == ActionType.FETCH_NEXUS_BRIEFING:
            return await self._fetch_nexus_briefing(p)
        if action == ActionType.CREATE_GITHUB_ISSUE:
            return await self._create_github_issue(p)
        if action == ActionType.CREATE_GITHUB_PR_COMMENT:
            return await self._create_github_pr_comment(p)
        if action == ActionType.CHECK_VERCEL_DEPLOYMENT:
            return await self._check_vercel_deployment(p)
        if action == ActionType.UPDATE_CLOUDFLARE_DNS:
            return await self._update_cloudflare_dns(p)
        if action == ActionType.SEND_SMS_VIA_GHEXIT:
            return await self._send_sms_via_ghexit(p)

        raise ValueError(f"No handler for action: {action.value}")

    # ── Level 1 handlers ─────────────────────────────────────────────────────

    async def _send_briefing_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        resend = self._get_resend()
        to = params.get("to", os.getenv("JARVIS_BRIEFING_EMAIL", "isaalia@gmail.com"))
        subject = params.get("subject", f"JARVIS Briefing — {datetime.utcnow().strftime('%Y-%m-%d')}")
        body_html = params.get("body_html", "<p>No briefing content provided.</p>")
        return resend.send_briefing(to=to, subject=subject, body_html=body_html)

    async def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        resend = self._get_resend()
        return resend.send_email(
            to=params["to"],
            subject=params["subject"],
            html=params["html"],
            text=params.get("text"),
            reply_to=params.get("reply_to"),
        )

    async def _check_service_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        url = params.get("url")
        if not url:
            raise ValueError("url param required for check_service_health")
        try:
            resp = httpx.get(url, timeout=10)
            return {"url": url, "status": resp.status_code, "ok": resp.status_code < 400}
        except Exception as exc:
            return {"url": url, "status": None, "ok": False, "error": str(exc)}

    async def _fetch_nexus_briefing(self, _params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        nexus_url = os.getenv("NEXUS_URL", "https://nexus.agyemanenterprises.com")
        key = os.getenv("NEXUS_INTERNAL_KEY")
        if not key:
            raise RuntimeError("NEXUS_INTERNAL_KEY not set")
        resp = httpx.get(
            f"{nexus_url}/api/enterprise/briefing",
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Level 2 handlers ─────────────────────────────────────────────────────

    async def _create_github_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN not set")
        repo = params["repo"]  # e.g. "Agyeman-Enterprises/nexus"
        resp = httpx.post(
            f"https://api.github.com/repos/{repo}/issues",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "title": params["title"],
                "body": params.get("body", ""),
                "labels": params.get("labels", []),
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"issue_number": data["number"], "url": data["html_url"]}

    async def _create_github_pr_comment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN not set")
        repo = params["repo"]
        pr_number = params["pr_number"]
        resp = httpx.post(
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"body": params["body"]},
            timeout=30,
        )
        resp.raise_for_status()
        return {"comment_id": resp.json()["id"]}

    async def _check_vercel_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        token = os.getenv("VERCEL_TOKEN")
        if not token:
            raise RuntimeError("VERCEL_TOKEN not set")
        project_id = params.get("project_id")
        url = (
            f"https://api.vercel.com/v6/deployments?projectId={project_id}&limit=5"
            if project_id else
            "https://api.vercel.com/v6/deployments?limit=10"
        )
        resp = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        resp.raise_for_status()
        deployments = resp.json().get("deployments", [])
        latest = deployments[0] if deployments else None
        return {
            "latest": {
                "uid": latest["uid"],
                "url": latest.get("url"),
                "state": latest.get("state"),
                "created": latest.get("createdAt"),
            } if latest else None,
            "total_fetched": len(deployments),
        }

    async def _update_cloudflare_dns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        token = os.getenv("CLOUDFLARE_API_TOKEN")
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID", params.get("zone_id"))
        if not token or not zone_id:
            raise RuntimeError("CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID must be set")
        record_id = params["record_id"]
        resp = httpx.patch(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={k: v for k, v in params.items() if k in ("name", "type", "content", "ttl", "proxied")},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("result", {})

    async def _send_sms_via_ghexit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        ghexit_url = os.getenv("GHEXIT_BASE_URL", "https://ghexit.vercel.app")
        token = os.getenv("GHEXIT_INTERNAL_SERVICE_TOKEN")
        if not token:
            raise RuntimeError("GHEXIT_INTERNAL_SERVICE_TOKEN not set")
        resp = httpx.post(
            f"{ghexit_url}/api/agent",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "action": "send_sms",
                "to": params["to"],
                "message": params["message"],
                "provider": params.get("provider", "twilio"),
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_resend(self) -> Any:
        if self._resend is None:
            from app.services.resend_service import ResendService
            self._resend = ResendService()
        return self._resend

    def _audit_log(self, decision: Decision, output: Any) -> None:
        LOGGER.info(
            "[JARVIS-EXECUTOR AUDIT] action=%s id=%s reason=%s output=%s",
            decision.action.value,
            decision.decision_id,
            decision.reason,
            str(output)[:500],
        )


# ── Singleton ─────────────────────────────────────────────────────────────────

_executor_instance: Optional[JarvisExecutor] = None


def get_executor() -> JarvisExecutor:
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = JarvisExecutor()
    return _executor_instance
