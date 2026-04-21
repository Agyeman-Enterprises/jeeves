-- Migration 022: Strategic Foresight Engine
CREATE TABLE IF NOT EXISTS jarvis_foresight_maps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_foresight_maps IS 'Strategic foresight maps';

CREATE TABLE IF NOT EXISTS jarvis_foresight_scenarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_foresight_scenarios IS 'Alternative future scenarios';

CREATE TABLE IF NOT EXISTS jarvis_foresight_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_foresight_alerts IS 'Proactive warnings from foresight';

CREATE TABLE IF NOT EXISTS jarvis_foresight_tracking (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_foresight_tracking IS 'Prediction accuracy tracking';

CREATE TABLE IF NOT EXISTS jarvis_foresight_interventions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_foresight_interventions IS 'Actions taken based on foresight';

ALTER TABLE jarvis_foresight_maps ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_foresight_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_foresight_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_foresight_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_foresight_interventions ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_foresight_maps' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_foresight_maps FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_foresight_scenarios' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_foresight_scenarios FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_foresight_alerts' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_foresight_alerts FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_foresight_tracking' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_foresight_tracking FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_foresight_interventions' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_foresight_interventions FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_foresight_maps_user_id ON jarvis_foresight_maps(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_foresight_scenarios_user_id ON jarvis_foresight_scenarios(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_foresight_alerts_user_id ON jarvis_foresight_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_foresight_tracking_user_id ON jarvis_foresight_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_foresight_interventions_user_id ON jarvis_foresight_interventions(user_id);
