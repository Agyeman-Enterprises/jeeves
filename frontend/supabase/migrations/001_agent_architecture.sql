-- Migration 001: Agent Architecture
CREATE TABLE IF NOT EXISTS jarvis_agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agents IS 'Agent registry for all Jarvis agents';

CREATE TABLE IF NOT EXISTS jarvis_agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_runs IS 'Agent execution runs and task queue';

CREATE TABLE IF NOT EXISTS jarvis_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_plans IS 'Execution plans created by Jarvis';

CREATE TABLE IF NOT EXISTS jarvis_plan_steps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_plan_steps IS 'Individual steps within execution plans';

ALTER TABLE jarvis_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_plan_steps ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agents'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agents
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_runs'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_runs
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_plans'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_plans
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_plan_steps'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_plan_steps
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_agents_user_id ON jarvis_agents(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_runs_user_id ON jarvis_agent_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_plans_user_id ON jarvis_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_plan_steps_user_id ON jarvis_plan_steps(user_id);
