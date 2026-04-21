-- Migration 020: Cognitive Economy & Resource Allocation
CREATE TABLE IF NOT EXISTS jarvis_cognitive_budgets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_cognitive_budgets IS 'Daily cognitive resource allocation';

CREATE TABLE IF NOT EXISTS jarvis_resource_allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_resource_allocations IS 'Resource allocation records';

CREATE TABLE IF NOT EXISTS jarvis_resource_constraints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_resource_constraints IS 'Resource constraints and limits';

CREATE TABLE IF NOT EXISTS jarvis_strategic_priority_maps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_strategic_priority_maps IS 'Weekly strategic priority maps';

CREATE TABLE IF NOT EXISTS jarvis_agent_resource_allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_resource_allocations IS 'Agent resource allocation';

CREATE TABLE IF NOT EXISTS jarvis_financial_allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_financial_allocations IS 'Financial resource allocation';

CREATE TABLE IF NOT EXISTS jarvis_allocation_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_allocation_recommendations IS 'Resource allocation recommendations';

ALTER TABLE jarvis_cognitive_budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_resource_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_resource_constraints ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_strategic_priority_maps ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_resource_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_financial_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_allocation_recommendations ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_cognitive_budgets' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_cognitive_budgets FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_resource_allocations' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_resource_allocations FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_resource_constraints' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_resource_constraints FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_strategic_priority_maps' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_strategic_priority_maps FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_agent_resource_allocations' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_agent_resource_allocations FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_financial_allocations' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_financial_allocations FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_allocation_recommendations' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_allocation_recommendations FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_cognitive_budgets_user_id ON jarvis_cognitive_budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_resource_allocations_user_id ON jarvis_resource_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_resource_constraints_user_id ON jarvis_resource_constraints(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_strategic_priority_maps_user_id ON jarvis_strategic_priority_maps(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_resource_allocations_user_id ON jarvis_agent_resource_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_financial_allocations_user_id ON jarvis_financial_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_allocation_recommendations_user_id ON jarvis_allocation_recommendations(user_id);
