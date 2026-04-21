-- Migration 024: Autonomous Co-Pilot Mode
CREATE TABLE IF NOT EXISTS jarvis_copilot_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_copilot_state IS 'Current state of co-pilot mode';

CREATE TABLE IF NOT EXISTS jarvis_autonomous_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_autonomous_actions IS 'Log of all autonomous actions';

CREATE TABLE IF NOT EXISTS jarvis_copilot_coordination (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_copilot_coordination IS 'System-wide coordination actions';

CREATE TABLE IF NOT EXISTS jarvis_mode_transitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_mode_transitions IS 'Mode transition history';

CREATE TABLE IF NOT EXISTS jarvis_copilot_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_copilot_metrics IS 'Co-pilot performance metrics';

ALTER TABLE jarvis_copilot_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_autonomous_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_copilot_coordination ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_mode_transitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_copilot_metrics ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_copilot_state' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_copilot_state FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_autonomous_actions' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_autonomous_actions FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_copilot_coordination' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_copilot_coordination FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_mode_transitions' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_mode_transitions FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_copilot_metrics' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_copilot_metrics FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_copilot_state_user_id ON jarvis_copilot_state(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_autonomous_actions_user_id ON jarvis_autonomous_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_copilot_coordination_user_id ON jarvis_copilot_coordination(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_mode_transitions_user_id ON jarvis_mode_transitions(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_copilot_metrics_user_id ON jarvis_copilot_metrics(user_id);
