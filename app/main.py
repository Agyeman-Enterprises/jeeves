"""
JJ — Akua's Autonomous Life Manager.
v2.1: Gmail, Calendar, Profile Builder, Evening Check-In added.
"""

from __future__ import annotations

import hmac
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router
from app.api.review import router as review_router
from app.api.schedule import router as schedule_router
from app.api.webhooks import router as webhooks_router
from app.config import get_settings
from app.core.orchestrator import get_orchestrator

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s")
LOGGER = logging.getLogger("jj")

_scheduler: Optional[BackgroundScheduler] = None


def _start_scheduler():
    global _scheduler
    from zoneinfo import ZoneInfo
    from app.jobs.morning_cycle import run_morning_cycle_sync, run_evening_checkin_sync
    from app.jobs.nightly_reconciliation import run_nightly_reconciliation_sync
    from app.jobs.repo_audit_cycle import run_repo_audit_sync

    s = get_settings()
    tz = ZoneInfo(s.timezone)
    _scheduler = BackgroundScheduler(timezone=tz)

    # 6am: Repo audit
    _scheduler.add_job(run_repo_audit_sync, "cron", hour=6, minute=0, id="repo_audit")
    # 7am: Morning briefing + daily question
    _scheduler.add_job(run_morning_cycle_sync, "cron", hour=s.morning_hour, minute=0, id="morning_cycle")
    # 6pm: Evening check-in (profile questions)
    _scheduler.add_job(run_evening_checkin_sync, "cron", hour=s.checkin_hour, minute=0, id="evening_checkin")
    # 11pm: Nightly reconciliation
    _scheduler.add_job(run_nightly_reconciliation_sync, "cron", hour=s.reflection_hour, minute=0, id="nightly_reconciliation")

    _scheduler.start()
    LOGGER.info("[JJ] Scheduler started: morning@%d:00, checkin@%d:00, nightly@%d:00 (%s)",
                s.morning_hour, s.checkin_hour, s.reflection_hour, s.timezone)


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGGER.info("[JJ] Starting up...")
    get_orchestrator()
    _start_scheduler()
    LOGGER.info("[JJ] Ready.")
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)
    LOGGER.info("[JJ] Shut down.")


app = FastAPI(title="JJ", description="Akua's Autonomous Life Manager",
              version=get_settings().version, lifespan=lifespan)

# ── Auth ───────────────────────────────────────────────────────────────
EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
EXEMPT_PREFIXES = ("/app", "/webhooks")


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        if any(request.url.path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)
        api_key = get_settings().api_key
        if not api_key:
            return await call_next(request)
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Missing Authorization header"}, status_code=401)
        provided = auth_header[7:]
        if not hmac.compare_digest(provided.encode(), api_key.encode()):
            return JSONResponse({"detail": "Invalid API key"}, status_code=403)
        return await call_next(request)


app.add_middleware(APIKeyMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001", "http://localhost:8080",
        "https://nexus.agyemanenterprises.com",
        "https://ghexit.agyemanenterprises.com",
        "https://jarvis.agyemanenterprises.com",
        "https://jeeves.agyemanenterprises.com",
        "https://jarvis-eight-ivory.vercel.app",
    ],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Routes ─────────────────────────────────────────────────────────────
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(review_router)
app.include_router(schedule_router)
app.include_router(webhooks_router)


@app.get("/health")
async def health():
    return await get_orchestrator().health_check()


@app.post("/morning-briefing")
async def trigger_morning_briefing():
    return await get_orchestrator().morning_briefing()


@app.post("/evening-checkin")
async def trigger_evening_checkin():
    return await get_orchestrator().evening_checkin()


@app.post("/checkin/answer")
async def submit_checkin_answer(question_id: str, answer: str):
    """AAA submits her answer to a profile question."""
    return await get_orchestrator().record_checkin_answer(question_id, answer)


@app.get("/profile/summary")
async def profile_summary():
    """Get JJ's current understanding of AAA."""
    orch = get_orchestrator()
    return {
        "summary": orch.profile.get_profile_summary(),
        "answer_count": orch.profile.get_answer_count(),
        "domain_coverage": orch.profile.get_domain_coverage(),
        "profile": orch.profile.synthesize_profile(),
    }


@app.post("/nightly-reconciliation")
async def trigger_nightly():
    from app.jobs.nightly_reconciliation import run_nightly_reconciliation
    return await run_nightly_reconciliation()


@app.post("/repo-audit")
async def trigger_repo_audit():
    from app.jobs.repo_audit_cycle import run_repo_audit
    return await run_repo_audit()


# ── PWA ────────────────────────────────────────────────────────────────
_STATIC_DIR = Path(__file__).parent / "static"


@app.get("/app")
async def pwa_index():
    return FileResponse(_STATIC_DIR / "index.html", media_type="text/html")


app.mount("/app", StaticFiles(directory=str(_STATIC_DIR)), name="pwa")
