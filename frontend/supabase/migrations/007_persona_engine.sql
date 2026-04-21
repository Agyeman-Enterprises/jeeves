-- Migration 007: Persona Engine
CREATE TABLE IF NOT EXISTS jarvis_personas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_personas IS 'Persona definitions for multi-identity framework';

CREATE TABLE IF NOT EXISTS jarvis_identity_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_identity_profile IS 'Core identity profile for user';

CREATE TABLE IF NOT EXISTS jarvis_persona_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_persona_rules IS 'Rules for persona selection and adaptation';

CREATE TABLE IF NOT EXISTS jarvis_emotional_context (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_emotional_context IS 'Emotional context for persona adaptation';

ALTER TABLE jarvis_personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_identity_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_persona_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_emotional_context ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_personas'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_personas
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_identity_profile'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_identity_profile
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_persona_rules'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_persona_rules
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_emotional_context'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_emotional_context
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_personas_user_id ON jarvis_personas(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_identity_profile_user_id ON jarvis_identity_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_persona_rules_user_id ON jarvis_persona_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_emotional_context_user_id ON jarvis_emotional_context(user_id);
