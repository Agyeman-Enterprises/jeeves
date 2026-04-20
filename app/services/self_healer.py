"""
JARVIS Self-Healing Audit System
=================================
Monitors every critical integration, attempts auto-repair, and calls Claude
when something can't be fixed automatically. Akua never has to touch code.

Monitored services:
  - JARVIS API health (own Railway deployment)
  - Railway deployment status (via GraphQL API)
  - Google OAuth (Gmail + Calendar token validity)
  - Dropbox token validity
  - NEXUS connectivity
  - DNS resolution for jarvis.agyemanenterprises.com
  - APScheduler job registry (are expected jobs still running?)
  - Required environment variables
  - LinkedIn session cookies (expiry check)
  - Cloudflare DNS (verify CNAME still points to correct Railway target)

Repair strategy per failure:
  - Railway crash     → trigger redeploy via Railway API
  - Google token      → call token refresh endpoint
  - Env var missing   → alert with remediation instructions
  - DNS wrong/missing → re-create CNAME via Cloudflare API
  - Anything else     → call Claude API, email diagnosis + fix plan to Akua
"""

from __future__ import annotations

import json
import logging
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Service registry — every entry gets checked on every audit run
# ---------------------------------------------------------------------------
SERVICES = {
    "jarvis_health": {
        "label": "JARVIS API (Railway)",
        "critical": True,
    },
    "railway_deployment": {
        "label": "Railway Deployment Status",
        "critical": True,
    },
    "google_oauth": {
        "label": "Google OAuth (Gmail/Calendar)",
        "critical": True,
    },
    "dropbox_token": {
        "label": "Dropbox Token",
        "critical": False,
    },
    "nexus_connectivity": {
        "label": "NEXUS (nexus.agyemanenterprises.com)",
        "critical": True,
    },
    "dns_jarvis": {
        "label": "DNS: jarvis.agyemanenterprises.com",
        "critical": True,
    },
    "env_vars": {
        "label": "Required Environment Variables",
        "critical": True,
    },
    "linkedin_cookies": {
        "label": "LinkedIn Session Cookies",
        "critical": False,
    },
    "cloudflare_cname": {
        "label": "Cloudflare DNS CNAME",
        "critical": False,
    },
}

REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "RAILWAY_PERSONAL_TOKEN",
    "RAILWAY_PROJECT_ID",
    "RAILWAY_SERVICE_ID",
    "JARVIS_BRIEFING_EMAIL",
]

# Hardcoded targets — never from user input
_RAILWAY_API = "https://backboard.railway.app/graphql/v2"
_ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
_GOOGLE_TOKENINFO = "https://www.googleapis.com/oauth2/v1/tokeninfo"
_DROPBOX_API = "https://api.dropboxapi.com/2/users/get_current_account"
_CLOUDFLARE_API = "https://api.cloudflare.com/client/v4"


# ---------------------------------------------------------------------------
# Individual health checks
# ---------------------------------------------------------------------------

def check_jarvis_health() -> tuple[bool, str]:
    """Ping JARVIS own health endpoint."""
    # URL comes from env but is constrained to https only
    base = os.getenv(
        "JARVIS_BACKEND_URL",
        "https://jarvis.agyemanenterprises.com",
    )
    if not base.startswith("https://"):
        return False, "JARVIS_BACKEND_URL must use https://"
    url = f"{base}/health"
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        if r.status_code == 200:
            return True, "OK"
        return False, f"Health endpoint returned HTTP {r.status_code}"
    except Exception as exc:
        return False, f"Could not reach {url}: {exc}"


def check_railway_deployment() -> tuple[bool, str]:
    """Check Railway deployment status via GraphQL API."""
    token = os.getenv("RAILWAY_PERSONAL_TOKEN")
    service_id = os.getenv("RAILWAY_SERVICE_ID")
    env_id = os.getenv("RAILWAY_ENV_ID")
    if not token or not service_id:
        return False, "RAILWAY_PERSONAL_TOKEN or RAILWAY_SERVICE_ID not set"

    query = """
    query ServiceDeployments($serviceId: String!, $environmentId: String) {
      deployments(
        input: { serviceId: $serviceId, environmentId: $environmentId }
        first: 1
      ) {
        edges { node { id status createdAt } }
      }
    }
    """
    try:
        r = httpx.post(
            _RAILWAY_API,
            json={"query": query, "variables": {"serviceId": service_id, "environmentId": env_id}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        data = r.json()
    except Exception as exc:
        return False, f"Railway API unreachable: {exc}"

    edges = data.get("data", {}).get("deployments", {}).get("edges", [])
    if not edges:
        return False, "No deployments found on Railway"

    status = edges[0]["node"].get("status", "UNKNOWN")
    if status == "SUCCESS":
        return True, f"Latest deployment: {status}"
    if status in ("FAILED", "CRASHED", "REMOVED"):
        return False, f"Latest Railway deployment status: {status}"
    return True, f"Deployment in progress: {status}"


def check_google_oauth() -> tuple[bool, str]:
    """Test Google token by hitting tokeninfo endpoint."""
    token_path = Path("config/google_drive_tokens.json")
    if not token_path.exists():
        return False, "config/google_drive_tokens.json not found"

    try:
        tokens = json.loads(token_path.read_text())
        access_token = tokens.get("access_token") or tokens.get("token")
        if not access_token:
            return False, "No access_token in google_drive_tokens.json"

        r = httpx.get(
            _GOOGLE_TOKENINFO,
            params={"access_token": access_token},
            timeout=10,
        )
        if r.status_code == 200:
            return True, "Google OAuth token valid"
        return False, f"Google tokeninfo returned {r.status_code} — token likely expired"
    except Exception as exc:
        return False, f"Google OAuth check failed: {exc}"


def check_dropbox_token() -> tuple[bool, str]:
    """Validate Dropbox long-lived token."""
    token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if not token:
        return False, "DROPBOX_ACCESS_TOKEN not set"

    try:
        r = httpx.post(
            _DROPBOX_API,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 200:
            return True, "Dropbox token valid"
        if r.status_code == 401:
            return False, "Dropbox token expired or revoked"
        return False, f"Dropbox API returned HTTP {r.status_code}"
    except Exception as exc:
        return False, f"Dropbox check failed: {exc}"


def check_nexus_connectivity() -> tuple[bool, str]:
    """Ping NEXUS API."""
    nexus_url = os.getenv("NEXUS_URL", "https://nexus.agyemanenterprises.com")
    if not nexus_url.startswith("https://"):
        return False, "NEXUS_URL must use https://"
    try:
        r = httpx.get(f"{nexus_url}/api/health", timeout=10, follow_redirects=True)
        if r.status_code == 200:
            return True, "NEXUS reachable"
        r2 = httpx.get(nexus_url, timeout=10, follow_redirects=True)
        if r2.status_code in (200, 302):
            return True, "NEXUS reachable (root)"
        return False, f"NEXUS returned HTTP {r.status_code}"
    except Exception as exc:
        return False, f"NEXUS unreachable: {exc}"


def check_dns_jarvis() -> tuple[bool, str]:
    """Verify jarvis.agyemanenterprises.com resolves."""
    try:
        ip = socket.gethostbyname("jarvis.agyemanenterprises.com")
        return True, f"DNS resolves to {ip}"
    except socket.gaierror:
        return False, "jarvis.agyemanenterprises.com does not resolve — CNAME may be missing"


def check_env_vars() -> tuple[bool, str]:
    """Verify all required env vars are set and non-empty."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if not missing:
        return True, "All required env vars present"
    return False, f"Missing env vars: {', '.join(missing)}"


def check_linkedin_cookies() -> tuple[bool, str]:
    """Check LinkedIn session cookies haven't expired."""
    cookie_path = Path("config/linkedin_session_cookies.json")
    if not cookie_path.exists():
        return False, "config/linkedin_session_cookies.json not found"
    try:
        cookies = json.loads(cookie_path.read_text())
        now_ts = datetime.now(timezone.utc).timestamp()
        expired = [
            c.get("name", "unknown")
            for c in (cookies if isinstance(cookies, list) else [])
            if (c.get("expiry") or c.get("expires") or 0) < now_ts
               and (c.get("expiry") or c.get("expires") or 0) > 0
        ]
        if expired:
            return False, f"LinkedIn cookies expired: {expired}"
        return True, "LinkedIn session cookies appear valid"
    except Exception as exc:
        return False, f"Could not parse LinkedIn cookies: {exc}"


def check_cloudflare_cname() -> tuple[bool, str]:
    """Verify public JARVIS URL (jarvis.flyryt.ai) responds via Cloudflare Worker."""
    public_url = os.getenv("JARVIS_PUBLIC_URL", "https://jarvis.flyryt.ai")
    try:
        r = httpx.get(f"{public_url}/health", timeout=10, follow_redirects=True)
        if r.status_code == 200:
            return True, f"Public URL {public_url} healthy (200 OK)"
        return False, f"Public URL {public_url} returned {r.status_code}"
    except Exception as exc:
        return False, f"Public URL {public_url} unreachable: {exc}"


# ---------------------------------------------------------------------------
# Repair strategies
# ---------------------------------------------------------------------------

def repair_railway_deployment() -> str:
    """Trigger a Railway redeploy."""
    token = os.getenv("RAILWAY_PERSONAL_TOKEN")
    service_id = os.getenv("RAILWAY_SERVICE_ID")
    env_id = os.getenv("RAILWAY_ENV_ID")
    if not token or not service_id:
        return "Cannot repair — Railway credentials missing"

    mutation = """
    mutation ServiceInstanceDeploy($serviceId: String!, $environmentId: String!) {
      serviceInstanceDeploy(serviceId: $serviceId, environmentId: $environmentId)
    }
    """
    try:
        r = httpx.post(
            _RAILWAY_API,
            json={"query": mutation, "variables": {"serviceId": service_id, "environmentId": env_id}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        data = r.json()
        if data.get("data", {}).get("serviceInstanceDeploy"):
            return "Railway redeploy triggered successfully"
        return f"Railway redeploy failed: {data.get('errors')}"
    except Exception as exc:
        return f"Railway redeploy error: {exc}"


def repair_google_token() -> str:
    """Refresh Google OAuth token using stored refresh token."""
    try:
        from app.services.google_drive_service import google_drive_service
        google_drive_service.refresh_token()
        return "Google OAuth token refreshed successfully"
    except Exception as exc:
        return f"Google token refresh failed: {exc}"


def repair_cloudflare_cname() -> str:
    """JARVIS is now served via Cloudflare Worker at jarvis.flyryt.ai — no CNAME to repair."""
    return "Public URL uses Cloudflare Worker (jarvis.flyryt.ai) — no CNAME repair needed"


# ---------------------------------------------------------------------------
# Claude API — called when auto-repair fails
# ---------------------------------------------------------------------------

def ask_claude_for_help(service_label: str, error_detail: str) -> str:
    """
    Call Claude API with the failure context. Returns Claude's diagnosis
    and recommended fix as plain text.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Claude API key not set — cannot get automated diagnosis"

    prompt = (
        f"You are JARVIS's internal diagnostic AI.\n\n"
        f"A service has failed:\nService: {service_label}\nError: {error_detail}\n\n"
        f"JARVIS runs on Railway (Python FastAPI). Key dependencies: "
        f"Google OAuth (Gmail/Calendar), Dropbox sync, NEXUS (Next.js on Vercel), "
        f"Railway deployment API, Cloudflare DNS.\n\n"
        f"Provide a concise diagnosis (2-3 sentences) and exact repair steps. "
        f"Be specific — commands, file paths, API calls. "
        f"Akua is not a developer; if a manual step is needed, say exactly what to click/type."
    )
    try:
        r = httpx.post(
            _ANTHROPIC_API,
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=30,
        )
        return r.json()["content"][0]["text"]
    except Exception as exc:
        return f"Claude API call failed: {exc}"


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------

def _send_alert(subject: str, body: str) -> None:
    """Send email + Pushover alert."""
    email = os.getenv("JARVIS_BRIEFING_EMAIL")
    try:
        from app.services.email.email_service import email_service
        if email and email_service:
            email_service.send_email(email, subject, body)
    except Exception as exc:
        LOGGER.warning("Alert email failed: %s", exc)

    try:
        from app.services.communications.pushover_service import pushover_service
        if pushover_service.is_configured():
            pushover_service.send_notification(
                title=subject[:100],
                message=body[:500],
                priority=1,
            )
    except Exception as exc:
        LOGGER.warning("Pushover alert failed: %s", exc)


# ---------------------------------------------------------------------------
# Main audit runner
# ---------------------------------------------------------------------------

CHECK_MAP = {
    "jarvis_health": check_jarvis_health,
    "railway_deployment": check_railway_deployment,
    "google_oauth": check_google_oauth,
    "dropbox_token": check_dropbox_token,
    "nexus_connectivity": check_nexus_connectivity,
    "dns_jarvis": check_dns_jarvis,
    "env_vars": check_env_vars,
    "linkedin_cookies": check_linkedin_cookies,
    "cloudflare_cname": check_cloudflare_cname,
}

REPAIR_MAP = {
    "railway_deployment": repair_railway_deployment,
    "google_oauth": repair_google_token,
    "cloudflare_cname": repair_cloudflare_cname,
}


def run_full_audit(notify_on_success: bool = False) -> dict[str, Any]:
    """
    Run all health checks, attempt auto-repair on failures, call Claude
    when auto-repair can't help, and alert Akua for every unresolved failure.

    Returns dict with keys: passed, failed, repaired, needs_attention.
    """
    now = datetime.now(timezone.utc).isoformat()
    results: dict[str, Any] = {
        "timestamp": now,
        "passed": [],
        "failed": [],
        "repaired": [],
        "needs_attention": [],
    }

    for service_key, check_fn in CHECK_MAP.items():
        label = SERVICES[service_key]["label"]
        try:
            ok, detail = check_fn()
        except Exception as exc:
            ok, detail = False, f"Check threw exception: {exc}"

        if ok:
            LOGGER.info("[Self-Audit] ✓ %s: %s", label, detail)
            results["passed"].append({"service": label, "detail": detail})
            continue

        LOGGER.warning("[Self-Audit] ✗ %s: %s", label, detail)
        results["failed"].append({"service": label, "detail": detail})

        # Attempt auto-repair
        repair_result = None
        if service_key in REPAIR_MAP:
            LOGGER.info("[Self-Audit] Auto-repairing %s...", label)
            repair_result = REPAIR_MAP[service_key]()
            LOGGER.info("[Self-Audit] Repair: %s", repair_result)

            try:
                ok2, _ = CHECK_MAP[service_key]()
            except Exception:
                ok2 = False

            if ok2:
                results["repaired"].append({
                    "service": label,
                    "error": detail,
                    "repair": repair_result,
                })
                _send_alert(
                    f"[JARVIS Auto-Repair] {label} fixed",
                    f"Was down: {detail}\n\nRepair: {repair_result}\n\nNow healthy.",
                )
                continue

        # Auto-repair failed — ask Claude for help
        claude_advice = ask_claude_for_help(label, detail)
        results["needs_attention"].append({
            "service": label,
            "error": detail,
            "repair_attempt": repair_result,
            "claude_advice": claude_advice,
        })

        body = f"Service: {label}\nError: {detail}\n"
        if repair_result:
            body += f"\nAuto-repair attempted: {repair_result}\n"
        body += f"\nClaude's diagnosis:\n{claude_advice}"
        _send_alert(f"[JARVIS ALERT] {label} is down", body)

    n_pass = len(results["passed"])
    n_fail = len(results["failed"])
    n_rep = len(results["repaired"])
    n_attn = len(results["needs_attention"])
    LOGGER.info(
        "[Self-Audit] Done — %d passed, %d failed (%d auto-repaired, %d need attention)",
        n_pass, n_fail, n_rep, n_attn,
    )

    if notify_on_success and n_fail == 0:
        _send_alert(
            "[JARVIS] All systems healthy",
            f"Self-audit at {now}: all {n_pass} services OK.",
        )

    log_dir = Path("data/audit_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    (log_dir / f"audit_{ts}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    return results
