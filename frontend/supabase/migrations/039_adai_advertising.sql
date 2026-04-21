-- Migration 039: AdAI Advertising Automation Tables
-- Adds tables for the AdAI Nexus sub-agent (advertising automation)
-- Replaces PredisAI with custom-built advertising management

-- ============================================================================
-- adai_platform_connections: Store Meta/Google/TikTok ad account credentials
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_platform_connections (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id      uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  platform          text NOT NULL CHECK (platform IN ('meta', 'google', 'tiktok')),
  account_id        text NOT NULL,
  account_name      text,
  access_token      text, -- Encrypted token (consider moving to vault)
  token_expires_at  timestamptz,
  scopes            jsonb DEFAULT '[]'::jsonb,
  status            text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'expired', 'revoked', 'error')),
  last_health_check timestamptz,
  last_sync_at      timestamptz,
  error_message     text,
  metadata          jsonb DEFAULT '{}'::jsonb,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id, platform, account_id)
);

COMMENT ON TABLE public.adai_platform_connections IS 'Ad platform connections (Meta, Google, TikTok) per workspace';
COMMENT ON COLUMN public.adai_platform_connections.access_token IS 'OAuth access token - consider encrypting or using vault';
COMMENT ON COLUMN public.adai_platform_connections.status IS 'Connection health: pending, active, expired, revoked, error';

CREATE INDEX IF NOT EXISTS idx_adai_platform_connections_workspace ON public.adai_platform_connections(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_platform_connections_status ON public.adai_platform_connections(status);

-- ============================================================================
-- adai_policies: Per-workspace governance rules for ad automation
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_policies (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id              uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  daily_spend_cap           numeric(12,2) DEFAULT 50.00,
  campaign_spend_cap        numeric(12,2),
  adset_spend_cap           numeric(12,2),
  target_cpa                numeric(12,2),
  target_roas               numeric(6,2),
  min_evidence_spend        numeric(12,2) DEFAULT 50.00,
  min_evidence_conversions  integer DEFAULT 3,
  min_evidence_impressions  integer DEFAULT 5000,
  scale_step_percent        numeric(5,2) DEFAULT 20.00,
  cooldown_hours            integer DEFAULT 24,
  requires_approval_above   numeric(12,2) DEFAULT 50.00,
  auto_pause_on_anomaly     boolean DEFAULT true,
  notify_email              text,
  metadata                  jsonb DEFAULT '{}'::jsonb,
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id)
);

COMMENT ON TABLE public.adai_policies IS 'Ad automation governance policies per workspace';
COMMENT ON COLUMN public.adai_policies.requires_approval_above IS 'Spend changes above this amount require manual approval';
COMMENT ON COLUMN public.adai_policies.cooldown_hours IS 'Minimum hours between significant changes to same entity';

CREATE INDEX IF NOT EXISTS idx_adai_policies_workspace ON public.adai_policies(workspace_id);

-- ============================================================================
-- adai_launch_specs: Campaign templates for quick deployment
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_launch_specs (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id          uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  name                  text NOT NULL,
  platform              text NOT NULL CHECK (platform IN ('meta', 'google', 'tiktok')),
  objective             text CHECK (objective IN ('conversions', 'traffic', 'awareness', 'engagement', 'leads', 'app_installs')),
  targeting             jsonb DEFAULT '{}'::jsonb,
  budget_config         jsonb DEFAULT '{}'::jsonb,
  creative_requirements jsonb DEFAULT '{}'::jsonb,
  brand_kit_ref         text,
  compliance_rules      jsonb DEFAULT '{}'::jsonb,
  is_active             boolean DEFAULT true,
  metadata              jsonb DEFAULT '{}'::jsonb,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_launch_specs IS 'Reusable campaign templates for quick ad deployment';

CREATE INDEX IF NOT EXISTS idx_adai_launch_specs_workspace ON public.adai_launch_specs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_launch_specs_platform ON public.adai_launch_specs(platform);

-- ============================================================================
-- adai_creatives: Creative assets (images, videos, copy variants)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_creatives (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id  uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  name          text NOT NULL,
  type          text NOT NULL CHECK (type IN ('image', 'video', 'carousel', 'collection')),
  asset_urls    jsonb DEFAULT '[]'::jsonb,
  headline      text,
  body          text,
  cta           text,
  variant_of    uuid REFERENCES public.adai_creatives(id),
  status        text DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'archived')),
  performance_score numeric(5,2),
  metadata      jsonb DEFAULT '{}'::jsonb,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_creatives IS 'Creative assets for ad campaigns';
COMMENT ON COLUMN public.adai_creatives.variant_of IS 'Parent creative if this is an A/B test variant';

CREATE INDEX IF NOT EXISTS idx_adai_creatives_workspace ON public.adai_creatives(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_creatives_type ON public.adai_creatives(type);
CREATE INDEX IF NOT EXISTS idx_adai_creatives_variant ON public.adai_creatives(variant_of);

-- ============================================================================
-- adai_campaigns: Mirror of platform campaigns (synced from Meta/Google/TikTok)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_campaigns (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id         uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  connection_id        uuid NOT NULL REFERENCES public.adai_platform_connections(id) ON DELETE CASCADE,
  platform_campaign_id text NOT NULL,
  name                 text NOT NULL,
  status               text NOT NULL DEFAULT 'PAUSED',
  objective            text,
  daily_budget         numeric(12,2),
  lifetime_budget      numeric(12,2),
  spend_today          numeric(12,2) DEFAULT 0,
  spend_lifetime       numeric(12,2) DEFAULT 0,
  last_sync_at         timestamptz,
  raw_payload          jsonb,
  metadata             jsonb DEFAULT '{}'::jsonb,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id, connection_id, platform_campaign_id)
);

COMMENT ON TABLE public.adai_campaigns IS 'Local mirror of ad platform campaigns';

CREATE INDEX IF NOT EXISTS idx_adai_campaigns_workspace ON public.adai_campaigns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_campaigns_connection ON public.adai_campaigns(connection_id);
CREATE INDEX IF NOT EXISTS idx_adai_campaigns_status ON public.adai_campaigns(status);

-- ============================================================================
-- adai_adsets: Mirror of platform ad sets
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_adsets (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id       uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  campaign_id        uuid NOT NULL REFERENCES public.adai_campaigns(id) ON DELETE CASCADE,
  platform_adset_id  text NOT NULL,
  name               text NOT NULL,
  status             text NOT NULL DEFAULT 'PAUSED',
  targeting          jsonb DEFAULT '{}'::jsonb,
  budget             numeric(12,2),
  bid_strategy       text,
  bid_amount         numeric(12,2),
  last_sync_at       timestamptz,
  raw_payload        jsonb,
  metadata           jsonb DEFAULT '{}'::jsonb,
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id, campaign_id, platform_adset_id)
);

COMMENT ON TABLE public.adai_adsets IS 'Local mirror of ad platform ad sets';

CREATE INDEX IF NOT EXISTS idx_adai_adsets_workspace ON public.adai_adsets(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_adsets_campaign ON public.adai_adsets(campaign_id);

-- ============================================================================
-- adai_ads: Mirror of platform ads
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_ads (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  adset_id        uuid NOT NULL REFERENCES public.adai_adsets(id) ON DELETE CASCADE,
  platform_ad_id  text NOT NULL,
  name            text NOT NULL,
  status          text NOT NULL DEFAULT 'PAUSED',
  creative_id     uuid REFERENCES public.adai_creatives(id),
  last_sync_at    timestamptz,
  raw_payload     jsonb,
  metadata        jsonb DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id, adset_id, platform_ad_id)
);

COMMENT ON TABLE public.adai_ads IS 'Local mirror of ad platform ads';

CREATE INDEX IF NOT EXISTS idx_adai_ads_workspace ON public.adai_ads(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_ads_adset ON public.adai_ads(adset_id);
CREATE INDEX IF NOT EXISTS idx_adai_ads_creative ON public.adai_ads(creative_id);

-- ============================================================================
-- adai_metrics_daily: Daily performance metrics (normalized across platforms)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_metrics_daily (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id        uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  date                date NOT NULL,
  entity_type         text NOT NULL CHECK (entity_type IN ('campaign', 'adset', 'ad')),
  entity_id           uuid NOT NULL,
  platform_entity_id  text,
  impressions         bigint DEFAULT 0,
  clicks              bigint DEFAULT 0,
  spend               numeric(12,2) DEFAULT 0,
  conversions         integer DEFAULT 0,
  conversion_value    numeric(12,2) DEFAULT 0,
  ctr                 numeric(8,4),
  cpc                 numeric(12,4),
  cpa                 numeric(12,2),
  roas                numeric(8,2),
  frequency           numeric(6,2),
  reach               bigint DEFAULT 0,
  video_views         bigint DEFAULT 0,
  metadata            jsonb DEFAULT '{}'::jsonb,
  created_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id, date, entity_type, entity_id)
);

COMMENT ON TABLE public.adai_metrics_daily IS 'Daily ad performance metrics normalized across all platforms';

CREATE INDEX IF NOT EXISTS idx_adai_metrics_daily_workspace_date ON public.adai_metrics_daily(workspace_id, date);
CREATE INDEX IF NOT EXISTS idx_adai_metrics_daily_entity ON public.adai_metrics_daily(entity_type, entity_id);

-- ============================================================================
-- adai_experiments: A/B test definitions
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_experiments (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  name            text NOT NULL,
  hypothesis      text,
  variable        text NOT NULL CHECK (variable IN ('creative', 'copy', 'audience', 'bid', 'placement')),
  status          text DEFAULT 'draft' CHECK (status IN ('draft', 'running', 'paused', 'completed', 'cancelled')),
  started_at      timestamptz,
  ended_at        timestamptz,
  winner_arm_id   uuid,
  confidence      numeric(5,2),
  metadata        jsonb DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_experiments IS 'A/B test experiment definitions';

CREATE INDEX IF NOT EXISTS idx_adai_experiments_workspace ON public.adai_experiments(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_experiments_status ON public.adai_experiments(status);

-- ============================================================================
-- adai_experiment_arms: Test variants within experiments
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_experiment_arms (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id uuid NOT NULL REFERENCES public.adai_experiments(id) ON DELETE CASCADE,
  name          text NOT NULL,
  config        jsonb NOT NULL DEFAULT '{}'::jsonb,
  ad_ids        uuid[] DEFAULT '{}',
  is_control    boolean DEFAULT false,
  impressions   bigint DEFAULT 0,
  conversions   integer DEFAULT 0,
  spend         numeric(12,2) DEFAULT 0,
  cpa           numeric(12,2),
  metadata      jsonb DEFAULT '{}'::jsonb,
  created_at    timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_experiment_arms IS 'Individual test variants within A/B experiments';

CREATE INDEX IF NOT EXISTS idx_adai_experiment_arms_experiment ON public.adai_experiment_arms(experiment_id);

-- Update winner_arm_id foreign key
ALTER TABLE public.adai_experiments
  ADD CONSTRAINT fk_adai_experiments_winner_arm
  FOREIGN KEY (winner_arm_id) REFERENCES public.adai_experiment_arms(id);

-- ============================================================================
-- adai_decisions: Every optimizer decision (audit trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_decisions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  run_id          uuid,
  entity_type     text NOT NULL CHECK (entity_type IN ('campaign', 'adset', 'ad', 'creative')),
  entity_id       uuid NOT NULL,
  decision_type   text NOT NULL CHECK (decision_type IN ('scale', 'pause', 'resume', 'rotate', 'create', 'update', 'delete')),
  rule_id         text,
  inputs          jsonb NOT NULL DEFAULT '{}'::jsonb,
  outputs         jsonb NOT NULL DEFAULT '{}'::jsonb,
  impact_estimate numeric(12,2),
  status          text DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'rejected', 'executed', 'failed', 'rolled_back')),
  executed_at     timestamptz,
  correlation_id  uuid,
  metadata        jsonb DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_decisions IS 'Immutable log of all optimizer decisions';
COMMENT ON COLUMN public.adai_decisions.rule_id IS 'Which rule triggered this decision (for debugging)';
COMMENT ON COLUMN public.adai_decisions.correlation_id IS 'Links to jarvis_events for cross-system tracing';

CREATE INDEX IF NOT EXISTS idx_adai_decisions_workspace ON public.adai_decisions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_decisions_status ON public.adai_decisions(status);
CREATE INDEX IF NOT EXISTS idx_adai_decisions_created ON public.adai_decisions(created_at);
CREATE INDEX IF NOT EXISTS idx_adai_decisions_entity ON public.adai_decisions(entity_type, entity_id);

-- ============================================================================
-- adai_approval_queue: Pending approvals for high-impact changes
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_approval_queue (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id  uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  decision_id   uuid NOT NULL REFERENCES public.adai_decisions(id) ON DELETE CASCADE,
  change_set    jsonb NOT NULL DEFAULT '{}'::jsonb,
  reason        text,
  requested_by  text NOT NULL DEFAULT 'adai',
  approved_by   uuid REFERENCES auth.users(id),
  status        text DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
  expires_at    timestamptz DEFAULT (now() + interval '7 days'),
  resolved_at   timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_approval_queue IS 'Queue for ad changes requiring manual approval';

CREATE INDEX IF NOT EXISTS idx_adai_approval_queue_workspace ON public.adai_approval_queue(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_approval_queue_status ON public.adai_approval_queue(status);
CREATE INDEX IF NOT EXISTS idx_adai_approval_queue_expires ON public.adai_approval_queue(expires_at) WHERE status = 'pending';

-- ============================================================================
-- adai_audit_log: Immutable audit trail (append-only)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_audit_log (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  decision_id     uuid REFERENCES public.adai_decisions(id),
  action          text NOT NULL,
  entity_type     text,
  entity_id       uuid,
  platform_entity_id text,
  before_state    jsonb,
  after_state     jsonb,
  performed_by    text NOT NULL DEFAULT 'system',
  correlation_id  uuid,
  created_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_audit_log IS 'Immutable audit log for all AdAI actions';
COMMENT ON COLUMN public.adai_audit_log.performed_by IS 'system, adai, or user:{uuid}';

CREATE INDEX IF NOT EXISTS idx_adai_audit_log_workspace ON public.adai_audit_log(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_audit_log_created ON public.adai_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_adai_audit_log_entity ON public.adai_audit_log(entity_type, entity_id);

-- ============================================================================
-- adai_rollback_snapshots: State snapshots for rollback capability
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_rollback_snapshots (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id        uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  decision_id         uuid NOT NULL REFERENCES public.adai_decisions(id) ON DELETE CASCADE,
  entity_type         text NOT NULL,
  entity_id           uuid NOT NULL,
  platform_entity_id  text,
  snapshot            jsonb NOT NULL,
  is_rolled_back      boolean DEFAULT false,
  rolled_back_at      timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_rollback_snapshots IS 'Pre-change snapshots enabling rollback';

CREATE INDEX IF NOT EXISTS idx_adai_rollback_workspace ON public.adai_rollback_snapshots(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_rollback_decision ON public.adai_rollback_snapshots(decision_id);

-- ============================================================================
-- adai_runs: Optimization cycle run tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.adai_runs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  run_type        text NOT NULL CHECK (run_type IN ('daily', 'hourly', 'manual', 'triggered')),
  status          text DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  started_at      timestamptz NOT NULL DEFAULT now(),
  completed_at    timestamptz,
  metrics_synced  integer DEFAULT 0,
  decisions_made  integer DEFAULT 0,
  decisions_executed integer DEFAULT 0,
  error_message   text,
  summary         jsonb DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.adai_runs IS 'Tracks optimization cycle runs';

CREATE INDEX IF NOT EXISTS idx_adai_runs_workspace ON public.adai_runs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adai_runs_status ON public.adai_runs(status);
CREATE INDEX IF NOT EXISTS idx_adai_runs_started ON public.adai_runs(started_at);

-- ============================================================================
-- Enable Row Level Security on all AdAI tables
-- ============================================================================

ALTER TABLE public.adai_platform_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_launch_specs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_creatives ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_adsets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_ads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_metrics_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_experiment_arms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_approval_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_rollback_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adai_runs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies: Workspace member access
-- ============================================================================

-- Helper function to check workspace membership
CREATE OR REPLACE FUNCTION public.is_workspace_member(ws_id uuid)
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.jarvis_workspace_members
    WHERE workspace_id = ws_id AND user_id = auth.uid()
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create policies for each table
DO $$
DECLARE
  tbl text;
  tables text[] := ARRAY[
    'adai_platform_connections',
    'adai_policies',
    'adai_launch_specs',
    'adai_creatives',
    'adai_campaigns',
    'adai_adsets',
    'adai_ads',
    'adai_metrics_daily',
    'adai_experiments',
    'adai_decisions',
    'adai_approval_queue',
    'adai_audit_log',
    'adai_rollback_snapshots',
    'adai_runs'
  ];
BEGIN
  FOREACH tbl IN ARRAY tables
  LOOP
    -- SELECT policy for workspace members
    EXECUTE format(
      'CREATE POLICY "%s_workspace_select" ON public.%I FOR SELECT USING (public.is_workspace_member(workspace_id))',
      tbl, tbl
    );

    -- INSERT/UPDATE/DELETE for workspace members (except audit_log which is append-only)
    IF tbl != 'adai_audit_log' THEN
      EXECUTE format(
        'CREATE POLICY "%s_workspace_modify" ON public.%I FOR ALL USING (public.is_workspace_member(workspace_id)) WITH CHECK (public.is_workspace_member(workspace_id))',
        tbl, tbl
      );
    ELSE
      -- Audit log: only INSERT allowed
      EXECUTE format(
        'CREATE POLICY "%s_workspace_insert" ON public.%I FOR INSERT WITH CHECK (public.is_workspace_member(workspace_id))',
        tbl, tbl
      );
    END IF;
  END LOOP;
END $$;

-- Experiment arms: access through experiment workspace
CREATE POLICY "adai_experiment_arms_workspace_select" ON public.adai_experiment_arms
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.adai_experiments e
      WHERE e.id = experiment_id AND public.is_workspace_member(e.workspace_id)
    )
  );

CREATE POLICY "adai_experiment_arms_workspace_modify" ON public.adai_experiment_arms
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.adai_experiments e
      WHERE e.id = experiment_id AND public.is_workspace_member(e.workspace_id)
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.adai_experiments e
      WHERE e.id = experiment_id AND public.is_workspace_member(e.workspace_id)
    )
  );

-- ============================================================================
-- Triggers for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION public.adai_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
  tbl text;
  tables text[] := ARRAY[
    'adai_platform_connections',
    'adai_policies',
    'adai_launch_specs',
    'adai_creatives',
    'adai_campaigns',
    'adai_adsets',
    'adai_ads',
    'adai_experiments',
    'adai_approval_queue'
  ];
BEGIN
  FOREACH tbl IN ARRAY tables
  LOOP
    EXECUTE format(
      'CREATE TRIGGER %s_updated_at BEFORE UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.adai_set_updated_at()',
      tbl, tbl
    );
  END LOOP;
END $$;

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON SCHEMA public IS 'JarvisCore schema including AdAI advertising automation tables';
