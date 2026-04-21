-- Migration 021: Universal Memory Graph
CREATE TABLE IF NOT EXISTS jarvis_universe_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_universe_embeddings IS 'Semantic embeddings for graph nodes';

CREATE TABLE IF NOT EXISTS jarvis_universe_event_map (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_universe_event_map IS 'Event to graph node mapping';

CREATE TABLE IF NOT EXISTS jarvis_umg_traversal_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_umg_traversal_cache IS 'Cached graph traversal results';

CREATE TABLE IF NOT EXISTS jarvis_umg_statistics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_umg_statistics IS 'Graph statistics and health metrics';

CREATE TABLE IF NOT EXISTS jarvis_umg_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_umg_queries IS 'Stored graph queries';

ALTER TABLE jarvis_universe_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_universe_event_map ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_umg_traversal_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_umg_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_umg_queries ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_universe_embeddings' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_universe_embeddings FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_universe_event_map' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_universe_event_map FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_umg_traversal_cache' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_umg_traversal_cache FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_umg_statistics' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_umg_statistics FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'jarvis_umg_queries' AND policyname = 'allow_user') THEN
    CREATE POLICY "allow_user" ON jarvis_umg_queries FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_universe_embeddings_user_id ON jarvis_universe_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_universe_event_map_user_id ON jarvis_universe_event_map(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_umg_traversal_cache_user_id ON jarvis_umg_traversal_cache(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_umg_statistics_user_id ON jarvis_umg_statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_umg_queries_user_id ON jarvis_umg_queries(user_id);
