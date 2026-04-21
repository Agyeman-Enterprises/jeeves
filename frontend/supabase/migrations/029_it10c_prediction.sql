-- IT-10C: Prediction Engine cache table

CREATE TABLE IF NOT EXISTS public.jarvis_prediction_cache (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL,
  prediction_type text NOT NULL,  -- 'latency' | 'failure_rate' | 'spend' | 'routing' | others
  target_key      text NOT NULL,  -- e.g. 'ghexit:sms', 'ghexit:email', 'workspace:all'
  horizon         text NOT NULL,  -- e.g. '24h', '1d', '7d'
  result          jsonb NOT NULL,
  computed_at     timestamptz NOT NULL DEFAULT now(),
  valid_until     timestamptz NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_jarvis_prediction_cache_key
  ON public.jarvis_prediction_cache (workspace_id, prediction_type, target_key, horizon);

CREATE INDEX IF NOT EXISTS idx_jarvis_prediction_cache_valid
  ON public.jarvis_prediction_cache (workspace_id, prediction_type, valid_until DESC);

COMMENT ON TABLE public.jarvis_prediction_cache IS 'Cached predictions for Jarvis (latency, failures, spend, routing, etc.)';

-- RLS Policies
ALTER TABLE public.jarvis_prediction_cache ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_prediction_cache'
      AND policyname = 'jarvis_prediction_cache_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_prediction_cache_allow_workspace_members"
      ON public.jarvis_prediction_cache
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_prediction_cache.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

