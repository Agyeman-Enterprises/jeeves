-- Migration 005: Briefing System
CREATE TABLE IF NOT EXISTS jarvis_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_signals IS 'Processed signals for briefing system';

CREATE TABLE IF NOT EXISTS jarvis_briefings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_briefings IS 'Daily/weekly/monthly briefings';

CREATE TABLE IF NOT EXISTS jarvis_briefing_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_briefing_preferences IS 'User preferences for briefings';

CREATE TABLE IF NOT EXISTS jarvis_timeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_timeline_events IS 'Chronological timeline of events';

CREATE TABLE IF NOT EXISTS jarvis_system_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_system_events IS 'System-level events';

ALTER TABLE jarvis_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_briefings ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_briefing_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_timeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_system_events ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_signals'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_signals
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_briefings'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_briefings
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_briefing_preferences'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_briefing_preferences
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_timeline_events'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_timeline_events
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_system_events'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_system_events
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_signals_user_id ON jarvis_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_briefings_user_id ON jarvis_briefings(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_briefing_preferences_user_id ON jarvis_briefing_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_timeline_events_user_id ON jarvis_timeline_events(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_system_events_user_id ON jarvis_system_events(user_id);
