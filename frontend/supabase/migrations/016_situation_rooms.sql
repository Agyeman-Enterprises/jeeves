-- Migration 016: Situation Rooms
CREATE TABLE IF NOT EXISTS jarvis_situation_room_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_situation_room_snapshots IS 'Situation room state snapshots';

CREATE TABLE IF NOT EXISTS jarvis_situation_room_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_situation_room_alerts IS 'Alerts from situation rooms';

CREATE TABLE IF NOT EXISTS jarvis_situation_room_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_situation_room_recommendations IS 'Recommendations from situation rooms';

CREATE TABLE IF NOT EXISTS jarvis_situation_room_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_situation_room_metrics IS 'Metrics from situation rooms';

ALTER TABLE jarvis_situation_room_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_situation_room_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_situation_room_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_situation_room_metrics ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_situation_room_snapshots'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_situation_room_snapshots
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_situation_room_alerts'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_situation_room_alerts
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_situation_room_recommendations'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_situation_room_recommendations
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_situation_room_metrics'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_situation_room_metrics
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_situation_room_snapshots_user_id ON jarvis_situation_room_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_situation_room_alerts_user_id ON jarvis_situation_room_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_situation_room_recommendations_user_id ON jarvis_situation_room_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_situation_room_metrics_user_id ON jarvis_situation_room_metrics(user_id);
