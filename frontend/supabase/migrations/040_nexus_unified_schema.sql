-- ============================================================
-- NEXUS UNIFIED SCHEMA MIGRATION
-- ============================================================
-- This migration consolidates Nexus tables with consistent naming.
-- Run AFTER all previous migrations.
--
-- NAMING CONVENTION: Simple names (entities, fact_finance, etc.)
-- This allows Nexus to work standalone or integrated with JarvisCore.
--
-- NOTE: Uses safe patterns that handle existing tables gracefully.
-- ============================================================

-- ============================================================
-- 1. ENTITY MANAGEMENT
-- ============================================================

-- Create entities table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text NOT NULL,
  name text NOT NULL,
  entity_type text NOT NULL DEFAULT 'subsidiary',
  industry text,
  sub_industry text,
  region text DEFAULT 'US-Pacific',
  country text DEFAULT 'US',
  currency text DEFAULT 'USD',
  status text DEFAULT 'active',
  lifecycle_stage text DEFAULT 'growth',
  parent_entity_id uuid,
  ownership_pct numeric(5,2) DEFAULT 100.00,
  founded_date date,
  acquired_date date,
  hipaa_covered boolean DEFAULT false,
  monthly_revenue numeric(18,2) DEFAULT 0,
  monthly_expenses numeric(18,2) DEFAULT 0,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Add workspace_id if missing
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'entities' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.entities ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- Add unique constraint on code if missing
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'entities_code_key') THEN
    ALTER TABLE public.entities ADD CONSTRAINT entities_code_key UNIQUE (code);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

-- Add self-reference FK if missing
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'entities_parent_entity_id_fkey') THEN
    ALTER TABLE public.entities
      ADD CONSTRAINT entities_parent_entity_id_fkey
      FOREIGN KEY (parent_entity_id) REFERENCES public.entities(id);
  END IF;
EXCEPTION WHEN duplicate_object THEN
  NULL;
END $$;

-- Create departments table
CREATE TABLE IF NOT EXISTS public.departments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text NOT NULL,
  name text NOT NULL,
  category text NOT NULL,
  sort_order int DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'departments' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.departments ADD COLUMN workspace_id uuid;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'departments_code_key') THEN
    ALTER TABLE public.departments ADD CONSTRAINT departments_code_key UNIQUE (code);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

-- Seed departments if empty
INSERT INTO public.departments (code, name, category, sort_order)
SELECT * FROM (VALUES
  ('FINANCE', 'Finance', 'core', 1),
  ('HR', 'Human Resources', 'support', 2),
  ('MARKETING', 'Marketing', 'core', 3),
  ('OPS', 'Operations', 'core', 4),
  ('LEGAL', 'Legal & Compliance', 'support', 5),
  ('STRATEGY', 'Strategy', 'strategic', 6),
  ('TECH', 'Technology', 'support', 7),
  ('SALES', 'Sales', 'core', 8)
) AS v(code, name, category, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM public.departments LIMIT 1)
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- 2. FINANCIAL FACT TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS public.fact_finance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL,
  period_date date NOT NULL,
  revenue numeric(18,2) DEFAULT 0,
  cogs numeric(18,2) DEFAULT 0,
  opex numeric(18,2) DEFAULT 0,
  depreciation numeric(18,2) DEFAULT 0,
  interest numeric(18,2) DEFAULT 0,
  taxes numeric(18,2) DEFAULT 0,
  net_income numeric(18,2),
  cash_balance numeric(18,2),
  accounts_receivable numeric(18,2),
  accounts_payable numeric(18,2),
  inventory numeric(18,2),
  total_assets numeric(18,2),
  total_liabilities numeric(18,2),
  operating_cash_flow numeric(18,2),
  investing_cash_flow numeric(18,2),
  financing_cash_flow numeric(18,2),
  capex numeric(18,2),
  data_source text DEFAULT 'manual',
  confidence_score numeric(3,2) DEFAULT 1.0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'fact_finance' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.fact_finance ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- Add FK if missing
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fact_finance_entity_id_fkey') THEN
    ALTER TABLE public.fact_finance
      ADD CONSTRAINT fact_finance_entity_id_fkey
      FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;
  END IF;
EXCEPTION WHEN duplicate_object THEN
  NULL;
END $$;

-- Add unique constraint if missing
DO $$
BEGIN
  ALTER TABLE public.fact_finance ADD CONSTRAINT fact_finance_entity_period_unique UNIQUE (entity_id, period_date);
EXCEPTION WHEN duplicate_table THEN
  NULL;
WHEN duplicate_object THEN
  NULL;
END $$;

-- fact_hr
CREATE TABLE IF NOT EXISTS public.fact_hr (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL,
  period_date date NOT NULL,
  headcount_start int DEFAULT 0,
  hires int DEFAULT 0,
  terminations int DEFAULT 0,
  voluntary_terms int DEFAULT 0,
  involuntary_terms int DEFAULT 0,
  turnover_rate numeric(5,2),
  retention_rate numeric(5,2),
  total_payroll numeric(18,2),
  avg_salary numeric(18,2),
  benefits_cost numeric(18,2),
  engagement_score numeric(5,2),
  sick_days int,
  overtime_hours numeric(10,2),
  training_hours numeric(10,2),
  open_positions int DEFAULT 0,
  avg_time_to_hire int,
  data_source text DEFAULT 'manual',
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'fact_hr' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.fact_hr ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- fact_marketing
CREATE TABLE IF NOT EXISTS public.fact_marketing (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL,
  period_date date NOT NULL,
  total_ad_spend numeric(18,2) DEFAULT 0,
  google_ads_spend numeric(18,2) DEFAULT 0,
  meta_ads_spend numeric(18,2) DEFAULT 0,
  other_ads_spend numeric(18,2) DEFAULT 0,
  content_spend numeric(18,2) DEFAULT 0,
  impressions bigint,
  clicks bigint,
  leads int,
  customers_acquired int,
  cac numeric(18,2),
  cpl numeric(18,2),
  ctr numeric(5,2),
  conversion_rate numeric(5,2),
  revenue_attributed numeric(18,2),
  roas numeric(5,2),
  website_sessions int,
  unique_visitors int,
  bounce_rate numeric(5,2),
  avg_session_duration int,
  email_subscribers int,
  email_open_rate numeric(5,2),
  email_click_rate numeric(5,2),
  data_source text DEFAULT 'manual',
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'fact_marketing' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.fact_marketing ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- fact_operations
CREATE TABLE IF NOT EXISTS public.fact_operations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL,
  period_date date NOT NULL,
  total_orders int,
  orders_fulfilled int,
  orders_cancelled int,
  sla_breaches int DEFAULT 0,
  error_rate numeric(5,2),
  defect_rate numeric(5,2),
  customer_complaints int,
  avg_fulfillment_time numeric(10,2),
  avg_resolution_time numeric(10,2),
  capacity_utilization numeric(5,2),
  patient_visits int,
  no_show_rate numeric(5,2),
  avg_wait_time int,
  uptime_pct numeric(5,2),
  api_calls bigint,
  active_users int,
  churn_rate numeric(5,2),
  data_source text DEFAULT 'manual',
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'fact_operations' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.fact_operations ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- fact_legal
CREATE TABLE IF NOT EXISTS public.fact_legal (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL,
  period_date date NOT NULL,
  open_cases int DEFAULT 0,
  closed_cases int DEFAULT 0,
  new_cases int DEFAULT 0,
  contracts_pending int DEFAULT 0,
  contracts_signed int DEFAULT 0,
  contracts_expiring_30d int DEFAULT 0,
  contracts_expiring_90d int DEFAULT 0,
  compliance_score numeric(5,2),
  audit_findings int DEFAULT 0,
  regulatory_filings_due int DEFAULT 0,
  regulatory_filings_completed int DEFAULT 0,
  licenses_expiring_30d int DEFAULT 0,
  licenses_expiring_90d int DEFAULT 0,
  hipaa_incidents int DEFAULT 0,
  data_breaches int DEFAULT 0,
  legal_fees numeric(18,2),
  settlement_costs numeric(18,2),
  data_source text DEFAULT 'manual',
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'fact_legal' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.fact_legal ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 3. INTELLIGENCE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS public.entity_risk_scores (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL,
  period_date date,
  calculated_at timestamptz DEFAULT now(),
  finance_risk smallint CHECK (finance_risk BETWEEN 0 AND 100),
  hr_risk smallint CHECK (hr_risk BETWEEN 0 AND 100),
  marketing_risk smallint CHECK (marketing_risk BETWEEN 0 AND 100),
  ops_risk smallint CHECK (ops_risk BETWEEN 0 AND 100),
  legal_risk smallint CHECK (legal_risk BETWEEN 0 AND 100),
  overall_risk smallint CHECK (overall_risk BETWEEN 0 AND 100),
  health_score smallint CHECK (health_score BETWEEN 0 AND 100),
  risk_factors jsonb DEFAULT '{}',
  risk_notes text,
  calculated_by text DEFAULT 'llm',
  model_version text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'entity_risk_scores' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.entity_risk_scores ADD COLUMN workspace_id uuid;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.entity_swot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL,
  period_date date,
  generated_at timestamptz DEFAULT now(),
  strengths jsonb NOT NULL DEFAULT '[]',
  weaknesses jsonb NOT NULL DEFAULT '[]',
  opportunities jsonb NOT NULL DEFAULT '[]',
  threats jsonb NOT NULL DEFAULT '[]',
  executive_summary text,
  key_recommendation text,
  generated_by text DEFAULT 'llm',
  model_version text,
  confidence_score numeric(3,2),
  human_reviewed boolean DEFAULT false,
  reviewed_by uuid,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'entity_swot' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.entity_swot ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 4. DECISION AND WORKFLOW
-- ============================================================

CREATE TABLE IF NOT EXISTS public.decision_queue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  department_id uuid,
  title text NOT NULL,
  description text,
  decision_type text NOT NULL,
  priority text DEFAULT 'medium',
  recommended_action text,
  expected_impact text,
  risk_if_delayed text,
  related_metrics jsonb,
  supporting_docs text[],
  status text DEFAULT 'pending',
  assigned_to uuid,
  due_date date,
  decision_made text,
  decision_date timestamptz,
  expected_outcome text,
  expected_outcome_metric text,
  expected_outcome_value numeric,
  outcome_check_date date,
  created_by text DEFAULT 'llm',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'decision_queue' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.decision_queue ADD COLUMN workspace_id uuid;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.decision_outcomes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id uuid NOT NULL,
  actual_outcome_value numeric,
  outcome_delta numeric,
  outcome_met boolean,
  llm_analysis text,
  contributing_factors jsonb,
  reward_signal numeric(3,2),
  measured_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'decision_outcomes' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.decision_outcomes ADD COLUMN workspace_id uuid;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.decision_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id uuid,
  action text NOT NULL,
  actor text,
  notes text,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'decision_log' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.decision_log ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 5. ALERTS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  title text NOT NULL,
  message text NOT NULL,
  severity text NOT NULL,
  category text,
  triggered_by text,
  trigger_metric text,
  trigger_value numeric,
  threshold_value numeric,
  status text DEFAULT 'active',
  acknowledged_at timestamptz,
  acknowledged_by uuid,
  resolved_at timestamptz,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'alerts' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.alerts ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 6. AGENT MANAGEMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS public.agent_states (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id text NOT NULL,
  agent_name text NOT NULL,
  category text,
  status text DEFAULT 'idle',
  last_run_at timestamptz,
  next_run_at timestamptz,
  run_count int DEFAULT 0,
  error_count int DEFAULT 0,
  last_error text,
  config jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'agent_states' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.agent_states ADD COLUMN workspace_id uuid;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'agent_states_agent_id_key') THEN
    ALTER TABLE public.agent_states ADD CONSTRAINT agent_states_agent_id_key UNIQUE (agent_id);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.agent_executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id text NOT NULL,
  status text DEFAULT 'queued',
  started_at timestamptz,
  completed_at timestamptz,
  duration_ms int,
  result jsonb,
  error text,
  alerts_created int DEFAULT 0,
  decisions_created int DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'agent_executions' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.agent_executions ADD COLUMN workspace_id uuid;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.agent_configs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id text NOT NULL,
  enabled boolean DEFAULT true,
  schedule text,
  thresholds jsonb DEFAULT '{}',
  monitored_metrics text[],
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'agent_configs' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.agent_configs ADD COLUMN workspace_id uuid;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'agent_configs_agent_id_key') THEN
    ALTER TABLE public.agent_configs ADD CONSTRAINT agent_configs_agent_id_key UNIQUE (agent_id);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.agent_autonomy (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id text NOT NULL,
  domain text NOT NULL,
  autonomy_level int DEFAULT 0 CHECK (autonomy_level BETWEEN 0 AND 3),
  approval_count int DEFAULT 0,
  rejection_count int DEFAULT 0,
  last_updated timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'agent_autonomy' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.agent_autonomy ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 7. PLAYBOOKS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.playbooks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text NOT NULL,
  name text NOT NULL,
  description text,
  category text,
  trigger_conditions jsonb DEFAULT '{}',
  steps jsonb DEFAULT '[]',
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'playbooks' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.playbooks ADD COLUMN workspace_id uuid;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'playbooks_code_key') THEN
    ALTER TABLE public.playbooks ADD CONSTRAINT playbooks_code_key UNIQUE (code);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.playbook_executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  playbook_id uuid,
  entity_id uuid,
  status text DEFAULT 'in_progress',
  current_step int DEFAULT 0,
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz,
  result jsonb,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'playbook_executions' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.playbook_executions ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 8. CONTENT MANAGEMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS public.content_queue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  title text NOT NULL,
  content_type text NOT NULL,
  content text,
  platform text,
  scheduled_for timestamptz,
  status text DEFAULT 'draft',
  approved_by uuid,
  approved_at timestamptz,
  published_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'content_queue' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.content_queue ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 9. RENEWALS AND LICENSES
-- ============================================================

CREATE TABLE IF NOT EXISTS public.renewals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  item_type text NOT NULL,
  item_name text NOT NULL,
  vendor text,
  expiry_date date NOT NULL,
  renewal_cost numeric(18,2),
  auto_renew boolean DEFAULT false,
  status text DEFAULT 'active',
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'renewals' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.renewals ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 10. PROJECTS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  name text NOT NULL,
  description text,
  status text DEFAULT 'active',
  priority text DEFAULT 'medium',
  start_date date,
  target_date date,
  completed_date date,
  owner_id uuid,
  budget numeric(18,2),
  actual_spend numeric(18,2),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'projects' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.projects ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 11. PLAID/BANK INTEGRATION
-- ============================================================

CREATE TABLE IF NOT EXISTS public.plaid_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  item_id text NOT NULL,
  access_token text NOT NULL,
  institution_id text,
  institution_name text,
  status text DEFAULT 'active',
  error_code text,
  error_message text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'plaid_items' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.plaid_items ADD COLUMN workspace_id uuid;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'plaid_items_item_id_key') THEN
    ALTER TABLE public.plaid_items ADD CONSTRAINT plaid_items_item_id_key UNIQUE (item_id);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.plaid_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plaid_item_id uuid,
  account_id text NOT NULL,
  name text,
  official_name text,
  type text,
  subtype text,
  mask text,
  current_balance numeric(18,2),
  available_balance numeric(18,2),
  iso_currency_code text DEFAULT 'USD',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'plaid_accounts' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.plaid_accounts ADD COLUMN workspace_id uuid;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'plaid_accounts_account_id_key') THEN
    ALTER TABLE public.plaid_accounts ADD CONSTRAINT plaid_accounts_account_id_key UNIQUE (account_id);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.plaid_transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plaid_account_id uuid,
  transaction_id text NOT NULL,
  amount numeric(18,2) NOT NULL,
  date date NOT NULL,
  name text,
  merchant_name text,
  category text[],
  pending boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'plaid_transactions' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.plaid_transactions ADD COLUMN workspace_id uuid;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'plaid_transactions_transaction_id_key') THEN
    ALTER TABLE public.plaid_transactions ADD CONSTRAINT plaid_transactions_transaction_id_key UNIQUE (transaction_id);
  END IF;
EXCEPTION WHEN duplicate_table THEN
  NULL;
END $$;

-- ============================================================
-- 12. OAUTH TOKENS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.oauth_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  provider text NOT NULL,
  access_token text NOT NULL,
  refresh_token text,
  token_type text DEFAULT 'Bearer',
  expires_at timestamptz,
  scope text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'oauth_tokens' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.oauth_tokens ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 13. BRIEFING SNAPSHOTS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.briefing_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  briefing_date date NOT NULL,
  content jsonb NOT NULL,
  summary text,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'briefing_snapshots' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.briefing_snapshots ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 14. SOCIAL/ANALYTICS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.social_posts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  platform text NOT NULL,
  post_id text,
  content text,
  media_urls text[],
  posted_at timestamptz,
  status text DEFAULT 'draft',
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'social_posts' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.social_posts ADD COLUMN workspace_id uuid;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.social_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id uuid,
  platform text NOT NULL,
  impressions int DEFAULT 0,
  engagements int DEFAULT 0,
  likes int DEFAULT 0,
  comments int DEFAULT 0,
  shares int DEFAULT 0,
  clicks int DEFAULT 0,
  measured_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'social_metrics' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.social_metrics ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- 15. EXTENDED METRICS (Publishing)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.fact_book_sales (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid,
  period_date date NOT NULL,
  asin text,
  isbn text,
  title text NOT NULL,
  format text,
  units_sold int DEFAULT 0,
  revenue numeric(18,2) DEFAULT 0,
  royalties numeric(18,2) DEFAULT 0,
  ku_pages_read int DEFAULT 0,
  avg_rating numeric(3,2),
  review_count int DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'fact_book_sales' AND column_name = 'workspace_id') THEN
    ALTER TABLE public.fact_book_sales ADD COLUMN workspace_id uuid;
  END IF;
END $$;

-- ============================================================
-- INDEXES (Safe creation)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_entities_code ON entities(code);
CREATE INDEX IF NOT EXISTS idx_entities_status ON entities(status);
CREATE INDEX IF NOT EXISTS idx_entities_workspace ON entities(workspace_id);

CREATE INDEX IF NOT EXISTS idx_fact_finance_entity_period ON fact_finance(entity_id, period_date);
CREATE INDEX IF NOT EXISTS idx_fact_finance_workspace ON fact_finance(workspace_id);

CREATE INDEX IF NOT EXISTS idx_fact_hr_entity_period ON fact_hr(entity_id, period_date);
CREATE INDEX IF NOT EXISTS idx_fact_marketing_entity_period ON fact_marketing(entity_id, period_date);
CREATE INDEX IF NOT EXISTS idx_fact_operations_entity_period ON fact_operations(entity_id, period_date);
CREATE INDEX IF NOT EXISTS idx_fact_legal_entity_period ON fact_legal(entity_id, period_date);

CREATE INDEX IF NOT EXISTS idx_risk_scores_entity ON entity_risk_scores(entity_id);
CREATE INDEX IF NOT EXISTS idx_swot_entity ON entity_swot(entity_id);

CREATE INDEX IF NOT EXISTS idx_alerts_entity_status ON alerts(entity_id, status);
CREATE INDEX IF NOT EXISTS idx_alerts_workspace ON alerts(workspace_id);

CREATE INDEX IF NOT EXISTS idx_decision_queue_status ON decision_queue(status, priority);
CREATE INDEX IF NOT EXISTS idx_decision_queue_workspace ON decision_queue(workspace_id);

CREATE INDEX IF NOT EXISTS idx_agent_states_agent_id ON agent_states(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON agent_executions(agent_id);

CREATE INDEX IF NOT EXISTS idx_plaid_items_entity ON plaid_items(entity_id);
CREATE INDEX IF NOT EXISTS idx_plaid_transactions_date ON plaid_transactions(date);

-- ============================================================
-- ROW LEVEL SECURITY (Safe enable)
-- ============================================================

DO $$
DECLARE
  tbl text;
BEGIN
  FOR tbl IN SELECT unnest(ARRAY[
    'entities', 'departments', 'fact_finance', 'fact_hr', 'fact_marketing',
    'fact_operations', 'fact_legal', 'entity_risk_scores', 'entity_swot',
    'decision_queue', 'decision_outcomes', 'decision_log', 'alerts',
    'agent_states', 'agent_executions', 'agent_configs', 'agent_autonomy',
    'playbooks', 'playbook_executions', 'content_queue', 'renewals',
    'projects', 'plaid_items', 'plaid_accounts', 'plaid_transactions',
    'oauth_tokens', 'briefing_snapshots', 'social_posts', 'social_metrics',
    'fact_book_sales'
  ])
  LOOP
    -- Enable RLS
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl);

    -- Create policy (drop first if exists to update)
    EXECUTE format('DROP POLICY IF EXISTS allow_authenticated ON public.%I', tbl);
    EXECUTE format('
      CREATE POLICY allow_authenticated ON public.%I
        FOR ALL USING (auth.uid() IS NOT NULL)
    ', tbl);
  END LOOP;
END$$;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
-- Tables created/updated with consistent simple naming convention.
-- Missing workspace_id columns have been added.
-- Nexus code should work without modification.
-- ============================================================
