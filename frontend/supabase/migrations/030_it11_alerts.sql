-- IT-11: Alerts & Notifications System

CREATE TABLE IF NOT EXISTS public.jarvis_alert_rules (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id         uuid NOT NULL,
  name                 text NOT NULL,
  description          text,
  is_enabled           boolean NOT NULL DEFAULT true,
  rule_type            text NOT NULL,  -- 'prediction_threshold' | 'anomaly_watch'
  source               text NOT NULL,  -- e.g. 'prediction:latency', 'prediction:failure_rate', 'anomaly:aim'
  condition            jsonb NOT NULL, -- rule-specific config (metric, comparator, threshold, etc.)
  channel              text NOT NULL,  -- 'log' | 'sms' | 'email' | 'webhook' | ...
  target               text,           -- email/phone/webhook URL/etc.
  min_interval_seconds integer NOT NULL DEFAULT 300,
  last_triggered_at    timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jarvis_alert_rules_workspace
  ON public.jarvis_alert_rules (workspace_id);

CREATE INDEX IF NOT EXISTS idx_jarvis_alert_rules_enabled
  ON public.jarvis_alert_rules (workspace_id, is_enabled);

COMMENT ON TABLE public.jarvis_alert_rules IS 'Per-workspace alert rules for prediction thresholds and anomalies.';

CREATE TABLE IF NOT EXISTS public.jarvis_alert_events (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id     uuid NOT NULL,
  rule_id          uuid NOT NULL REFERENCES public.jarvis_alert_rules (id) ON DELETE CASCADE,
  triggered_at     timestamptz NOT NULL,
  event_type       text NOT NULL,        -- 'prediction_threshold' | 'anomaly_detected'
  payload          jsonb NOT NULL,       -- snapshot of triggering data
  delivery_channel text NOT NULL,        -- e.g. 'log', 'sms', 'email', 'webhook'
  delivery_status  text NOT NULL,        -- 'pending' | 'sent' | 'failed' | 'skipped'
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jarvis_alert_events_workspace_time
  ON public.jarvis_alert_events (workspace_id, triggered_at DESC);

COMMENT ON TABLE public.jarvis_alert_events IS 'Alert events generated when rules fire.';

-- RLS Policies
ALTER TABLE public.jarvis_alert_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_alert_events ENABLE ROW LEVEL SECURITY;

-- RLS for jarvis_alert_rules
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_alert_rules'
      AND policyname = 'jarvis_alert_rules_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_alert_rules_allow_workspace_members"
      ON public.jarvis_alert_rules
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_alert_rules.workspace_id
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
      AND tablename = 'jarvis_alert_rules'
      AND policyname = 'jarvis_alert_rules_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_alert_rules_allow_workspace_members_mod"
      ON public.jarvis_alert_rules
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_alert_rules.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_alert_rules.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR DELETE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_alert_rules.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_alert_events
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_alert_events'
      AND policyname = 'jarvis_alert_events_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_alert_events_allow_workspace_members"
      ON public.jarvis_alert_events
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_alert_events.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

