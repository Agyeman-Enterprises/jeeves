-- IT-12: Agent Trigger System (Auto-Action Engine)

CREATE TABLE IF NOT EXISTS public.jarvis_agent_rules (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id         uuid NOT NULL,
  name                 text NOT NULL,
  description          text,
  is_enabled           boolean NOT NULL DEFAULT true,
  trigger_type         text NOT NULL,  -- 'prediction_threshold' | 'anomaly_trigger'
  source               text NOT NULL,  -- e.g. 'prediction:latency', 'prediction:failure_rate', 'anomaly:aim'
  condition            jsonb NOT NULL, -- structure depends on trigger_type
  action               jsonb NOT NULL, -- action definition {type: "...", ...}
  min_interval_seconds integer NOT NULL DEFAULT 300,
  last_triggered_at    timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_rules_workspace_enabled
  ON public.jarvis_agent_rules (workspace_id, is_enabled);

COMMENT ON TABLE public.jarvis_agent_rules IS 'Agent trigger rules for auto-actions.';

CREATE TABLE IF NOT EXISTS public.jarvis_agent_executions (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id     uuid NOT NULL,
  rule_id          uuid NOT NULL REFERENCES public.jarvis_agent_rules(id) ON DELETE CASCADE,
  triggered_at     timestamptz NOT NULL,
  action_type      text NOT NULL,
  action_payload   jsonb NOT NULL,
  result_status    text NOT NULL,  -- 'success' | 'failed' | 'skipped'
  result_detail    jsonb,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_workspace_time
  ON public.jarvis_agent_executions (workspace_id, triggered_at DESC);

COMMENT ON TABLE public.jarvis_agent_executions IS 'Execution log for agent rules.';

-- RLS Policies
ALTER TABLE public.jarvis_agent_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_agent_executions ENABLE ROW LEVEL SECURITY;

-- RLS for jarvis_agent_rules
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_agent_rules'
      AND policyname = 'jarvis_agent_rules_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_agent_rules_allow_workspace_members"
      ON public.jarvis_agent_rules
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_agent_rules.workspace_id
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
      AND tablename = 'jarvis_agent_rules'
      AND policyname = 'jarvis_agent_rules_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_agent_rules_allow_workspace_members_mod"
      ON public.jarvis_agent_rules
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_agent_rules.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_agent_rules.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR DELETE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_agent_rules.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_agent_executions
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_agent_executions'
      AND policyname = 'jarvis_agent_executions_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_agent_executions_allow_workspace_members"
      ON public.jarvis_agent_executions
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_agent_executions.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

