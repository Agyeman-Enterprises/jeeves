-- Migration 023: Self-Refactoring & Modular Brain Evolution
CREATE TABLE IF NOT EXISTS jarvis_self_audits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_self_audits IS 'Daily self-audit results';

CREATE TABLE IF NOT EXISTS jarvis_refactoring_proposals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_refactoring_proposals IS 'Proposed architectural improvements';

CREATE TABLE IF NOT EXISTS jarvis_refactoring_implementations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_refactoring_implementations IS 'Refactoring implementation tracking';

CREATE TABLE IF NOT EXISTS jarvis_refactoring_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_refactoring_performance IS 'Post-refactoring performance tracking';

CREATE TABLE IF NOT EXISTS jarvis_agent_evolution (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_evolution IS 'Agent evolution tracking';

CREATE TABLE IF NOT EXISTS jarvis_schema_evolution (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_schema_evolution IS 'Database schema evolution tracking';

ALTER TABLE jarvis_self_audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_refactoring_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_refactoring_implementations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_refactoring_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_evolution ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_schema_evolution ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_self_audits' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_self_audits FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_refactoring_proposals' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_refactoring_proposals FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_refactoring_implementations' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_refactoring_implementations FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_refactoring_performance' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_refactoring_performance FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_agent_evolution' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_agent_evolution FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_schema_evolution' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_schema_evolution FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_self_audits_user_id ON jarvis_self_audits(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_refactoring_proposals_user_id ON jarvis_refactoring_proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_refactoring_implementations_user_id ON jarvis_refactoring_implementations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_refactoring_performance_user_id ON jarvis_refactoring_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_evolution_user_id ON jarvis_agent_evolution(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_schema_evolution_user_id ON jarvis_schema_evolution(user_id);
