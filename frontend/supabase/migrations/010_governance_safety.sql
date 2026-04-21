-- Migration 010: Governance and Safety
CREATE TABLE IF NOT EXISTS jarvis_agent_permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_permissions IS 'Permission matrix for agents';

CREATE TABLE IF NOT EXISTS jarvis_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_audit_log IS 'Immutable audit log of all actions';

CREATE TABLE IF NOT EXISTS jarvis_kill_switches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_kill_switches IS 'Emergency kill switches for agents and domains';

ALTER TABLE jarvis_agent_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_kill_switches ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_permissions'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_permissions
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_audit_log'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_audit_log
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_kill_switches'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_kill_switches
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_agent_permissions_user_id ON jarvis_agent_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_audit_log_user_id ON jarvis_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_kill_switches_user_id ON jarvis_kill_switches(user_id);
