-- Migration 014: Emotional Intelligence
CREATE TABLE IF NOT EXISTS jarvis_mental_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_mental_state IS 'Real-time mental state tracking';

CREATE TABLE IF NOT EXISTS jarvis_behavioral_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_behavioral_signals IS 'Behavioral signals for state modeling';

CREATE TABLE IF NOT EXISTS jarvis_energy_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_energy_patterns IS 'Energy pattern learning';

CREATE TABLE IF NOT EXISTS jarvis_state_adaptations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_state_adaptations IS 'Adaptations based on mental state';

CREATE TABLE IF NOT EXISTS jarvis_emotional_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_emotional_rules IS 'Rules for emotional intelligence';

CREATE TABLE IF NOT EXISTS jarvis_support_mode (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_support_mode IS 'Support mode activation state';

ALTER TABLE jarvis_mental_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_behavioral_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_energy_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_state_adaptations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_emotional_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_support_mode ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_mental_state'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_mental_state
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_behavioral_signals'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_behavioral_signals
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_energy_patterns'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_energy_patterns
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_state_adaptations'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_state_adaptations
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_emotional_rules'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_emotional_rules
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_support_mode'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_support_mode
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_mental_state_user_id ON jarvis_mental_state(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_behavioral_signals_user_id ON jarvis_behavioral_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_energy_patterns_user_id ON jarvis_energy_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_state_adaptations_user_id ON jarvis_state_adaptations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_emotional_rules_user_id ON jarvis_emotional_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_support_mode_user_id ON jarvis_support_mode(user_id);
