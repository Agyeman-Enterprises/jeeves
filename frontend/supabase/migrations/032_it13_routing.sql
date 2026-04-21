-- IT-13: Provider Routing Brain

CREATE TABLE IF NOT EXISTS public.jarvis_routing_providers (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL,
  provider_key    text NOT NULL, -- e.g. 'ghexit', 'twilio', 'sendgrid'
  channel         text NOT NULL, -- 'sms' | 'email' | 'voice' | etc.
  display_name    text,
  base_weight     numeric NOT NULL DEFAULT 1,
  region          text,          -- e.g. 'us', 'eu'
  cost_per_unit   numeric,       -- optional, e.g. $ per sms
  status          text NOT NULL DEFAULT 'active', -- 'active' | 'disabled' | 'degraded'
  is_default      boolean NOT NULL DEFAULT false,
  metadata        jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_jarvis_routing_providers_key
  ON public.jarvis_routing_providers (workspace_id, channel, provider_key);

CREATE INDEX IF NOT EXISTS idx_jarvis_routing_providers_workspace_channel
  ON public.jarvis_routing_providers (workspace_id, channel);

COMMENT ON TABLE public.jarvis_routing_providers IS 'Per-workspace routing provider configuration for each channel.';

CREATE TABLE IF NOT EXISTS public.jarvis_routing_policies (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id      uuid NOT NULL,
  channel           text NOT NULL,  -- 'sms' | 'email' | etc.
  strategy          text NOT NULL,  -- 'weighted' | 'latency_optimized' | 'cost_optimized' | 'failover'
  health_threshold  numeric NOT NULL DEFAULT 0.6,
  max_failure_rate  numeric NOT NULL DEFAULT 0.05,
  max_latency_ms    integer NOT NULL DEFAULT 1500,
  prefer_low_cost   boolean NOT NULL DEFAULT false,
  metadata          jsonb,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_jarvis_routing_policies_workspace_channel
  ON public.jarvis_routing_policies (workspace_id, channel);

COMMENT ON TABLE public.jarvis_routing_policies IS 'Per-workspace routing policies for channels.';

CREATE TABLE IF NOT EXISTS public.jarvis_routing_decisions (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id         uuid NOT NULL,
  channel              text NOT NULL,
  request_id           text,
  chosen_provider_key  text,
  strategy             text,
  score                numeric,
  reason               text,
  snapshot             jsonb,
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jarvis_routing_decisions_workspace_time
  ON public.jarvis_routing_decisions (workspace_id, created_at DESC);

COMMENT ON TABLE public.jarvis_routing_decisions IS 'Log of routing decisions taken by the routing brain.';

-- RLS Policies
ALTER TABLE public.jarvis_routing_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_routing_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_routing_decisions ENABLE ROW LEVEL SECURITY;

-- RLS for jarvis_routing_providers
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_routing_providers'
      AND policyname = 'jarvis_routing_providers_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_routing_providers_allow_workspace_members"
      ON public.jarvis_routing_providers
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_providers.workspace_id
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
      AND tablename = 'jarvis_routing_providers'
      AND policyname = 'jarvis_routing_providers_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_routing_providers_allow_workspace_members_mod"
      ON public.jarvis_routing_providers
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_providers.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_providers.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR DELETE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_providers.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_routing_policies
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_routing_policies'
      AND policyname = 'jarvis_routing_policies_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_routing_policies_allow_workspace_members"
      ON public.jarvis_routing_policies
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_policies.workspace_id
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
      AND tablename = 'jarvis_routing_policies'
      AND policyname = 'jarvis_routing_policies_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_routing_policies_allow_workspace_members_mod"
      ON public.jarvis_routing_policies
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_policies.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_policies.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR DELETE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_policies.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_routing_decisions
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_routing_decisions'
      AND policyname = 'jarvis_routing_decisions_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_routing_decisions_allow_workspace_members"
      ON public.jarvis_routing_decisions
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_routing_decisions.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

