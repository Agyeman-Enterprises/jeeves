-- Migration 009: Action Layer
CREATE TABLE IF NOT EXISTS jarvis_action_policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_action_policies IS 'Policies governing autonomous actions';

CREATE TABLE IF NOT EXISTS jarvis_action_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_action_logs IS 'Log of all actions taken by Jarvis';

CREATE TABLE IF NOT EXISTS jarvis_action_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_action_approvals IS 'User approvals for actions';

ALTER TABLE jarvis_action_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_action_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_action_approvals ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_action_policies'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_action_policies
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_action_logs'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_action_logs
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_action_approvals'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_action_approvals
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_action_policies_user_id ON jarvis_action_policies(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_action_logs_user_id ON jarvis_action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_action_approvals_user_id ON jarvis_action_approvals(user_id);
