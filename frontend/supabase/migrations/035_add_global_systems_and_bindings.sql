-- Migration 035: Global Systems and Bindings
-- Creates tables for global systems (Jarvis, Nexus, Ghexit Telecom) and their workspace bindings and event consumers

-- ============================================================================
-- jarvis_global_systems: Registry of global systems
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jarvis_global_systems (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  slug        text NOT NULL UNIQUE,
  name        text NOT NULL,
  system_type text NOT NULL,
  description text,
  metadata    jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.jarvis_global_systems IS 'Registry of global systems (Jarvis, Nexus, Ghexit Telecom) that operate across workspaces within a tenant.';
COMMENT ON COLUMN public.jarvis_global_systems.tenant_id IS 'The tenant that owns this global system.';
COMMENT ON COLUMN public.jarvis_global_systems.slug IS 'Unique identifier slug for the system (e.g., "jarvis", "nexus", "ghexit_telecom").';
COMMENT ON COLUMN public.jarvis_global_systems.name IS 'Human-readable name of the system.';
COMMENT ON COLUMN public.jarvis_global_systems.system_type IS 'Type of system (e.g., "ai_ceo", "bizops_os", "telecom_infra").';
COMMENT ON COLUMN public.jarvis_global_systems.description IS 'Optional description of the system and its purpose.';
COMMENT ON COLUMN public.jarvis_global_systems.metadata IS 'Additional metadata about the system in JSON format.';

CREATE INDEX IF NOT EXISTS idx_jarvis_global_systems_tenant ON public.jarvis_global_systems(tenant_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_global_systems_slug ON public.jarvis_global_systems(slug);

-- ============================================================================
-- jarvis_system_workspace_bindings: Links global systems to workspaces
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jarvis_system_workspace_bindings (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id   uuid NOT NULL REFERENCES public.jarvis_global_systems(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  access_level text NOT NULL,
  metadata    jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE(system_id, workspace_id)
);

COMMENT ON TABLE public.jarvis_system_workspace_bindings IS 'Links global systems to workspaces, defining which systems have access to which workspaces and at what level.';
COMMENT ON COLUMN public.jarvis_system_workspace_bindings.system_id IS 'Reference to the global system.';
COMMENT ON COLUMN public.jarvis_system_workspace_bindings.workspace_id IS 'Reference to the workspace this system can access.';
COMMENT ON COLUMN public.jarvis_system_workspace_bindings.access_level IS 'Access level granted to the system (e.g., "read", "write", "admin").';
COMMENT ON COLUMN public.jarvis_system_workspace_bindings.metadata IS 'Additional metadata about the binding in JSON format.';

CREATE INDEX IF NOT EXISTS idx_jarvis_system_workspace_bindings_system ON public.jarvis_system_workspace_bindings(system_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_system_workspace_bindings_workspace ON public.jarvis_system_workspace_bindings(workspace_id);

-- ============================================================================
-- jarvis_event_consumers: Event consumers for global systems
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jarvis_event_consumers (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id     uuid NOT NULL REFERENCES public.jarvis_global_systems(id) ON DELETE CASCADE,
  event_type    text NOT NULL,
  handler_type  text NOT NULL,
  handler_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  is_active     boolean NOT NULL DEFAULT true,
  metadata      jsonb,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.jarvis_event_consumers IS 'Defines which events each global system consumes and how they are handled.';
COMMENT ON COLUMN public.jarvis_event_consumers.system_id IS 'Reference to the global system that consumes these events.';
COMMENT ON COLUMN public.jarvis_event_consumers.event_type IS 'Event type pattern (e.g., "company.created", "module.*", "*" for all events).';
COMMENT ON COLUMN public.jarvis_event_consumers.handler_type IS 'Type of handler (e.g., "internal", "webhook", "queue").';
COMMENT ON COLUMN public.jarvis_event_consumers.handler_config IS 'Configuration for the handler in JSON format (e.g., {"route": "jarvis"}).';
COMMENT ON COLUMN public.jarvis_event_consumers.is_active IS 'Whether this event consumer is currently active.';
COMMENT ON COLUMN public.jarvis_event_consumers.metadata IS 'Additional metadata about the consumer in JSON format.';

CREATE INDEX IF NOT EXISTS idx_jarvis_event_consumers_system_event ON public.jarvis_event_consumers(system_id, event_type);
CREATE INDEX IF NOT EXISTS idx_jarvis_event_consumers_system ON public.jarvis_event_consumers(system_id);
CREATE INDEX IF NOT EXISTS idx_jarvis_event_consumers_active ON public.jarvis_event_consumers(is_active) WHERE is_active = true;

-- ============================================================================
-- Enable Row Level Security
-- ============================================================================

ALTER TABLE public.jarvis_global_systems ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_system_workspace_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_event_consumers ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies for jarvis_global_systems
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_global_systems'
      AND policyname = 'jarvis_global_systems_tenant_members'
  ) THEN
    CREATE POLICY "jarvis_global_systems_tenant_members" ON public.jarvis_global_systems
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          tenant_id IN (
            SELECT w.tenant_id FROM public.workspaces w
            JOIN public.jarvis_workspace_members m ON m.workspace_id = w.id
            WHERE m.user_id = auth.uid()
          )
        )
      );
  END IF;
END $$;

-- ============================================================================
-- RLS Policies for jarvis_system_workspace_bindings
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_system_workspace_bindings'
      AND policyname = 'jarvis_system_workspace_bindings_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_system_workspace_bindings_workspace_members" ON public.jarvis_system_workspace_bindings
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          workspace_id IN (
            SELECT workspace_id FROM public.jarvis_workspace_members
            WHERE user_id = auth.uid()
          )
          OR workspace_id IN (
            SELECT id FROM public.workspaces WHERE owner_id = auth.uid()
          )
        )
      );
  END IF;
END $$;

-- ============================================================================
-- RLS Policies for jarvis_event_consumers
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_event_consumers'
      AND policyname = 'jarvis_event_consumers_tenant_members'
  ) THEN
    CREATE POLICY "jarvis_event_consumers_tenant_members" ON public.jarvis_event_consumers
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          system_id IN (
            SELECT gs.id FROM public.jarvis_global_systems gs
            WHERE gs.tenant_id IN (
              SELECT w.tenant_id FROM public.workspaces w
              JOIN public.jarvis_workspace_members m ON m.workspace_id = w.id
              WHERE m.user_id = auth.uid()
            )
          )
        )
      );
  END IF;
END $$;

