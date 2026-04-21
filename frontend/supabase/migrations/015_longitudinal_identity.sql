-- Migration 015: Longitudinal Identity System
CREATE TABLE IF NOT EXISTS jarvis_longitudinal_identity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_longitudinal_identity IS 'Longitudinal identity model';

CREATE TABLE IF NOT EXISTS jarvis_identity_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_identity_patterns IS 'Detected identity patterns';

CREATE TABLE IF NOT EXISTS jarvis_identity_drift (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_identity_drift IS 'Identity drift detection';

CREATE TABLE IF NOT EXISTS jarvis_longitudinal_goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_longitudinal_goals IS 'Long-term goals tracking';

CREATE TABLE IF NOT EXISTS jarvis_core_values (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_core_values IS 'Core values and principles';

ALTER TABLE jarvis_longitudinal_identity ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_identity_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_identity_drift ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_longitudinal_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_core_values ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_longitudinal_identity'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_longitudinal_identity
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_identity_patterns'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_identity_patterns
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_identity_drift'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_identity_drift
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_longitudinal_goals'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_longitudinal_goals
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_core_values'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_core_values
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_longitudinal_identity_user_id ON jarvis_longitudinal_identity(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_identity_patterns_user_id ON jarvis_identity_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_identity_drift_user_id ON jarvis_identity_drift(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_longitudinal_goals_user_id ON jarvis_longitudinal_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_core_values_user_id ON jarvis_core_values(user_id);
