-- Migration 037: System Workspace Roles and Module Mappings
-- Creates tables for mapping global systems to workspaces/modules with roles and integration placeholders

-- ============================================================================
-- jarvis_system_workspace_roles: Maps systems to workspaces with specific roles
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jarvis_system_workspace_roles (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id   uuid NOT NULL REFERENCES public.jarvis_global_systems(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  system_role text NOT NULL,
  scope       text NOT NULL,
  metadata    jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE(system_id, workspace_id)
);

COMMENT ON TABLE public.jarvis_system_workspace_roles IS 'Maps global systems to workspaces with specific roles and scopes (e.g., Jarvis as "executive", Nexus as "ops_controller").';
COMMENT ON COLUMN public.jarvis_system_workspace_roles.system_id IS 'Reference to the global system.';
COMMENT ON COLUMN public.jarvis_system_workspace_roles.workspace_id IS 'Reference to the workspace this system has a role in.';
COMMENT ON COLUMN public.jarvis_system_workspace_roles.system_role IS 'Role of the system in this workspace (e.g., "executive", "ops_controller", "communications_hub").';
COMMENT ON COLUMN public.jarvis_system_workspace_roles.scope IS 'Scope of access/permissions (e.g., "full", "operations", "routing").';
COMMENT ON COLUMN public.jarvis_system_workspace_roles.metadata IS 'Additional metadata about the role mapping in JSON format.';

CREATE INDEX IF NOT EXISTS idx_system_workspace_roles_system ON public.jarvis_system_workspace_roles(system_id);
CREATE INDEX IF NOT EXISTS idx_system_workspace_roles_workspace ON public.jarvis_system_workspace_roles(workspace_id);
CREATE INDEX IF NOT EXISTS idx_system_workspace_roles_role ON public.jarvis_system_workspace_roles(system_role);

-- ============================================================================
-- jarvis_system_module_mappings: Maps systems to modules with roles
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jarvis_system_module_mappings (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id   uuid NOT NULL REFERENCES public.jarvis_global_systems(id) ON DELETE CASCADE,
  module_id   uuid NOT NULL REFERENCES public.modules(id) ON DELETE CASCADE,
  system_role text NOT NULL,
  scope       text NOT NULL,
  metadata    jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE(system_id, module_id)
);

COMMENT ON TABLE public.jarvis_system_module_mappings IS 'Maps global systems to specific modules with roles and scopes. Defines which systems can interact with which modules.';
COMMENT ON COLUMN public.jarvis_system_module_mappings.system_id IS 'Reference to the global system.';
COMMENT ON COLUMN public.jarvis_system_module_mappings.module_id IS 'Reference to the module this system can access.';
COMMENT ON COLUMN public.jarvis_system_module_mappings.system_role IS 'Role of the system for this module (e.g., "executive", "ops_controller").';
COMMENT ON COLUMN public.jarvis_system_module_mappings.scope IS 'Scope of access for this module (e.g., "full", "ops", "finance").';
COMMENT ON COLUMN public.jarvis_system_module_mappings.metadata IS 'Additional metadata about the module mapping in JSON format.';

CREATE INDEX IF NOT EXISTS idx_system_module_mappings_system ON public.jarvis_system_module_mappings(system_id);
CREATE INDEX IF NOT EXISTS idx_system_module_mappings_module ON public.jarvis_system_module_mappings(module_id);
CREATE INDEX IF NOT EXISTS idx_system_module_mappings_role ON public.jarvis_system_module_mappings(system_role);

-- ============================================================================
-- nexus_integration_placeholders: Placeholder configuration for Nexus integration
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.nexus_integration_placeholders (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id        uuid NOT NULL REFERENCES public.jarvis_global_systems(id) ON DELETE CASCADE,
  expected_endpoint text,
  expected_schema  jsonb,
  connection_status text NOT NULL DEFAULT 'not_configured',
  metadata         jsonb,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.nexus_integration_placeholders IS 'Placeholder configuration for Nexus integration. Stores expected endpoints and schemas before actual integration.';
COMMENT ON COLUMN public.nexus_integration_placeholders.system_id IS 'Reference to the Nexus global system.';
COMMENT ON COLUMN public.nexus_integration_placeholders.expected_endpoint IS 'Expected API endpoint URL for Nexus integration (placeholder).';
COMMENT ON COLUMN public.nexus_integration_placeholders.expected_schema IS 'Expected API schema/contract in JSON format (placeholder).';
COMMENT ON COLUMN public.nexus_integration_placeholders.connection_status IS 'Integration status: not_configured, pending, connected, error.';
COMMENT ON COLUMN public.nexus_integration_placeholders.metadata IS 'Additional metadata about the integration placeholder in JSON format.';

CREATE INDEX IF NOT EXISTS idx_nexus_integration_placeholders_system ON public.nexus_integration_placeholders(system_id);
CREATE INDEX IF NOT EXISTS idx_nexus_integration_placeholders_status ON public.nexus_integration_placeholders(connection_status);

-- ============================================================================
-- ghexit_integration_placeholders: Placeholder configuration for Ghexit integration
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ghexit_integration_placeholders (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id        uuid NOT NULL REFERENCES public.jarvis_global_systems(id) ON DELETE CASCADE,
  protocol         text DEFAULT 'pending',
  connection_status text NOT NULL DEFAULT 'not_configured',
  metadata         jsonb,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.ghexit_integration_placeholders IS 'Placeholder configuration for Ghexit Telecom integration. Stores protocol and connection details before actual integration.';
COMMENT ON COLUMN public.ghexit_integration_placeholders.system_id IS 'Reference to the Ghexit Telecom global system.';
COMMENT ON COLUMN public.ghexit_integration_placeholders.protocol IS 'Communication protocol (e.g., "http", "websocket", "grpc", "pending").';
COMMENT ON COLUMN public.ghexit_integration_placeholders.connection_status IS 'Integration status: not_configured, pending, connected, error.';
COMMENT ON COLUMN public.ghexit_integration_placeholders.metadata IS 'Additional metadata about the integration placeholder in JSON format.';

CREATE INDEX IF NOT EXISTS idx_ghexit_integration_placeholders_system ON public.ghexit_integration_placeholders(system_id);
CREATE INDEX IF NOT EXISTS idx_ghexit_integration_placeholders_status ON public.ghexit_integration_placeholders(connection_status);

-- ============================================================================
-- Enable Row Level Security
-- ============================================================================

ALTER TABLE public.jarvis_system_workspace_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_system_module_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nexus_integration_placeholders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ghexit_integration_placeholders ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies for jarvis_system_workspace_roles
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_system_workspace_roles'
      AND policyname = 'jarvis_system_workspace_roles_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_system_workspace_roles_workspace_members" ON public.jarvis_system_workspace_roles
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
-- RLS Policies for jarvis_system_module_mappings
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_system_module_mappings'
      AND policyname = 'jarvis_system_module_mappings_workspace_members'
  ) THEN
    CREATE POLICY "jarvis_system_module_mappings_workspace_members" ON public.jarvis_system_module_mappings
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          module_id IN (
            SELECT m.id FROM public.modules m
            JOIN public.jarvis_workspace_members wm ON wm.workspace_id = m.workspace_id
            WHERE wm.user_id = auth.uid()
          )
        )
      );
  END IF;
END $$;

-- ============================================================================
-- RLS Policies for nexus_integration_placeholders
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'nexus_integration_placeholders'
      AND policyname = 'nexus_integration_placeholders_tenant_members'
  ) THEN
    CREATE POLICY "nexus_integration_placeholders_tenant_members" ON public.nexus_integration_placeholders
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

-- ============================================================================
-- RLS Policies for ghexit_integration_placeholders
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'ghexit_integration_placeholders'
      AND policyname = 'ghexit_integration_placeholders_tenant_members'
  ) THEN
    CREATE POLICY "ghexit_integration_placeholders_tenant_members" ON public.ghexit_integration_placeholders
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

