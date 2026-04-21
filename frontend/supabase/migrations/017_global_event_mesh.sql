-- Migration 017: Global Event Mesh
CREATE TABLE IF NOT EXISTS jarvis_event_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_event_routes IS 'Event routing configuration';

CREATE TABLE IF NOT EXISTS jarvis_event_mesh_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_event_mesh_events IS 'All events flowing through GEM';

CREATE TABLE IF NOT EXISTS jarvis_event_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_event_subscriptions IS 'Event subscriptions for agents/systems';

CREATE TABLE IF NOT EXISTS jarvis_event_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_event_deliveries IS 'Event delivery tracking';

CREATE TABLE IF NOT EXISTS jarvis_event_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_event_patterns IS 'Detected event patterns';

ALTER TABLE jarvis_event_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_event_mesh_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_event_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_event_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_event_patterns ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_event_routes'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_event_routes
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_event_mesh_events'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_event_mesh_events
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_event_subscriptions'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_event_subscriptions
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_event_deliveries'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_event_deliveries
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_event_patterns'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_event_patterns
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_event_routes_user_id ON jarvis_event_routes(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_event_mesh_events_user_id ON jarvis_event_mesh_events(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_event_subscriptions_user_id ON jarvis_event_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_event_deliveries_user_id ON jarvis_event_deliveries(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_event_patterns_user_id ON jarvis_event_patterns(user_id);
