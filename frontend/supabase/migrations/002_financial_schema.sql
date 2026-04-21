-- Migration 002: Financial Schema
CREATE TABLE IF NOT EXISTS nexus_financial_entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE nexus_financial_entities IS 'Financial entities (LLCs, clinics, businesses)';

CREATE TABLE IF NOT EXISTS nexus_financial_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE nexus_financial_transactions IS 'Financial transactions across all entities';

CREATE TABLE IF NOT EXISTS nexus_financial_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE nexus_financial_snapshots IS 'Periodic financial snapshots for entities';

CREATE TABLE IF NOT EXISTS nexus_tax_positions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE nexus_tax_positions IS 'Tax positions and estimates per entity';

ALTER TABLE nexus_financial_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE nexus_financial_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE nexus_financial_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE nexus_tax_positions ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'nexus_financial_entities'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON nexus_financial_entities
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'nexus_financial_transactions'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON nexus_financial_transactions
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'nexus_financial_snapshots'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON nexus_financial_snapshots
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'nexus_tax_positions'
      AND policyname = 'allow_user'
  ) THEN
    CREATE POLICY "allow_user" ON nexus_tax_positions
      FOR ALL USING (auth.uid() IS NOT NULL);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_nexus_financial_entities_user_id ON nexus_financial_entities(user_id);
CREATE INDEX IF NOT EXISTS idx_nexus_financial_transactions_user_id ON nexus_financial_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_nexus_financial_snapshots_user_id ON nexus_financial_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_nexus_tax_positions_user_id ON nexus_tax_positions(user_id);
