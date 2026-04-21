-- Migration 041: Complete memory schema
-- Adds missing content columns to jarvis_memory_chunks and jarvis_journal_entries
-- These tables were created in 008 with only id/user_id/timestamps — no content.

ALTER TABLE jarvis_memory_chunks
  ADD COLUMN IF NOT EXISTS session_id   TEXT,
  ADD COLUMN IF NOT EXISTS role         TEXT CHECK (role IN ('user', 'assistant', 'system')),
  ADD COLUMN IF NOT EXISTS content      TEXT,
  ADD COLUMN IF NOT EXISTS agent        TEXT,
  ADD COLUMN IF NOT EXISTS importance   SMALLINT DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
  ADD COLUMN IF NOT EXISTS source       TEXT DEFAULT 'chat';

ALTER TABLE jarvis_journal_entries
  ADD COLUMN IF NOT EXISTS session_id   TEXT,
  ADD COLUMN IF NOT EXISTS entry_type   TEXT DEFAULT 'reflection',
  ADD COLUMN IF NOT EXISTS content      TEXT,
  ADD COLUMN IF NOT EXISTS summary      TEXT,
  ADD COLUMN IF NOT EXISTS tags         TEXT[] DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_jarvis_memory_session   ON jarvis_memory_chunks(session_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_memory_role      ON jarvis_memory_chunks(role);
CREATE INDEX IF NOT EXISTS idx_jarvis_memory_created   ON jarvis_memory_chunks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jarvis_journal_session  ON jarvis_journal_entries(session_id);
