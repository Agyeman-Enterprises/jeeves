# JJ Merge Plan — Jeeves + JARVIS → JJ (Single Source of Truth)
# ae-enforcement contract compliant — READ → PLAN → APPROVE → EXECUTE → VERIFY

---

## 1. What I Read (every file opened)

- `C:\DEV\jeeves\app\config.py` — Settings, env prefix JEEVES_, all integration URLs
- `C:\DEV\jeeves\app\db.py` — Supabase client, returns None when unconfigured (graceful)
- `C:\DEV\jeeves\app\main.py` — 5 routers, APScheduler 4 jobs, health endpoint
- `C:\DEV\jeeves\app\core\orchestrator.py` — Central dispatcher, 182 lines, real
- `C:\DEV\jeeves\app\core\profile_builder.py` — 45-question profile system, DB-wired
- `C:\DEV\jeeves\app\core\suggestion_engine.py` — 6 suggestion types, real
- `C:\DEV\jeeves\app\core\planner.py` — Day plan from goals + calendar, real
- `C:\DEV\jeeves\app\core\context_assembler.py` — Builds LLM context from DB + Aqui
- `C:\DEV\jeeves\app\services\action_dispatcher.py` — HTTP dispatch to ContentForge etc.
- `C:\DEV\jeeves\app\services\google_service.py` — Gmail + Calendar OAuth, real
- `C:\DEV\jeeves\app\memory\aqui_client.py` — External HTTP to Aqui pgvector (fragile)
- `C:\DEV\jeeves\app\agents\__init__.py` — EMPTY, no agents implemented
- `C:\DEV\jeeves\GATE7.txt` — Sections A/B/C checked, D/E/F(partial)/G unchecked
- `C:\DEV\jeeves\requirements.txt` — 9 deps, no langgraph/mem0/anthropic
- `C:\DEV\jeeves\Dockerfile` — Port 4004, CMD uvicorn
- `C:\DEV\jeeves\.env` — All JEEVES_ vars set, Supabase URL confirmed tzjygaxpzrtevlnganjs
- `C:\DEV\Jarvis\backend\brain\mimograph.py` — 15K lines, uses SUPABASE_URL/KEY direct, jarvis_brain_* tables
- `C:\DEV\Jarvis\backend\brain\user_model.py` — 17K lines, SEED_GOALS, jarvis_brain_* tables
- `C:\DEV\Jarvis\backend\agents\base.py` — BaseAgent ABC, AgentResponse dataclass
- `C:\DEV\Jarvis\backend\core\jang_graph.py` — LangGraph state machine, imports backend.core.*
- `C:\DEV\Jarvis\backend\core\jang_state.py` — JANGState TypedDict
- `C:\DEV\Jarvis\.github\workflows\gate-check.yml` — Real CI gate, copy to Jeeves
- `C:\DEV\Jarvis\.claude\GATE_PASSED` — Plain text, NOT a real GATE_CERT.json
- `tzjygaxpzrtevlnganjs` schema — 14 tables: jeeves_goals(14 rows), jeeves_belief_nodes(17),
  jeeves_belief_edges(11), jeeves_events(7), jeeves_profile_answers(0), jeeves_preferences(22),
  jeeves_patterns(6), jeeves_state(4), jeeves_suggestions(0), jeeves_actions(0),
  jeeves_approvals(0), jeeves_resources(3), jeeves_meal_plans(0), jeeves_behavioral_evidence(0)
  RLS DISABLED on: jeeves_profile_answers, jeeves_behavioral_evidence, jeeves_goals,
  jeeves_belief_nodes, jeeves_belief_edges, jeeves_events

---

## 2. What I Found (actual state, no assumptions)

### Jeeves (base — C:\DEV\jeeves)
- WORKING: orchestrator, profile_builder, suggestion_engine, planner, context_assembler,
  action_dispatcher, google_service, aqui_client, morning_cycle, nightly_reconciliation,
  repo_audit_cycle — all real implementations
- BROKEN/MISSING: agents/ is empty, db.py returns None (correct behavior but callers
  must be verified), Aqui is single point of failure (no fallback)
- ENFORCEMENT GAPS: no .github/, no scripts/run-gate.sh, no gate7-map.json, no PLAN_APPROVED
- DB: correctly pointed at tzjygaxpzrtevlnganjs, 14 tables with live data
- SECURITY: 6 tables have RLS disabled — jeeves_profile_answers, jeeves_behavioral_evidence,
  jeeves_goals, jeeves_belief_nodes, jeeves_belief_edges, jeeves_events
- CONFIG BUG: jarviscore_supabase_url and jarviscore_service_role_key in config.py —
  JarvisCore is now FormPilot and has nothing to do with JJ

### JARVIS (donor — C:\DEV\Jarvis)
- WORKING: 37+ agents, brain/ (mimograph + user_model), jang_graph, jang_state, BaseAgent,
  all services (email, calendar, finance, RAG), all routes
- BROKEN: brain/ files use `SUPABASE_URL` direct env vars (not JEEVES_ prefix), use
  `jarvis_brain_*` table names (don't exist in JJ DB — JJ uses `jeeves_*` tables),
  all imports use `backend.*` paths (must change to `app.*`)
- JOBS: empty — no scheduler. Jeeves has the scheduler.
- GATE: .claude/GATE_PASSED is plain text, not a real cert. JARVIS code is unverified.

### Critical architectural problem being solved
Jeeves on Hetzner called Aqui on Hetzner. Hetzner went down = both dead simultaneously.
JJ fix: add mem0 as local memory tier. When Aqui is unreachable, fall back to mem0.
Memory never goes fully dark again.

---

## 3. What I Will Change (specific files, exact reason per phase)

### Phase 0 — Enforcement setup (unblock implementation)
- CREATE `.github/workflows/gate-check.yml` — copy from JARVIS, required for CI
- CREATE `scripts/run-gate.sh` — copy from ae-enforcement, required for gate execution
- CREATE `gate7-map.json` — map every GATE7.txt checkbox to spec
- FIX `app/config.py` — remove jarviscore_supabase_url, jarviscore_service_role_key
- FIX RLS — enable RLS on 6 tables, add service-role bypass policy
- CREATE `.claude/PLAN_APPROVED` — Akua said go

### Phase 1 — Brain port
- CREATE `app/brain/__init__.py`
- CREATE `app/brain/user_model.py` — port from JARVIS backend/brain/user_model.py
  CHANGES: `backend.*` → `app.*` imports, `jarvis_brain_goals` → `jeeves_goals`,
  `jarvis_brain_traits` → `jeeves_belief_nodes`, use app.db.get_db() not raw os.getenv
- CREATE `app/brain/mimograph.py` — port from JARVIS backend/brain/mimograph.py
  CHANGES: same import + table renames, remove hardcoded SUPABASE_URL/KEY
- CREATE `app/api/brain.py` — 11 brain endpoints (observe, briefing, questions, etc.)
- MODIFY `app/main.py` — register brain router
- UPDATE `requirements.txt` — add any new deps from brain modules

### Phase 2 — Agents port
- CREATE `app/agents/base.py` — copy from JARVIS backend/agents/base.py (no changes needed)
- CREATE `app/agents/` all 37 domain agents — update `backend.*` → `app.*` imports
- CREATE `app/agents/masters/` — all 13 master agents
- CREATE `app/agents/specialists/` — all specialist sub-agents
- MODIFY `app/core/orchestrator.py` — register and route to agents

### Phase 3 — Memory resilience (mem0 + JJ DB)
- CREATE `app/memory/mem0_service.py` — port from JARVIS backend/memory/mem0_service.py
  CHANGES: update imports, wire to JEEVES_ config keys, store vectors in JJ DB
- MODIFY `app/memory/aqui_client.py` — wrap all calls in try/except, fall back to mem0
- MODIFY `app/core/context_assembler.py` — use resilient memory client
- UPDATE `requirements.txt` — add mem0ai
NOTE: All persistent state in JJ DB (tzjygaxpzrtevlnganjs). Aqui = external, addressed separately.

### Phase 4 — JANG port
- CREATE `app/core/jang_state.py` — copy from JARVIS backend/core/jang_state.py
- CREATE `app/core/jang_graph.py` — port from JARVIS backend/core/jang_graph.py
  CHANGES: `backend.*` → `app.*` imports
- CREATE `app/api/jang.py` — LangGraph chat endpoint
- MODIFY `app/main.py` — register jang router
- UPDATE `requirements.txt` — add langgraph

### Phase 5 — Services port
- CREATE `app/services/email_service.py` — port from JARVIS (Gmail + Outlook)
- CREATE `app/services/calendar_service.py` — port from JARVIS
- CREATE `app/services/finance_service.py` — port from JARVIS (Plaid/Stripe/Square)
- CREATE `app/services/rag_service.py` — port from JARVIS
- UPDATE `requirements.txt` — add new service deps

### Phase 6 — Routes + Scheduler
- CREATE `app/api/empire.py` — morning ritual, service health aggregation
- MODIFY `app/jobs/morning_cycle.py` — wire to brain/mimograph for richer briefings
- MODIFY `app/jobs/nightly_reconciliation.py` — wire to user_model observations
- MODIFY `app/main.py` — register empire router

### Phase 7 — GATE7 update + deploy
- REWRITE `GATE7.txt` — update to JJ scope (adds brain, agents, JANG, memory fallback)
- Run all 9 gates
- Fix failures
- Deploy via Coolify to port 4004

### Phase 8 — v2.1.0: Frontend Migration + Dual-Write Sync Layer (APPROVED ADDENDUM)

Owner instruction: "MIGRATE ALL — merge Jeeves and JARVIS. data written to both docker and
supabase. if one is down, write to log and update without data loss when it comes back."

#### 8a — Frontend Migration
- COPY `C:\DEV\Jarvis\frontend\` → `C:\DEV\jeeves\frontend\`
- REWRITE `frontend/app/api/jarvis/route.ts` → routes to JJ `/jang/chat` (port 4004)
- REWRITE `frontend/app/api/jarvis/personal/route.ts` → reads `jeeves_events` + `jeeves_tasks`
- REWRITE `frontend/app/api/jarvis/timeline/route.ts` → reads `jeeves_signals` via Supabase
- REWRITE `frontend/app/api/jarvis/priorities/route.ts` → reads `/brain/goals` from JJ
- EXTEND `frontend/app/api/proxy/[...path]/route.ts` → default URL port 4004, add DELETE/PATCH/PUT
- UPDATE `frontend/.env.local` → `tzjygaxpzrtevlnganjs`, `localhost:4004`
- UPDATE `frontend/.env.production` → `tzjygaxpzrtevlnganjs`, `jeeves.agyemanenterprises.com`
- CREATE `frontend/Dockerfile` — Next.js container with build args for JJ Supabase + backend URL

#### 8b — Compat Router
- CREATE `app/api/compat.py` — maps old JARVIS frontend paths to JJ equivalents:
  /agents/status, /api/empire/status, /api/empire/portfolio, /api/knowledge/stats,
  /api/knowledge/search, /api/graph/entities, /api/jobs (full CRUD on jeeves_tasks),
  /briefing/today, /api/personality/core, /query→/jang/chat, /api/system/status
- MODIFY `app/main.py` — register compat_router

#### 8c — Dual-Write Sync Layer
- CREATE `app/memory/sync_manager.py` — SyncManager class:
  Cloud (Supabase tzjygaxpzrtevlnganjs) = primary authority, always written first.
  Local (mem0/Qdrant) = secondary replica. On local failure: queue in jj_sync_queue.
  Methods: write_memory(), write_reflection(), write_preference(), log_agent_run(),
  log_action(), emit_signal(), search_memory()
- CREATE `app/jobs/sync_recovery.py` — drains jj_sync_queue when Docker returns.
  Runs at startup + every 15min via APScheduler.
- MODIFY `app/main.py` — register sync_recovery in APScheduler
- MODIFY `app/core/jang_graph.py` — wire write_back_node to use get_sync_manager()
  instead of calling mem.add() directly. All conversation memory goes through
  dual-write layer.

#### 8d — New Supabase Tables (tzjygaxpzrtevlnganjs)
Six tables required for v2.1.0:
  - jeeves_agent_runs — agent execution log
  - jeeves_action_logs — dispatched action log
  - jeeves_tasks — task CRUD (exposed via /api/jobs)
  - jeeves_journal_entries — journal store
  - jeeves_signals — timeline events + dual-write primary store for memory
  - jj_sync_queue — pending local writes when Docker is down

Migration file: supabase/migrations/001_jj_v210_tables.sql

#### 8e — Dependency updates
- ADD to requirements.txt: pytest>=8.0.0, pytest-asyncio>=0.23.0 (test framework)
- All other deps (anthropic, langgraph, mem0ai) already in requirements.txt

#### 8f — Tests
- CREATE `tests/__init__.py`
- CREATE `tests/test_sync_manager.py` — cloud write succeeds, local failure queues,
  search_memory falls back to cloud
- CREATE `tests/test_sync_recovery.py` — pending queue item drained and marked synced

---

## 4. What I Will NOT Touch

- `app/core/profile_builder.py` — working, no changes needed
- `app/core/suggestion_engine.py` — working, no changes needed
- `app/core/planner.py` — working, no changes needed
- `app/services/google_service.py` — working OAuth, no changes needed
- `app/services/action_dispatcher.py` — working, no changes needed
- `app/integrations/` — all 4 clients working
- `app/db.py` — correct design, no changes
- `Dockerfile` — port 4004 correct, no changes
- JARVIS Next.js frontend — MIGRATED to jeeves/frontend/ in Phase 8a (owner order: merge all)
- JarvisCore/FormPilot Supabase (rcyekqufeautozmiljoq) — not touched
- Aqui pgvector (Hetzner) — not touched, only adding fallback around it
- Any other project in C:\DEV — this plan is Jeeves-only scope

---

## 5. How I Will Verify (behavioral tests per phase, not build passing)

### Phase 0 verification
- `curl http://localhost:4004/health` returns 200 (no regression)
- `scripts/run-gate.sh` executes without "file not found"
- RLS verified: anonymous HTTP request to jeeves_goals returns 403

### Phase 1 verification
- `POST /ingest/observe` → records to DB → `GET /brain/profile` returns it
- `GET /brain/briefing` → returns LLM-generated text with retirement countdown
- `GET /brain/goals` → returns 14 goals from jeeves_goals with effective_weight ranked
- `GET /brain/contradictions` → returns detected contradictions

### Phase 2 verification
- `POST /chat {"message": "what should I work on today?"}` → response cites specific goals
- `POST /chat {"message": "check my email"}` → email agent fires, returns real count
- Each agent's `handle()` returns an `AgentResponse` (not raises)

### Phase 3 verification
- Stop Aqui service (or point to dead URL) → `POST /chat` still returns a response
  (falls back to mem0, not 500 error)
- Restore Aqui → `POST /chat` uses Aqui again automatically

### Phase 4 verification
- `POST /jang/chat {"message": "run my morning ritual"}` → LangGraph executes
  retrieve_memory → synthesize → reflect nodes without error

### Phase 5 verification
- `GET /email/summary` → returns real unread count from Gmail
- `GET /finance/summary` → returns balance data (Plaid/Stripe)

### Phase 6 + 7 verification
- All GATE7.txt checkboxes pass
- `scripts/run-gate.sh` shows all 9 gates PASS
- Docker image builds, container starts, /health returns 200
- Coolify deploy succeeds, jeeves.agyemanenterprises.com responds
