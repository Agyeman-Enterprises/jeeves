-- IT-14: Incident Playbooks & Self-Repair Orchestrator

CREATE TABLE IF NOT EXISTS public.jarvis_incident_playbooks (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id     uuid NOT NULL,
  name             text NOT NULL,
  description      text,
  is_enabled       boolean NOT NULL DEFAULT true,
  trigger_source   text NOT NULL, -- 'alert' | 'agent' | 'manual'
  trigger_matcher  jsonb NOT NULL, -- loosely-typed matcher object
  default_severity text NOT NULL DEFAULT 'medium',
  steps            jsonb NOT NULL, -- array of { index, type, config }
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incident_playbooks_workspace
  ON public.jarvis_incident_playbooks (workspace_id, is_enabled);

COMMENT ON TABLE public.jarvis_incident_playbooks IS 'Reusable incident playbooks with trigger matchers and step sequences.';

CREATE TABLE IF NOT EXISTS public.jarvis_incidents (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id  uuid NOT NULL,
  playbook_id   uuid REFERENCES public.jarvis_incident_playbooks(id),
  status        text NOT NULL, -- 'open' | 'in_progress' | 'resolved' | 'cancelled'
  severity      text NOT NULL,
  title         text NOT NULL,
  description   text,
  context       jsonb,
  opened_at     timestamptz NOT NULL DEFAULT now(),
  resolved_at   timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incidents_workspace_time
  ON public.jarvis_incidents (workspace_id, opened_at DESC);

COMMENT ON TABLE public.jarvis_incidents IS 'Concrete incident instances created from alerts/agents/manual.';

CREATE TABLE IF NOT EXISTS public.jarvis_incident_steps (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id  uuid NOT NULL REFERENCES public.jarvis_incidents(id) ON DELETE CASCADE,
  step_index   integer NOT NULL,
  step_type    text NOT NULL, -- 'notify' | 'agentAction' | 'runAgentRule' | 'wait' | ...
  status       text NOT NULL, -- 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  config       jsonb NOT NULL,
  result       jsonb,
  started_at   timestamptz,
  completed_at timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incident_steps_incident_order
  ON public.jarvis_incident_steps (incident_id, step_index);

COMMENT ON TABLE public.jarvis_incident_steps IS 'Materialized steps for incidents, mapped from their playbooks.';

-- RLS Policies
ALTER TABLE public.jarvis_incident_playbooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_incident_steps ENABLE ROW LEVEL SECURITY;

-- RLS for jarvis_incident_playbooks
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_incident_playbooks'
      AND policyname = 'jarvis_incident_playbooks_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_incident_playbooks_allow_workspace_members"
      ON public.jarvis_incident_playbooks
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incident_playbooks.workspace_id
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
      AND tablename = 'jarvis_incident_playbooks'
      AND policyname = 'jarvis_incident_playbooks_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_incident_playbooks_allow_workspace_members_mod"
      ON public.jarvis_incident_playbooks
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incident_playbooks.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incident_playbooks.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR DELETE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incident_playbooks.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_incidents
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_incidents'
      AND policyname = 'jarvis_incidents_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_incidents_allow_workspace_members"
      ON public.jarvis_incidents
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incidents.workspace_id
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
      AND tablename = 'jarvis_incidents'
      AND policyname = 'jarvis_incidents_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_incidents_allow_workspace_members_mod"
      ON public.jarvis_incidents
      FOR INSERT WITH CHECK (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incidents.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR UPDATE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incidents.workspace_id
          AND m.user_id = auth.uid()
        )
      )
      FOR DELETE USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_incidents.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_incident_steps
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_incident_steps'
      AND policyname = 'jarvis_incident_steps_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_incident_steps_allow_workspace_members"
      ON public.jarvis_incident_steps
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_incidents i
          JOIN public.jarvis_workspace_members m ON m.workspace_id = i.workspace_id
          WHERE i.id = jarvis_incident_steps.incident_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

