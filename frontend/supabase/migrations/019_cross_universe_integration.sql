-- Migration 019: Cross-Universe Integration
CREATE TABLE IF NOT EXISTS jarvis_universe_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_universe_nodes IS 'Universal graph nodes across all universes';

CREATE TABLE IF NOT EXISTS jarvis_universe_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_universe_edges IS 'Relationships between universe nodes';

CREATE TABLE IF NOT EXISTS jarvis_cross_universe_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_cross_universe_events IS 'Events that span multiple universes';

CREATE TABLE IF NOT EXISTS jarvis_cross_predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_cross_predictions IS 'Predictions spanning multiple universes';

CREATE TABLE IF NOT EXISTS jarvis_cross_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_cross_recommendations IS 'Recommendations spanning multiple universes';

CREATE TABLE IF NOT EXISTS jarvis_universe_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_universe_snapshots IS 'System-wide state snapshots';

CREATE TABLE IF NOT EXISTS jarvis_cross_agent_coordination (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_cross_agent_coordination IS 'Cross-universe agent coordination';

ALTER TABLE jarvis_universe_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_universe_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_cross_universe_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_cross_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_cross_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_universe_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_cross_agent_coordination ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_universe_nodes'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_universe_nodes
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_universe_edges'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_universe_edges
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_cross_universe_events'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_cross_universe_events
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_cross_predictions'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_cross_predictions
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_cross_recommendations'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_cross_recommendations
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_universe_snapshots'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_universe_snapshots
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_cross_agent_coordination'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_cross_agent_coordination
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_universe_nodes_user_id ON jarvis_universe_nodes(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_universe_edges_user_id ON jarvis_universe_edges(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_cross_universe_events_user_id ON jarvis_cross_universe_events(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_cross_predictions_user_id ON jarvis_cross_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_cross_recommendations_user_id ON jarvis_cross_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_universe_snapshots_user_id ON jarvis_universe_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_cross_agent_coordination_user_id ON jarvis_cross_agent_coordination(user_id);
