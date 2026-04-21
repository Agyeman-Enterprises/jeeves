-- Migration 008: Memory and Journal
CREATE TABLE IF NOT EXISTS jarvis_memory_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_memory_chunks IS 'Memory chunks with embeddings for retrieval';

CREATE TABLE IF NOT EXISTS jarvis_journal_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE jarvis_journal_entries IS 'Journal entries for narrative memory';

ALTER TABLE jarvis_memory_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE jarvis_journal_entries ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_memory_chunks'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_memory_chunks
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'jarvis_journal_entries'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON jarvis_journal_entries
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_jarvis_memory_chunks_user_id ON jarvis_memory_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_journal_entries_user_id ON jarvis_journal_entries(user_id);
