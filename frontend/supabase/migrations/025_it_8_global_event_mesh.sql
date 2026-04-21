-- IT-8: Global Event Mesh v0
-- jarvis_events, jarvis_event_subscriptions, jarvis_event_deliveries

-- ===========================
-- jarvis_events
-- ===========================

CREATE TABLE IF NOT EXISTS public.jarvis_events (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id   uuid NOT NULL,
  user_id        uuid NOT NULL,
  event_type     text NOT NULL,
  source         text NOT NULL, -- e.g. 'jarvis.command', 'nexus.analytics', 'external.webhook'
  subject_id     text,          -- arbitrary id of entity (task id, message id, etc)
  correlation_id uuid,          -- to link multiple events in one workflow
  causation_id   uuid,          -- id of the event that caused this one
  payload        jsonb NOT NULL,
  status         text NOT NULL DEFAULT 'stored', -- 'stored', 'dispatched', 'failed'
  error_message  text,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.jarvis_events IS
  'Global Event Mesh v0: append-only log of all Jarvis/Nexus events with typed payloads.';

CREATE INDEX IF NOT EXISTS idx_jarvis_events_workspace_created_at
  ON public.jarvis_events (workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_jarvis_events_type_created_at
  ON public.jarvis_events (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_jarvis_events_correlation_id
  ON public.jarvis_events (correlation_id);

CREATE INDEX IF NOT EXISTS idx_jarvis_events_subject_id
  ON public.jarvis_events (subject_id);

-- RLS
ALTER TABLE public.jarvis_events ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_events'
      AND policyname = 'jarvis_events_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_events_allow_workspace_members"
      ON public.jarvis_events
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_events'
      AND policyname = 'jarvis_events_allow_workspace_members_ins_upd'
  ) THEN
    CREATE POLICY "jarvis_events_allow_workspace_members_ins_upd"
      ON public.jarvis_events
      FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR UPDATE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

-- ===========================
-- jarvis_event_subscriptions
-- ===========================

CREATE TABLE IF NOT EXISTS public.jarvis_event_subscriptions (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id   uuid NOT NULL,
  user_id        uuid NOT NULL,
  name           text NOT NULL, -- human-readable label
  event_type     text NOT NULL, -- which event type(s) this subscription is for (v0: single type)
  filter_expr    jsonb,         -- future: structured filters (e.g., by subject_id or payload fields)
  handler_key    text NOT NULL, -- e.g. 'nexus.analytics', 'notifications', 'situation-room'
  is_active      boolean NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.jarvis_event_subscriptions IS
  'Subscriptions to GEM events. v0 is mostly for internal routing, but allows future user-defined subscriptions.';

CREATE INDEX IF NOT EXISTS idx_jarvis_event_subscriptions_workspace
  ON public.jarvis_event_subscriptions (workspace_id, event_type);

ALTER TABLE public.jarvis_event_subscriptions ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_event_subscriptions'
      AND policyname = 'jarvis_event_subs_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_event_subs_allow_workspace_members"
      ON public.jarvis_event_subscriptions
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_event_subscriptions'
      AND policyname = 'jarvis_event_subs_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_event_subs_allow_workspace_members_mod"
      ON public.jarvis_event_subscriptions
      FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR UPDATE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR DELETE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

-- ===========================
-- jarvis_event_deliveries
-- ===========================

CREATE TABLE IF NOT EXISTS public.jarvis_event_deliveries (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id   uuid NOT NULL,
  user_id        uuid NOT NULL,
  event_id       uuid NOT NULL REFERENCES public.jarvis_events(id) ON DELETE CASCADE,
  subscription_id uuid, -- nullable: internal handlers may not have a subscription row
  handler_key    text NOT NULL,
  status         text NOT NULL DEFAULT 'pending', -- 'pending', 'success', 'failed'
  attempts       integer NOT NULL DEFAULT 0,
  last_error     text,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.jarvis_event_deliveries IS
  'Tracks delivery attempts for GEM events to internal/external handlers.';

CREATE INDEX IF NOT EXISTS idx_jarvis_event_deliveries_event
  ON public.jarvis_event_deliveries (event_id);

CREATE INDEX IF NOT EXISTS idx_jarvis_event_deliveries_workspace_status
  ON public.jarvis_event_deliveries (workspace_id, status);

ALTER TABLE public.jarvis_event_deliveries ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_event_deliveries'
      AND policyname = 'jarvis_event_deliveries_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_event_deliveries_allow_workspace_members"
      ON public.jarvis_event_deliveries
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_event_deliveries'
      AND policyname = 'jarvis_event_deliveries_allow_workspace_members_mod'
  ) THEN
    CREATE POLICY "jarvis_event_deliveries_allow_workspace_members_mod"
      ON public.jarvis_event_deliveries
      FOR INSERT WITH CHECK (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR UPDATE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      )
      FOR DELETE USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          workspace_id IN (
            SELECT workspace_id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END$$;

