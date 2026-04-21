-- Migration 038: Add Simulation Columns to jarvis_events
-- Adds tenant_id, company_id, module_id, source_system_slug, and is_simulation columns
-- to support event simulation and better entity linking

-- ============================================================================
-- Add new columns to existing jarvis_events table
-- ============================================================================

-- Add tenant_id column
ALTER TABLE public.jarvis_events
ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants(id) ON DELETE CASCADE;

-- Add company_id column (references jarvis_companies)
ALTER TABLE public.jarvis_events
ADD COLUMN IF NOT EXISTS company_id uuid REFERENCES public.jarvis_companies(id) ON DELETE SET NULL;

-- Add module_id column (references modules)
ALTER TABLE public.jarvis_events
ADD COLUMN IF NOT EXISTS module_id uuid REFERENCES public.modules(id) ON DELETE SET NULL;

-- Add source_system_slug column (more specific than source)
ALTER TABLE public.jarvis_events
ADD COLUMN IF NOT EXISTS source_system_slug text;

-- Add is_simulation column
ALTER TABLE public.jarvis_events
ADD COLUMN IF NOT EXISTS is_simulation boolean NOT NULL DEFAULT false;

-- ============================================================================
-- Add indexes for new columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_jarvis_events_tenant ON public.jarvis_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_events_company ON public.jarvis_events(company_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_events_module ON public.jarvis_events(module_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_events_source_system_slug ON public.jarvis_events(source_system_slug);
CREATE INDEX IF NOT EXISTS idx_jarvis_events_simulation ON public.jarvis_events(is_simulation);

-- Composite index for simulation queries
CREATE INDEX IF NOT EXISTS idx_jarvis_events_simulation_workspace ON public.jarvis_events(is_simulation, workspace_id) WHERE is_simulation = true;

-- ============================================================================
-- Add comments
-- ============================================================================

COMMENT ON COLUMN public.jarvis_events.tenant_id IS 'Reference to the tenant this event belongs to. Allows tenant-level event queries.';
COMMENT ON COLUMN public.jarvis_events.company_id IS 'Reference to the company/workspace unit this event relates to (if applicable).';
COMMENT ON COLUMN public.jarvis_events.module_id IS 'Reference to the module this event relates to (if applicable).';
COMMENT ON COLUMN public.jarvis_events.source_system_slug IS 'Identifies the originating system by slug (e.g. "simulation", "jarvis", "nexus", "ghexit_telecom"). More specific than the source column.';
COMMENT ON COLUMN public.jarvis_events.is_simulation IS 'True if this event is part of a simulation run, false for real events. Allows filtering simulation events from production data.';

-- Update table comment to mention simulation support
COMMENT ON TABLE public.jarvis_events IS 'Global Event Mesh v0: append-only log of all Jarvis/Nexus events with typed payloads. Supports both real and simulation events.';

-- ============================================================================
-- Backfill tenant_id for existing events (optional, safe to skip if no existing data)
-- ============================================================================

-- This will backfill tenant_id from workspace_id for existing events
-- Safe to run even if there are no existing events
UPDATE public.jarvis_events
SET tenant_id = w.tenant_id
FROM public.workspaces w
WHERE jarvis_events.workspace_id = w.id
  AND jarvis_events.tenant_id IS NULL;

-- ============================================================================
-- Note: RLS policies already exist from migration 025
-- The new columns will be automatically covered by existing policies
-- ============================================================================

