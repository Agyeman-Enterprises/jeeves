-- Seed 002: Agyeman Enterprises Workspaces
-- Creates all workspaces for the Agyeman Enterprises tenant

DO $$
DECLARE
  v_owner_id uuid := '1ee91f2a-65aa-4c5a-bbca-f979fa0bfac8';
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_workspace_slug text;
  v_workspace_name text;
  v_workspace_desc text;
BEGIN
  -- Verify owner exists
  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = v_owner_id) THEN
    RAISE EXCEPTION 'Owner user with id % not found in auth.users. Please verify the user exists.', v_owner_id;
  END IF;

  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Tenant "agyeman-enterprises" not found. Please run 001_seed_tenant.sql first.';
  END IF;

  -- Workspace definitions
  FOR v_workspace_name, v_workspace_slug, v_workspace_desc IN
    SELECT * FROM (VALUES
      ('Global Systems', 'global-systems', 'Core infrastructure and system workspaces'),
      ('Healthcare', 'healthcare', 'Healthcare business portfolio workspace'),
      ('Technology & SaaS', 'technology-saas', 'Technology and SaaS businesses workspace'),
      ('Creative & Retail', 'creative-retail', 'Creative and retail businesses workspace'),
      ('Publishing & Media', 'publishing-media', 'Publishing and media businesses workspace'),
      ('Crypto & Gaming', 'crypto-gaming', 'Cryptocurrency and gaming businesses workspace'),
      ('Education', 'education', 'Education businesses workspace'),
      ('Engineering & Manufacturing', 'engineering-manufacturing', 'Engineering and manufacturing businesses workspace'),
      ('Finance', 'finance', 'Finance and tax services workspace')
    ) AS t(name, slug, description)
  LOOP
    -- Insert or update workspace
    INSERT INTO public.workspaces (tenant_id, owner_id, name, slug, description, metadata)
    VALUES (
      v_tenant_id,
      v_owner_id,
      v_workspace_name,
      v_workspace_slug,
      v_workspace_desc,
      '{}'::jsonb
    )
    ON CONFLICT (tenant_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        owner_id = EXCLUDED.owner_id,
        updated_at = now()
    RETURNING id INTO v_workspace_id;

    IF v_workspace_id IS NULL THEN
      SELECT id INTO v_workspace_id FROM public.workspaces 
      WHERE tenant_id = v_tenant_id AND slug = v_workspace_slug;
    END IF;

    RAISE NOTICE 'Workspace: % (%)', v_workspace_name, v_workspace_id;
  END LOOP;

  RAISE NOTICE 'Seeding complete! Created/updated 9 workspaces.';

END $$;

