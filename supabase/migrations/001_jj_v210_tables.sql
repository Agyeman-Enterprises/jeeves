-- ============================================================
-- JJ v2.1.0 — New Tables Migration
-- Project: tzjygaxpzrtevlnganjs
-- Applied: 2026-04-21
-- Description: Frontend migration + dual-write sync layer tables
-- ============================================================

-- ── jeeves_agent_runs ─────────────────────────────────────────────────────────
-- Logs every agent execution: name, task, status, result, timing.
CREATE TABLE IF NOT EXISTS jeeves_agent_runs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name  TEXT NOT NULL,
    task        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'running',  -- running | success | failed
    result      JSONB,
    error       TEXT,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

ALTER TABLE jeeves_agent_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON jeeves_agent_runs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ── jeeves_action_logs ────────────────────────────────────────────────────────
-- Records every dispatched action (HTTP calls to ContentForge, AlrtMe, etc.)
CREATE TABLE IF NOT EXISTS jeeves_action_logs (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action    TEXT NOT NULL,
    agent     TEXT,
    payload   JSONB NOT NULL DEFAULT '{}',
    result    JSONB,
    status    TEXT NOT NULL DEFAULT 'success',  -- success | failed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE jeeves_action_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON jeeves_action_logs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ── jeeves_tasks ──────────────────────────────────────────────────────────────
-- Task CRUD — exposed via /api/jobs compat endpoint and frontend /jarvis/jobs
CREATE TABLE IF NOT EXISTS jeeves_tasks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT NOT NULL,
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'pending',  -- pending | running | completed | failed
    priority     INTEGER NOT NULL DEFAULT 5,        -- 1 (highest) to 10 (lowest)
    due_date     DATE,
    related_goal TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE jeeves_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON jeeves_tasks
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ── jeeves_journal_entries ────────────────────────────────────────────────────
-- Daily journal entries from Akua (text + structured mood/energy metadata)
CREATE TABLE IF NOT EXISTS jeeves_journal_entries (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content    TEXT NOT NULL,
    mood       TEXT,            -- positive | neutral | negative
    energy     INTEGER,         -- 1–10
    tags       TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE jeeves_journal_entries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON jeeves_journal_entries
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ── jeeves_signals ────────────────────────────────────────────────────────────
-- Timeline events + primary durable store for dual-write memory layer.
-- Every memory write (conversation, fact, reflection) lands here first.
CREATE TABLE IF NOT EXISTS jeeves_signals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_type TEXT NOT NULL,   -- mem0_add | mem0_reflect | mem0_preference | event | alert
    source      TEXT NOT NULL,   -- jj_memory | agent_name | jang | external
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE jeeves_signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON jeeves_signals
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_jeeves_signals_created_at ON jeeves_signals (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jeeves_signals_signal_type ON jeeves_signals (signal_type);

-- ── jj_sync_queue ─────────────────────────────────────────────────────────────
-- Pending local writes when Docker/Hetzner is down.
-- sync_recovery job drains this table when Docker comes back online.
CREATE TABLE IF NOT EXISTS jj_sync_queue (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation   TEXT NOT NULL,   -- mem0_add | mem0_reflect | mem0_preference
    payload     JSONB NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending | synced | failed
    attempts    INTEGER NOT NULL DEFAULT 0,
    last_error  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    synced_at   TIMESTAMPTZ
);

ALTER TABLE jj_sync_queue ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON jj_sync_queue
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_jj_sync_queue_status ON jj_sync_queue (status) WHERE status = 'pending';
