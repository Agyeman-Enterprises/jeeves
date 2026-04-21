-- IT-10A: Provider Intelligence Module (PIM) tables

-- RAW PROVIDER EVENTS
CREATE TABLE IF NOT EXISTS public.jarvis_pim_provider_events (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_event_id uuid UNIQUE, -- references the GEM event id, but we don't enforce FK to keep decoupling
  workspace_id    uuid NOT NULL,
  provider        text NOT NULL, -- e.g. 'ghexit'
  channel         text NOT NULL, -- 'sms' | 'mms' | 'email' | 'voice' | 'video' | etc.
  event_type      text NOT NULL, -- 'sent' | 'delivered' | 'failed' | 'started' | 'ended' | ...
  occurred_at     timestamptz NOT NULL,
  latency_ms      integer,
  error_code      text,
  error_group     text,     -- normalized error category: 'network', 'auth', 'throttle', 'remote', 'config', 'unknown'
  routing_path    jsonb,    -- e.g. { "primaryCarrier": "telnyx", "fallbackCarrier": null }
  metadata        jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jarvis_pim_provider_events_workspace_time
  ON public.jarvis_pim_provider_events (workspace_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_jarvis_pim_provider_events_provider_channel
  ON public.jarvis_pim_provider_events (provider, channel, occurred_at DESC);

COMMENT ON TABLE public.jarvis_pim_provider_events IS 'Raw normalized provider events for the Provider Intelligence Module (PIM).';

-- DAILY ROLLUPS PER PROVIDER + CHANNEL
CREATE TABLE IF NOT EXISTS public.jarvis_pim_daily_rollups (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL,
  provider        text NOT NULL,
  channel         text NOT NULL,
  date_bucket     date NOT NULL,
  messages_total  integer NOT NULL,
  messages_failed integer NOT NULL,
  avg_latency_ms  numeric,
  p95_latency_ms  numeric,
  p99_latency_ms  numeric,
  jitter_ms       numeric,
  health_score    numeric,     -- 0–1 heuristic health indicator
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_jarvis_pim_daily_rollups_key
  ON public.jarvis_pim_daily_rollups (workspace_id, provider, channel, date_bucket);

COMMENT ON TABLE public.jarvis_pim_daily_rollups IS 'Daily rollups of provider behavior for PIM: totals, latency, jitter, health.';

-- TIME-BUCKETED LATENCY CURVES
CREATE TABLE IF NOT EXISTS public.jarvis_pim_latency_curves (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL,
  provider        text NOT NULL,
  channel         text NOT NULL,
  time_bucket     timestamptz NOT NULL, -- e.g. hour bucket
  latency_p50_ms  numeric,
  latency_p90_ms  numeric,
  latency_p95_ms  numeric,
  latency_p99_ms  numeric,
  samples         integer NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jarvis_pim_latency_curves_workspace_time
  ON public.jarvis_pim_latency_curves (workspace_id, time_bucket DESC);

COMMENT ON TABLE public.jarvis_pim_latency_curves IS 'Latency distribution curves per provider/channel/time bucket for prediction and visualization.';

-- RLS Policies
ALTER TABLE public.jarvis_pim_provider_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_pim_daily_rollups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_pim_latency_curves ENABLE ROW LEVEL SECURITY;

-- RLS for jarvis_pim_provider_events
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_pim_provider_events'
      AND policyname = 'jarvis_pim_provider_events_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_pim_provider_events_allow_workspace_members"
      ON public.jarvis_pim_provider_events
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_pim_provider_events.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_pim_provider_events'
      AND policyname = 'jarvis_pim_provider_events_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_pim_provider_events_allow_workspace_members_mod"
      ON public.jarvis_pim_provider_events
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_pim_provider_events.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_pim_provider_events.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_pim_daily_rollups
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_pim_daily_rollups'
      AND policyname = 'jarvis_pim_daily_rollups_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_pim_daily_rollups_allow_workspace_members"
      ON public.jarvis_pim_daily_rollups
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_pim_daily_rollups.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_pim_latency_curves
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_pim_latency_curves'
      AND policyname = 'jarvis_pim_latency_curves_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_pim_latency_curves_allow_workspace_members"
      ON public.jarvis_pim_latency_curves
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_pim_latency_curves.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

