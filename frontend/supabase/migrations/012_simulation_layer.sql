-- Migration 012: Simulation Layer
CREATE TABLE IF NOT EXISTS jarvis_simulations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_simulations IS 'Simulation runs';

CREATE TABLE IF NOT EXISTS jarvis_simulation_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_simulation_results IS 'Simulation results';

CREATE TABLE IF NOT EXISTS jarvis_clinical_sim_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_clinical_sim_models IS 'Clinical simulation models';

CREATE TABLE IF NOT EXISTS jarvis_financial_sim_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_financial_sim_models IS 'Financial simulation models';

CREATE TABLE IF NOT EXISTS jarvis_operational_sim_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_operational_sim_models IS 'Operational simulation models';

CREATE TABLE IF NOT EXISTS jarvis_risk_sim_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_risk_sim_models IS 'Risk simulation models';

CREATE TABLE IF NOT EXISTS jarvis_agent_load_sims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_agent_load_sims IS 'Agent load balancing simulations';

CREATE TABLE IF NOT EXISTS jarvis_strategic_scenarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_strategic_scenarios IS 'Strategic scenario planning';

ALTER TABLE jarvis_simulations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_simulation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_clinical_sim_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_financial_sim_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_operational_sim_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_risk_sim_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_agent_load_sims ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_strategic_scenarios ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_simulations'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_simulations
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_simulation_results'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_simulation_results
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_clinical_sim_models'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_clinical_sim_models
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_financial_sim_models'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_financial_sim_models
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_operational_sim_models'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_operational_sim_models
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_risk_sim_models'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_risk_sim_models
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_agent_load_sims'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_agent_load_sims
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_strategic_scenarios'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_strategic_scenarios
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_simulations_user_id ON jarvis_simulations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_simulation_results_user_id ON jarvis_simulation_results(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_clinical_sim_models_user_id ON jarvis_clinical_sim_models(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_financial_sim_models_user_id ON jarvis_financial_sim_models(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_operational_sim_models_user_id ON jarvis_operational_sim_models(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_risk_sim_models_user_id ON jarvis_risk_sim_models(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_agent_load_sims_user_id ON jarvis_agent_load_sims(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_strategic_scenarios_user_id ON jarvis_strategic_scenarios(user_id);
