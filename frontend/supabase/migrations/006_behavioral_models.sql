-- Migration 006: Behavioral Models
CREATE TABLE IF NOT EXISTS jarvis_behavior_vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_behavior_vectors IS 'Behavioral vector representations';

CREATE TABLE IF NOT EXISTS jarvis_decision_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_decision_logs IS 'Log of user decisions for learning';

CREATE TABLE IF NOT EXISTS jarvis_communication_examples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_communication_examples IS 'Examples of user communication style';

CREATE TABLE IF NOT EXISTS jarvis_preference_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_preference_rules IS 'Learned preference rules';

CREATE TABLE IF NOT EXISTS jarvis_behavior_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_behavior_patterns IS 'Detected behavior patterns';

CREATE TABLE IF NOT EXISTS jarvis_error_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_error_events IS 'Error events for analysis';

CREATE TABLE IF NOT EXISTS jarvis_root_causes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_root_causes IS 'Root cause analysis results';

ALTER TABLE jarvis_behavior_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_decision_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_communication_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_preference_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_behavior_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_error_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_root_causes ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_behavior_vectors'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_behavior_vectors
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_decision_logs'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_decision_logs
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_communication_examples'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_communication_examples
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_preference_rules'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_preference_rules
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_behavior_patterns'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_behavior_patterns
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_error_events'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_error_events
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_root_causes'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_root_causes
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_behavior_vectors_user_id ON jarvis_behavior_vectors(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_decision_logs_user_id ON jarvis_decision_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_communication_examples_user_id ON jarvis_communication_examples(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_preference_rules_user_id ON jarvis_preference_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_behavior_patterns_user_id ON jarvis_behavior_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_error_events_user_id ON jarvis_error_events(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_root_causes_user_id ON jarvis_root_causes(user_id);
