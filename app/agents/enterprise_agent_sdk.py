"""
Enterprise Agent SDK
--------------------
Shared utilities for calling /api/agent endpoints on any app in the portfolio.
All apps speak this protocol — NEXUS domain agents use this to call them.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any, Dict, Optional

import httpx

AGENT_SECRET = os.getenv("NEXUS_AGENT_SECRET", "nexus_agent_secret_change_me")
REQUEST_TIMEOUT = 15  # seconds


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _build_headers(secret: str = AGENT_SECRET) -> Dict[str, str]:
    ts = str(int(time.time()))
    sig = _sign(ts, secret)
    return {
        "Content-Type": "application/json",
        "X-Agent-Timestamp": ts,
        "X-Agent-Signature": sig,
        "X-Agent-Client": "nexus",
    }


async def call_agent_api(
    base_url: str,
    action: str,
    payload: Optional[Dict[str, Any]] = None,
    secret: str = AGENT_SECRET,
    timeout: int = REQUEST_TIMEOUT,
) -> Dict[str, Any]:
    """
    POST {base_url}/api/agent  with { action, payload }
    Returns the JSON response body.
    Raises httpx.HTTPError on non-2xx.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{base_url.rstrip('/')}/api/agent",
            json={"action": action, "payload": payload or {}},
            headers=_build_headers(secret),
        )
        resp.raise_for_status()
        return resp.json()


def call_agent_api_sync(
    base_url: str,
    action: str,
    payload: Optional[Dict[str, Any]] = None,
    secret: str = AGENT_SECRET,
    timeout: int = REQUEST_TIMEOUT,
) -> Dict[str, Any]:
    """Synchronous version for non-async contexts."""
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(
            f"{base_url.rstrip('/')}/api/agent",
            json={"action": action, "payload": payload or {}},
            headers=_build_headers(secret),
        )
        resp.raise_for_status()
        return resp.json()
