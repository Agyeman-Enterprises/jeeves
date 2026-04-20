"""
Domain Tracker — syncs domain portfolio from GoDaddy (+ others) into Supabase.

Runs daily via scheduler. JARVIS reads from the domains table to answer queries
like "which domains expire this month?" and fires alrtme alerts for expiring domains.

Requires env vars:
  GODADDY_API_KEY      — GoDaddy developer API key (get from developer.godaddy.com)
  GODADDY_API_SECRET   — GoDaddy developer API secret
  SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY  — standard JARVIS Supabase env
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

LOGGER = logging.getLogger(__name__)

GODADDY_BASE = "https://api.godaddy.com/v1"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
GODADDY_KEY = os.getenv("GODADDY_API_KEY", "")
GODADDY_SECRET = os.getenv("GODADDY_API_SECRET", "")


def _sb_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }


def _gd_headers() -> Dict[str, str]:
    return {
        "Authorization": f"sso-key {GODADDY_KEY}:{GODADDY_SECRET}",
        "Accept": "application/json",
    }


def _godaddy_available() -> bool:
    return bool(GODADDY_KEY and GODADDY_SECRET)


def fetch_godaddy_domains() -> List[Dict[str, Any]]:
    """Fetch all domains from GoDaddy account."""
    if not _godaddy_available():
        LOGGER.warning("GoDaddy credentials not set — skipping sync")
        return []

    domains = []
    limit = 100
    marker = None

    with httpx.Client(timeout=30) as client:
        while True:
            params: Dict[str, Any] = {"limit": limit, "includes": "contacts,nameServers"}
            if marker:
                params["marker"] = marker

            resp = client.get(f"{GODADDY_BASE}/domains", headers=_gd_headers(), params=params)
            if resp.status_code != 200:
                LOGGER.error("GoDaddy API error %s: %s", resp.status_code, resp.text[:300])
                break

            batch = resp.json()
            if not batch:
                break

            domains.extend(batch)

            if len(batch) < limit:
                break
            marker = batch[-1].get("domain")

    LOGGER.info("Fetched %d domains from GoDaddy", len(domains))
    return domains


def _parse_domain_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert GoDaddy domain object to our DB row format."""
    expires_str = raw.get("expires")
    expires_at = None
    if expires_str:
        try:
            expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00")).isoformat()
        except ValueError:
            pass

    nameservers = [
        ns.get("hostname", "") if isinstance(ns, dict) else str(ns)
        for ns in raw.get("nameServers") or []
    ] or None

    # Infer DNS provider from nameservers
    ns_str = " ".join(nameservers or []).lower()
    if "cloudflare" in ns_str:
        dns_provider = "cloudflare"
    elif "godaddy" in ns_str or "domaincontrol" in ns_str:
        dns_provider = "godaddy"
    else:
        dns_provider = "other" if nameservers else None

    return {
        "name": raw.get("domain", "").lower(),
        "registrar": "godaddy",
        "status": raw.get("status", "active").lower(),
        "expires_at": expires_at,
        "auto_renew": raw.get("renewAuto", True),
        "locked": raw.get("locked", True),
        "dns_provider": dns_provider,
        "nameservers": nameservers,
        "privacy": raw.get("privacy", False),
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "raw_data": raw,
    }


def upsert_domains(rows: List[Dict[str, Any]]) -> int:
    """Upsert domain rows into Supabase. Returns count upserted."""
    if not rows or not SUPABASE_URL or not SUPABASE_KEY:
        return 0

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{SUPABASE_URL}/rest/v1/domains",
            headers={**_sb_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=rows,
        )
        if resp.status_code not in (200, 201):
            LOGGER.error("Supabase upsert error %s: %s", resp.status_code, resp.text[:300])
            return 0

    return len(rows)


def get_expiring_domains(days: int = 30) -> List[Dict[str, Any]]:
    """Return domains expiring within `days` days."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    cutoff = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{SUPABASE_URL}/rest/v1/domains",
            headers=_sb_headers(),
            params={
                "select": "name,expires_at,auto_renew,registrar",
                "expires_at": f"lte.{cutoff}",
                "status": "eq.active",
                "order": "expires_at.asc",
            },
        )
        if resp.status_code != 200:
            return []
        return resp.json()


def get_all_domains() -> List[Dict[str, Any]]:
    """Return all active domains from Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{SUPABASE_URL}/rest/v1/domains",
            headers=_sb_headers(),
            params={
                "select": "name,registrar,status,expires_at,auto_renew,dns_provider,synced_at",
                "status": "eq.active",
                "order": "expires_at.asc",
            },
        )
        if resp.status_code != 200:
            return []
        return resp.json()


def sync_domains() -> Dict[str, Any]:
    """Full sync: GoDaddy → Supabase. Returns summary dict."""
    LOGGER.info("Starting domain sync...")

    raw_domains = fetch_godaddy_domains()
    if not raw_domains:
        return {"ok": True, "synced": 0, "expiring_30d": 0, "message": "No GoDaddy credentials or no domains"}

    rows = [_parse_domain_row(d) for d in raw_domains]
    synced = upsert_domains(rows)

    expiring = get_expiring_domains(30)
    expiring_no_renew = [d for d in expiring if not d.get("auto_renew")]

    result = {
        "ok": True,
        "synced": synced,
        "total": len(rows),
        "expiring_30d": len(expiring),
        "expiring_no_auto_renew": len(expiring_no_renew),
        "domains_expiring": [d["name"] for d in expiring],
    }

    LOGGER.info("Domain sync complete: %s", result)
    return result


def fire_expiry_alerts() -> None:
    """Send alrtme alert for domains expiring in ≤30 days with auto_renew OFF."""
    expiring = get_expiring_domains(30)
    at_risk = [d for d in expiring if not d.get("auto_renew")]

    if not at_risk:
        return

    try:
        import os
        import httpx as _httpx

        alrtme_key = os.getenv("ALRTME_API_KEY", "")
        alrtme_channel = os.getenv("ALRTME_CHANNEL", "akualrts")
        if not alrtme_key:
            LOGGER.warning("ALRTME_API_KEY not set — skipping expiry alert")
            return

        names = ", ".join(d["name"] for d in at_risk[:5])
        if len(at_risk) > 5:
            names += f" (+{len(at_risk)-5} more)"

        msg = f"⚠️ {len(at_risk)} domain(s) expiring in 30 days with auto-renew OFF: {names}"

        with _httpx.Client(timeout=10) as client:
            client.post(
                "https://alrtme.co/api/send",
                headers={"Authorization": f"Bearer {alrtme_key}", "Content-Type": "application/json"},
                json={"channel": alrtme_channel, "message": msg, "title": "Domain Expiry Alert"},
            )
    except Exception as exc:
        LOGGER.warning("Failed to send domain expiry alert: %s", exc)
