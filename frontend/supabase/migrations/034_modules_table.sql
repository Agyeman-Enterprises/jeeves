-- Migration 034: Modules Table
-- Creates table for storing module metadata

CREATE TABLE IF NOT EXISTS public.modules (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid REFERENCES public.workspaces(id) ON DELETE CASCADE,
  tenant_id   uuid REFERENCES public.tenants(id) ON DELETE CASCADE,
  name        text NOT NULL,
  slug        text NOT NULL,
  version     text,
  description text,
  metadata    jsonb,
  is_active   boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE(workspace_id, slug)
);

COMMENT ON TABLE public.modules IS 'Module metadata for workspaces. Modules are features or capabilities available within a workspace.';

CREATE INDEX IF NOT EXISTS idx_modules_workspace ON public.modules(workspace_id);
CREATE INDEX IF NOT EXISTS idx_modules_tenant ON public.modules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_modules_slug ON public.modules(slug);

ALTER TABLE public.modules ENABLE ROW LEVEL SECURITY;

-- RLS Policy for modules
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'modules'
      AND policyname = 'modules_workspace_members'
  ) THEN
    CREATE POLICY "modules_workspace_members" ON public.modules
      FOR SELECT USING (
        auth.uid() IS NOT NULL AND (
          EXISTS (
            SELECT 1 FROM public.jarvis_workspace_members m
            WHERE m.workspace_id = modules.workspace_id
            AND m.user_id = auth.uid()
          )
        )
      );
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'modules'
      AND policyname = 'modules_workspace_members_modify'
  ) THEN
    CREATE POLICY "modules_workspace_members_modify" ON public.modules
      FOR ALL USING (
        auth.uid() IS NOT NULL AND (
          EXISTS (
            SELECT 1 FROM public.jarvis_workspace_members m
            WHERE m.workspace_id = modules.workspace_id
            AND m.user_id = auth.uid()
          )
        )
      )
      WITH CHECK (
        auth.uid() IS NOT NULL AND (
          EXISTS (
            SELECT 1 FROM public.jarvis_workspace_members m
            WHERE m.workspace_id = modules.workspace_id
            AND m.user_id = auth.uid()
          )
        )
      );
  END IF;
END $$;

