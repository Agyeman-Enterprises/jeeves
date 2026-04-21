-- IT-10B: Activity Intelligence Module (AIM) tables

-- PER-USER DAILY ACTIVITY
CREATE TABLE IF NOT EXISTS public.jarvis_aim_user_activity (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id      uuid NOT NULL,
  user_id           uuid NOT NULL,
  date_bucket       date NOT NULL,
  messages_sent     integer NOT NULL DEFAULT 0,
  messages_received integer NOT NULL DEFAULT 0,
  calls_made        integer NOT NULL DEFAULT 0,
  calls_received    integer NOT NULL DEFAULT 0,
  emails_sent       integer NOT NULL DEFAULT 0,
  emails_received   integer NOT NULL DEFAULT 0,
  active_minutes    integer NOT NULL DEFAULT 0,
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_jarvis_aim_user_activity_key
  ON public.jarvis_aim_user_activity (workspace_id, user_id, date_bucket);

CREATE INDEX IF NOT EXISTS idx_jarvis_aim_user_activity_workspace_date
  ON public.jarvis_aim_user_activity (workspace_id, date_bucket DESC);

COMMENT ON TABLE public.jarvis_aim_user_activity IS 'Per-user, per-day activity summaries for AIM (messages, calls, emails, approximate engagement).';

-- PER-WORKSPACE DAILY COMMUNICATION CYCLES
CREATE TABLE IF NOT EXISTS public.jarvis_aim_enterprise_cycles (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id        uuid NOT NULL,
  date_bucket         date NOT NULL,
  msg_total           integer NOT NULL,
  call_total          integer NOT NULL,
  email_total         integer NOT NULL,
  peak_hour_local     integer,        -- 0–23
  off_peak_hour_local integer,        -- 0–23
  weekday_pattern     jsonb,          -- optional, for future use
  cycle_score         numeric,        -- 0–1, how "regular" behavior is
  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_jarvis_aim_enterprise_cycles_key
  ON public.jarvis_aim_enterprise_cycles (workspace_id, date_bucket);

CREATE INDEX IF NOT EXISTS idx_jarvis_aim_enterprise_cycles_workspace_date
  ON public.jarvis_aim_enterprise_cycles (workspace_id, date_bucket DESC);

COMMENT ON TABLE public.jarvis_aim_enterprise_cycles IS 'Per-workspace daily communication cycles (volume, peaks, regularity).';

-- ANOMALIES
CREATE TABLE IF NOT EXISTS public.jarvis_aim_anomalies (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL,
  entity_type     text NOT NULL,  -- 'user' | 'workspace'
  entity_id       uuid,           -- null if entity_type = 'workspace'
  detected_at     timestamptz NOT NULL,
  anomaly_type    text NOT NULL,  -- e.g. 'volume_spike', 'volume_drop'
  severity        numeric NOT NULL,  -- 0–1
  baseline_window text NOT NULL,  -- e.g. '7d', '30d'
  notes           text,
  raw_metrics     jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jarvis_aim_anomalies_workspace_time
  ON public.jarvis_aim_anomalies (workspace_id, detected_at DESC);

COMMENT ON TABLE public.jarvis_aim_anomalies IS 'AIM anomalies detected for users and workspaces.';

-- RLS Policies
ALTER TABLE public.jarvis_aim_user_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_aim_enterprise_cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_aim_anomalies ENABLE ROW LEVEL SECURITY;

-- RLS for jarvis_aim_user_activity
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_aim_user_activity'
      AND policyname = 'jarvis_aim_user_activity_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_aim_user_activity_allow_workspace_members"
      ON public.jarvis_aim_user_activity
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_aim_user_activity.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_aim_enterprise_cycles
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_aim_enterprise_cycles'
      AND policyname = 'jarvis_aim_enterprise_cycles_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_aim_enterprise_cycles_allow_workspace_members"
      ON public.jarvis_aim_enterprise_cycles
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_aim_enterprise_cycles.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

-- RLS for jarvis_aim_anomalies
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_aim_anomalies'
      AND policyname = 'jarvis_aim_anomalies_allow_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_aim_anomalies_allow_workspace_members"
      ON public.jarvis_aim_anomalies
      FOR SELECT USING (
        EXISTS (
          SELECT 1 FROM public.jarvis_workspace_members m
          WHERE m.workspace_id = jarvis_aim_anomalies.workspace_id
          AND m.user_id = auth.uid()
        )
      );
  END IF;
END$$;

