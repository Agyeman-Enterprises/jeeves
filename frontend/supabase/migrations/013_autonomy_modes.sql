-- Migration 013: Autonomy Modes
CREATE TABLE IF NOT EXISTS jarvis_autonomy_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_autonomy_settings IS 'Global and domain-specific autonomy settings';

CREATE TABLE IF NOT EXISTS jarvis_domain_autonomy (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_domain_autonomy IS 'Autonomy settings per domain';

CREATE TABLE IF NOT EXISTS jarvis_agent_autonomy (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_autonomy IS 'Autonomy settings per agent';

CREATE TABLE IF NOT EXISTS jarvis_task_autonomy (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_task_autonomy IS 'Autonomy settings per task type';

CREATE TABLE IF NOT EXISTS jarvis_autonomy_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_autonomy_history IS 'History of autonomy mode changes';

CREATE TABLE IF NOT EXISTS jarvis_autonomy_calibration (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_autonomy_calibration IS 'Autonomy calibration data';

ALTER TABLE jarvis_autonomy_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_domain_autonomy ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_autonomy ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_task_autonomy ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_autonomy_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_autonomy_calibration ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_autonomy_settings'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_autonomy_settings
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_domain_autonomy'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_domain_autonomy
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_autonomy'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_autonomy
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_task_autonomy'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_task_autonomy
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_autonomy_history'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_autonomy_history
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_autonomy_calibration'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_autonomy_calibration
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_autonomy_settings_user_id ON jarvis_autonomy_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_domain_autonomy_user_id ON jarvis_domain_autonomy(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_autonomy_user_id ON jarvis_agent_autonomy(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_task_autonomy_user_id ON jarvis_task_autonomy(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_autonomy_history_user_id ON jarvis_autonomy_history(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_autonomy_calibration_user_id ON jarvis_autonomy_calibration(user_id);
