-- Seed 009: System Mappings
-- Creates workspace role mappings, module mappings, and integration placeholders for global systems

DO $$
DECLARE
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_module_id uuid;
  v_jarvis_system_id uuid;
  v_nexus_system_id uuid;
  v_ghexit_system_id uuid;
  v_workspace_slug text;
  v_workspace_name text;
  v_mapping_count integer := 0;
  v_nexus_placeholder_id uuid;
  v_ghexit_placeholder_id uuid;
BEGIN
  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Tenant "agyeman-enterprises" not found. Please run 001_seed_tenant.sql first.';
  END IF;

  -- Get system IDs
  SELECT id INTO v_jarvis_system_id FROM public.jarvis_global_systems WHERE slug = 'jarvis';
  SELECT id INTO v_nexus_system_id FROM public.jarvis_global_systems WHERE slug = 'nexus';
  SELECT id INTO v_ghexit_system_id FROM public.jarvis_global_systems WHERE slug = 'ghexit_telecom';

  IF v_jarvis_system_id IS NULL OR v_nexus_system_id IS NULL OR v_ghexit_system_id IS NULL THEN
    RAISE EXCEPTION 'Global systems not found. Please run 007_seed_global_systems.sql first.';
  END IF;

  -- ============================================================================
  -- Step 1: Workspace Role Mappings
  -- ============================================================================

  -- Jarvis → "executive", scope "full" (all workspaces)
  FOR v_workspace_id, v_workspace_slug, v_workspace_name IN
    SELECT id, slug, name FROM public.workspaces WHERE tenant_id = v_tenant_id
  LOOP
    INSERT INTO public.jarvis_system_workspace_roles (system_id, workspace_id, system_role, scope, metadata)
    VALUES (
      v_jarvis_system_id,
      v_workspace_id,
      'executive',
      'full',
      jsonb_build_object('workspace_slug', v_workspace_slug, 'workspace_name', v_workspace_name)
    )
    ON CONFLICT (system_id, workspace_id) DO NOTHING;
    
    v_mapping_count := v_mapping_count + 1;
  END LOOP;

  RAISE NOTICE 'Jarvis workspace role mappings created: % workspaces', v_mapping_count;

  -- Nexus → "ops_controller", scope "operations" (EXCLUDE Global Systems)
  v_mapping_count := 0;
  FOR v_workspace_id, v_workspace_slug, v_workspace_name IN
    SELECT id, slug, name FROM public.workspaces 
    WHERE tenant_id = v_tenant_id AND slug != 'global-systems'
  LOOP
    INSERT INTO public.jarvis_system_workspace_roles (system_id, workspace_id, system_role, scope, metadata)
    VALUES (
      v_nexus_system_id,
      v_workspace_id,
      'ops_controller',
      'operations',
      jsonb_build_object('workspace_slug', v_workspace_slug, 'workspace_name', v_workspace_name)
    )
    ON CONFLICT (system_id, workspace_id) DO NOTHING;
    
    v_mapping_count := v_mapping_count + 1;
  END LOOP;

  RAISE NOTICE 'Nexus workspace role mappings created: % workspaces (excluding Global Systems)', v_mapping_count;

  -- Ghexit → "communications_hub", scope "routing" (all workspaces)
  v_mapping_count := 0;
  FOR v_workspace_id, v_workspace_slug, v_workspace_name IN
    SELECT id, slug, name FROM public.workspaces WHERE tenant_id = v_tenant_id
  LOOP
    INSERT INTO public.jarvis_system_workspace_roles (system_id, workspace_id, system_role, scope, metadata)
    VALUES (
      v_ghexit_system_id,
      v_workspace_id,
      'communications_hub',
      'routing',
      jsonb_build_object('workspace_slug', v_workspace_slug, 'workspace_name', v_workspace_name)
    )
    ON CONFLICT (system_id, workspace_id) DO NOTHING;
    
    v_mapping_count := v_mapping_count + 1;
  END LOOP;

  RAISE NOTICE 'Ghexit workspace role mappings created: % workspaces', v_mapping_count;

  -- ============================================================================
  -- Step 2: Module Mappings
  -- ============================================================================

  -- Jarvis → all modules
  v_mapping_count := 0;
  FOR v_module_id IN
    SELECT id FROM public.modules WHERE tenant_id = v_tenant_id
  LOOP
    INSERT INTO public.jarvis_system_module_mappings (system_id, module_id, system_role, scope, metadata)
    VALUES (
      v_jarvis_system_id,
      v_module_id,
      'executive',
      'full',
      jsonb_build_object('mapping_type', 'full_access')
    )
    ON CONFLICT (system_id, module_id) DO NOTHING;
    
    v_mapping_count := v_mapping_count + 1;
  END LOOP;

  RAISE NOTICE 'Jarvis module mappings created: % modules', v_mapping_count;

  -- Nexus → modules with "ops" or "finance" scope
  -- This includes modules in Finance workspace and modules with ops/finance-related categories
  v_mapping_count := 0;
  FOR v_module_id IN
    SELECT m.id 
    FROM public.modules m
    JOIN public.workspaces w ON w.id = m.workspace_id
    WHERE m.tenant_id = v_tenant_id
      AND (
        w.slug = 'finance'
        OR w.slug LIKE '%ops%'
        OR w.slug LIKE '%operation%'
        OR m.metadata->>'category' IN ('finance', 'operations', 'ops')
        OR m.name ILIKE '%finance%'
        OR m.name ILIKE '%ops%'
        OR m.name ILIKE '%operation%'
        OR m.name ILIKE '%tax%'
        OR m.name ILIKE '%biz%'
        OR m.name ILIKE '%crm%'
      )
  LOOP
    INSERT INTO public.jarvis_system_module_mappings (system_id, module_id, system_role, scope, metadata)
    VALUES (
      v_nexus_system_id,
      v_module_id,
      'ops_controller',
      'operations',
      jsonb_build_object('mapping_type', 'ops_finance_scope')
    )
    ON CONFLICT (system_id, module_id) DO NOTHING;
    
    v_mapping_count := v_mapping_count + 1;
  END LOOP;

  RAISE NOTICE 'Nexus module mappings created: % modules (ops/finance scope)', v_mapping_count;

  -- Ghexit → none (placeholder only, no module mappings)

  -- ============================================================================
  -- Step 3: Integration Placeholders
  -- ============================================================================

  -- Nexus integration placeholder
  SELECT id INTO v_nexus_placeholder_id FROM public.nexus_integration_placeholders
  WHERE system_id = v_nexus_system_id;
  
  IF v_nexus_placeholder_id IS NULL THEN
    INSERT INTO public.nexus_integration_placeholders (
      system_id,
      expected_endpoint,
      expected_schema,
      connection_status,
      metadata
    )
    VALUES (
      v_nexus_system_id,
      'https://nexus.agyeman-enterprises.local/api/v1',
      jsonb_build_object(
        'version', '1.0.0',
        'endpoints', jsonb_build_array(
          jsonb_build_object('path', '/companies', 'method', 'GET'),
          jsonb_build_object('path', '/modules', 'method', 'GET'),
          jsonb_build_object('path', '/workspaces', 'method', 'GET'),
          jsonb_build_object('path', '/kg/entities', 'method', 'GET')
        )
      ),
      'not_configured',
      jsonb_build_object('note', 'Placeholder integration configuration for Nexus BizOps OS')
    )
    RETURNING id INTO v_nexus_placeholder_id;
    
    RAISE NOTICE 'Nexus integration placeholder created (%)', v_nexus_placeholder_id;
  ELSE
    RAISE NOTICE 'Nexus integration placeholder already exists (%)', v_nexus_placeholder_id;
  END IF;

  -- Ghexit integration placeholder
  SELECT id INTO v_ghexit_placeholder_id FROM public.ghexit_integration_placeholders
  WHERE system_id = v_ghexit_system_id;
  
  IF v_ghexit_placeholder_id IS NULL THEN
    INSERT INTO public.ghexit_integration_placeholders (
      system_id,
      protocol,
      connection_status,
      metadata
    )
    VALUES (
      v_ghexit_system_id,
      'pending',
      'not_configured',
      jsonb_build_object('note', 'Placeholder integration configuration for Ghexit Telecom Infrastructure')
    )
    RETURNING id INTO v_ghexit_placeholder_id;
    
    RAISE NOTICE 'Ghexit integration placeholder created (%)', v_ghexit_placeholder_id;
  ELSE
    RAISE NOTICE 'Ghexit integration placeholder already exists (%)', v_ghexit_placeholder_id;
  END IF;

  -- Summary
  RAISE NOTICE '========================================';
  RAISE NOTICE 'System Mappings Seeding Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Workspace role mappings: Created for all systems';
  RAISE NOTICE 'Module mappings: Jarvis (all), Nexus (ops/finance), Ghexit (none)';
  RAISE NOTICE 'Integration placeholders: Nexus and Ghexit configured';

END $$;

