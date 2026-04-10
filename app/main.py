"""
Jeeves — Akua's Autonomous Life Manager.

One service. One brain. No mocks.
Deploys to Coolify on Hetzner. Talks to Supabase, LiteLLM, Aqui, Nexus, Ghexit.
PWA/JanusBot/SMS are clients — they call this API, nothing else.
"""

from __future__ import annotations

import hmac
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router
from app.api.review import router as review_router
from app.api.schedule import router as schedule_router
from app.config import get_settings
from app.core.orchestrator import get_orchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
LOGGER = logging.getLogger("jeeves")

# ── Scheduler ──────────────────────────────────────────────────────────
_scheduler: Optional[BackgroundScheduler] = None


def _start_scheduler():
    """Start APScheduler with daily cycles."""
    global _scheduler
    from zoneinfo import ZoneInfo
    from app.jobs.morning_cycle import run_morning_cycle_sync
    from app.jobs.nightly_reconciliation import run_nightly_reconciliation_sync
    from app.jobs.repo_audit_cycle import run_repo_audit_sync

    s = get_settings()
    tz = ZoneInfo(s.timezone)

    _scheduler = BackgroundScheduler(timezone=tz)

    # 6am: Repo audit
    _scheduler.add_job(run_repo_audit_sync, "cron", hour=6, minute=0, id="repo_audit")
    # 7am: Morning briefing
    _scheduler.add_job(run_morning_cycle_sync, "cron", hour=s.morning_hour, minute=0, id="morning_cycle")
    # 11pm: Nightly reconciliation
    _scheduler.add_job(run_nightly_reconciliation_sync, "cron", hour=s.reflection_hour, minute=0, id="nightly_reconciliation")

    _scheduler.start()
    LOGGER.info("[Jeeves] Scheduler started: morning@%d:00, nightly@%d:00, repo_audit@6:00 (%s)",
                s.morning_hour, s.reflection_hour, s.timezone)


# ── Lifespan ───────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGGER.info("[Jeeves] Starting up...")
    # Initialize orchestrator (creates all modules, seeds data)
    get_orchestrator()
    # Start scheduler
    _start_scheduler()
    LOGGER.info("[Jeeves] ✅ Ready. All systems initialized.")
    yield
    # Shutdown
    if _scheduler:
        _scheduler.shutdown(wait=False)
    LOGGER.info("[Jeeves] Shut down.")


# ── App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Jeeves",
    description="Akua's Autonomous Life Manager",
    version=get_settings().version,
    lifespan=lifespan,
)

# ── Auth middleware ────────────────────────────────────────────────────
EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        api_key = get_settings().api_key
        if not api_key:
            # Dev mode — no auth
            return await call_next(request)
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Missing Authorization header"}, status_code=401)
        provided = auth_header[7:]
        if not hmac.compare_digest(provided.encode(), api_key.encode()):
            return JSONResponse({"detail": "Invalid API key"}, status_code=403)
        return await call_next(request)


app.add_middleware(APIKeyMiddleware)

# ── CORS ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001", "http://localhost:8080",
        "https://nexus.agyemanenterprises.com",
        "https://ghexit.agyemanenterprises.com",
        "https://jarvis.agyemanenterprises.com",
        "https://jeeves.agyemanenterprises.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(review_router)
app.include_router(schedule_router)


@app.get("/health")
async def health():
    """Health check — public, no auth."""
    orch = get_orchestrator()
    return await orch.health_check()


@app.post("/morning-briefing")
async def trigger_morning_briefing():
    """Manually trigger a morning briefing."""
    orch = get_orchestrator()
    return await orch.morning_briefing()


@app.post("/nightly-reconciliation")
async def trigger_nightly_reconciliation():
    """Manually trigger nightly reconciliation."""
    from app.jobs.nightly_reconciliation import run_nightly_reconciliation
    return await run_nightly_reconciliation()


@app.post("/repo-audit")
async def trigger_repo_audit():
    """Manually trigger repo audit."""
    from app.jobs.repo_audit_cycle import run_repo_audit
    return await run_repo_audit()
