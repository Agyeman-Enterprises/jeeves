-- Migration 003: Agent Lifecycle
ALTER TABLE jarvis_agents
  ADD COLUMN IF NOT EXISTS status TEXT,
  ADD COLUMN IF NOT EXISTS last_heartbeat TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS attempt_count INT,
  ADD COLUMN IF NOT EXISTS max_attempts INT;

ALTER TABLE jarvis_agent_runs
  ADD COLUMN IF NOT EXISTS attempt_count INT,
  ADD COLUMN IF NOT EXISTS max_attempts INT,
  ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_error_kind TEXT;

CREATE INDEX IF NOT EXISTS idx_jarvis_agents_status ON jarvis_agents(status);
CREATE INDEX IF NOT EXISTS idx_jarvis_agents_last_heartbeat ON jarvis_agents(last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_runs_attempt_count ON jarvis_agent_runs(attempt_count);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_runs_next_attempt_at ON jarvis_agent_runs(next_attempt_at);
