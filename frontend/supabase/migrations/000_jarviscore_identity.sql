-- Migration 000: JarvisCore Identity Tables
-- Creates the core identity tables: tenants, workspaces, and workspace members
-- This should run before any migrations that reference these tables

-- tenants: Root organizational container
CREATE TABLE IF NOT EXISTS public.tenants (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  slug        text UNIQUE,
  metadata    jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.tenants IS 'Root organizational container. Represents top-level organizations/companies. Each tenant can have multiple workspaces.';

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON public.tenants(slug);

-- workspaces: Business/project containers within a tenant
CREATE TABLE IF NOT EXISTS public.workspaces (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   uuid NOT NULL REFERENCES public.tenants(id),
  owner_id    uuid NOT NULL REFERENCES auth.users(id),
  name        text NOT NULL,
  slug        text,
  description text,
  metadata    jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.workspaces IS 'Business/project containers within a tenant. Workspaces isolate data and enable multi-tenancy. Each workspace belongs to one tenant and has one owner.';

CREATE INDEX IF NOT EXISTS idx_workspaces_tenant ON public.workspaces(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON public.workspaces(owner_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_workspaces_tenant_slug ON public.workspaces(tenant_id, slug) WHERE slug IS NOT NULL;

-- jarvis_workspace_members: Join table linking users to workspaces
CREATE TABLE IF NOT EXISTS public.jarvis_workspace_members (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
  user_id     uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role        text,
  metadata    jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id, user_id)
);

COMMENT ON TABLE public.jarvis_workspace_members IS 'Join table linking users to workspaces. Defines membership and access control. Includes role information.';

CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace ON public.jarvis_workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON public.jarvis_workspace_members(user_id);

-- Enable RLS
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jarvis_workspace_members ENABLE ROW LEVEL SECURITY;

-- RLS Policies for tenants
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'tenants'
      AND policyname = 'tenants_select'
  ) THEN
    CREATE POLICY "tenants_select" ON public.tenants
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          EXISTS (
            SELECT 1 FROM public.workspaces w
            JOIN public.jarvis_workspace_members m ON m.workspace_id = w.id
            WHERE w.tenant_id = tenants.id
            AND m.user_id = auth.uid()
          )
        )
      );
  END IF;
END $$;

-- RLS Policies for workspaces
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'workspaces'
      AND policyname = 'workspaces_workspace_members'
  ) THEN
    CREATE POLICY "workspaces_workspace_members" ON public.workspaces
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          owner_id = auth.uid() OR
          EXISTS (
            SELECT 1 FROM public.jarvis_workspace_members m
            WHERE m.workspace_id = workspaces.id
            AND m.user_id = auth.uid()
          )
        )
      );
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'workspaces'
      AND policyname = 'workspaces_owner_modify'
  ) THEN
    CREATE POLICY "workspaces_owner_modify" ON public.workspaces
      FOR UPDATE USING (owner_id = auth.uid())
      WITH CHECK (owner_id = auth.uid());
  END IF;
END $$;

-- RLS Policies for workspace members
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_workspace_members'
      AND policyname = 'workspace_members_select'
  ) THEN
    CREATE POLICY "workspace_members_select" ON public.jarvis_workspace_members
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          user_id = auth.uid() OR
          EXISTS (
            SELECT 1 FROM public.workspaces w
            WHERE w.id = jarvis_workspace_members.workspace_id
            AND w.owner_id = auth.uid()
          )
        )
      );
  END IF;
END $$;

