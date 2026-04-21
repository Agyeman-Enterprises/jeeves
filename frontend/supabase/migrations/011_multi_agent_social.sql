-- Migration 011: Multi-Agent Social Layer
CREATE TABLE IF NOT EXISTS jarvis_agent_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_messages IS 'Inter-agent messages';

CREATE TABLE IF NOT EXISTS jarvis_agent_coordination (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_coordination IS 'Agent coordination events';

CREATE TABLE IF NOT EXISTS jarvis_agent_conflicts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_conflicts IS 'Agent conflict resolution log';

CREATE TABLE IF NOT EXISTS jarvis_agent_dependencies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_dependencies IS 'Agent dependency graph';

CREATE TABLE IF NOT EXISTS jarvis_agent_locks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_locks IS 'Resource locks for parallel execution';

CREATE TABLE IF NOT EXISTS jarvis_executive_coordinators (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_executive_coordinators IS 'Executive coordinator agents';

CREATE TABLE IF NOT EXISTS jarvis_agent_queues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_queues IS 'Agent task queues';

CREATE TABLE IF NOT EXISTS jarvis_agent_collaborations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_collaborations IS 'Agent collaboration records';

ALTER TABLE jarvis_agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_coordination ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_conflicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_locks ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_executive_coordinators ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_queues ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_collaborations ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_messages'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_messages
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_coordination'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_coordination
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_conflicts'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_conflicts
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_dependencies'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_dependencies
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_locks'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_locks
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_executive_coordinators'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_executive_coordinators
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_queues'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_queues
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_collaborations'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_collaborations
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_agent_messages_user_id ON jarvis_agent_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_coordination_user_id ON jarvis_agent_coordination(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_conflicts_user_id ON jarvis_agent_conflicts(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_dependencies_user_id ON jarvis_agent_dependencies(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_locks_user_id ON jarvis_agent_locks(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_executive_coordinators_user_id ON jarvis_executive_coordinators(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_queues_user_id ON jarvis_agent_queues(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_collaborations_user_id ON jarvis_agent_collaborations(user_id);
