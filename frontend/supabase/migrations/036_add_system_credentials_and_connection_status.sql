-- Migration 036: System Credentials and Connection Status
-- Adds connection status tracking and credential storage for global systems

-- ============================================================================
-- Add connection_status column to jarvis_global_systems
-- ============================================================================

ALTER TABLE public.jarvis_global_systems
ADD COLUMN IF NOT EXISTS connection_status text NOT NULL DEFAULT 'not_configured';

COMMENT ON COLUMN public.jarvis_global_systems.connection_status IS 'Indicates system integration state: not_configured, pending, connected, error.';

-- ============================================================================
-- jarvis_system_credentials: Credential storage for global systems
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.jarvis_system_credentials (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id       uuid NOT NULL REFERENCES public.jarvis_global_systems(id) ON DELETE CASCADE,
  credential_type text NOT NULL,
  credential_hash text NOT NULL,
  scopes          jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata        jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE(system_id, credential_type)
);

COMMENT ON TABLE public.jarvis_system_credentials IS 'Credentials (placeholder) for external systems such as Nexus, Ghexit. No real keys stored yet.';
COMMENT ON COLUMN public.jarvis_system_credentials.system_id IS 'Reference to the global system these credentials belong to.';
COMMENT ON COLUMN public.jarvis_system_credentials.credential_type IS 'Type of credential (e.g., "api_key", "service_token", "oauth_token").';
COMMENT ON COLUMN public.jarvis_system_credentials.credential_hash IS 'Hashed or placeholder value for the credential. Real keys should be encrypted/hashed before storage.';
COMMENT ON COLUMN public.jarvis_system_credentials.scopes IS 'Array of permission scopes granted to this credential (e.g., ["admin"], ["read", "write"]).';
COMMENT ON COLUMN public.jarvis_system_credentials.metadata IS 'Additional metadata about the credential in JSON format.';

CREATE INDEX IF NOT EXISTS idx_system_credentials_system_id ON public.jarvis_system_credentials(system_id);
CREATE INDEX IF NOT EXISTS idx_system_credentials_type ON public.jarvis_system_credentials(credential_type);

-- ============================================================================
-- Enable Row Level Security
-- ============================================================================

ALTER TABLE public.jarvis_system_credentials ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies for jarvis_system_credentials
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_system_credentials'
      AND policyname = 'jarvis_system_credentials_tenant_members'
  ) THEN
    CREATE POLICY "jarvis_system_credentials_tenant_members" ON public.jarvis_system_credentials
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

  -- Only system owners/admins should be able to insert/update credentials
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'jarvis_system_credentials'
      AND policyname = 'jarvis_system_credentials_admin_only'
  ) THEN
    CREATE POLICY "jarvis_system_credentials_admin_only" ON public.jarvis_system_credentials
      FOR ALL USING (
        auth.uid() IS NOT NULL AND (
          system_id IN (
            SELECT gs.id FROM public.jarvis_global_systems gs
            JOIN public.workspaces w ON w.tenant_id = gs.tenant_id
            WHERE w.owner_id = auth.uid()
          )
        )
      )
      WITH CHECK (
        auth.uid() IS NOT NULL AND (
          system_id IN (
            SELECT gs.id FROM public.jarvis_global_systems gs
            JOIN public.workspaces w ON w.tenant_id = gs.tenant_id
            WHERE w.owner_id = auth.uid()
          )
        )
      );
  END IF;
END $$;

