-- Seed 010: Event Simulation Baseline
-- Creates a small baseline of simulation events to test routing concepts
-- All events are marked with is_simulation = TRUE and source_system_slug = 'simulation'

DO $$
DECLARE
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_workspace_slug text;
  v_company_id uuid;
  v_module_id uuid;
  v_event_count integer := 0;
  v_owner_id uuid := '1ee91f2a-65aa-4c5a-bbca-f979fa0bfac8';
BEGIN
  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';

  IF v_tenant_id IS NULL THEN
    RAISE NOTICE 'Tenant agyeman-enterprises not found, skipping simulation baseline.';
    RETURN;
  END IF;

  -- Verify owner exists
  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = v_owner_id) THEN
    RAISE NOTICE 'Owner user not found, skipping simulation baseline.';
    RETURN;
  END IF;

  -- ============================================================================
  -- Step 1: Workspace-level events
  -- ============================================================================

  FOR v_workspace_id, v_workspace_slug IN
    SELECT id, slug FROM public.workspaces WHERE tenant_id = v_tenant_id
  LOOP
    -- workspace.updated event
    INSERT INTO public.jarvis_events (
      tenant_id,
      workspace_id,
      user_id,
      event_type,
      source,
      source_system_slug,
      payload,
      is_simulation,
      status
    ) VALUES (
      v_tenant_id,
      v_workspace_id,
      v_owner_id,
      'workspace.updated',
      'simulation.workspace',
      'simulation',
      jsonb_build_object(
        'workspace_slug', v_workspace_slug,
        'note', 'Initial simulation event for workspace baseline',
        'simulation_run', 'baseline_001'
      ),
      true,
      'stored'
    )
    ON CONFLICT DO NOTHING;
    
    v_event_count := v_event_count + 1;
  END LOOP;

  RAISE NOTICE 'Created % workspace.updated simulation events', v_event_count;

  -- ============================================================================
  -- Step 2: Company-level events (company.created)
  -- ============================================================================

  v_event_count := 0;
  FOR v_company_id, v_workspace_id IN
    SELECT id, workspace_id FROM public.jarvis_companies 
    WHERE tenant_id = v_tenant_id
    LIMIT 10  -- Limit to first 10 companies for baseline
  LOOP
    INSERT INTO public.jarvis_events (
      tenant_id,
      workspace_id,
      company_id,
      user_id,
      event_type,
      source,
      source_system_slug,
      payload,
      is_simulation,
      status
    ) VALUES (
      v_tenant_id,
      v_workspace_id,
      v_company_id,
      v_owner_id,
      'company.created',
      'simulation.company',
      'simulation',
      jsonb_build_object(
        'company_id', v_company_id::text,
        'note', 'Simulation event: company created',
        'simulation_run', 'baseline_001'
      ),
      true,
      'stored'
    )
    ON CONFLICT DO NOTHING;
    
    v_event_count := v_event_count + 1;
  END LOOP;

  RAISE NOTICE 'Created % company.created simulation events', v_event_count;

  -- ============================================================================
  -- Step 3: Module-level events (module.created)
  -- ============================================================================

  v_event_count := 0;
  FOR v_module_id, v_workspace_id IN
    SELECT id, workspace_id FROM public.modules 
    WHERE tenant_id = v_tenant_id
    LIMIT 10  -- Limit to first 10 modules for baseline
  LOOP
    INSERT INTO public.jarvis_events (
      tenant_id,
      workspace_id,
      module_id,
      user_id,
      event_type,
      source,
      source_system_slug,
      payload,
      is_simulation,
      status
    ) VALUES (
      v_tenant_id,
      v_workspace_id,
      v_module_id,
      v_owner_id,
      'module.created',
      'simulation.module',
      'simulation',
      jsonb_build_object(
        'module_id', v_module_id::text,
        'note', 'Simulation event: module created',
        'simulation_run', 'baseline_001'
      ),
      true,
      'stored'
    )
    ON CONFLICT DO NOTHING;
    
    v_event_count := v_event_count + 1;
  END LOOP;

  RAISE NOTICE 'Created % module.created simulation events', v_event_count;

  -- ============================================================================
  -- Step 4: Knowledge Graph entity events (kg.entity.created)
  -- ============================================================================

  v_event_count := 0;
  -- Create a few kg.entity.created events for different entity types
  FOR v_workspace_id, v_workspace_slug IN
    SELECT id, slug FROM public.workspaces 
    WHERE tenant_id = v_tenant_id
    LIMIT 5  -- Limit to 5 workspaces for KG events
  LOOP
    INSERT INTO public.jarvis_events (
      tenant_id,
      workspace_id,
      user_id,
      event_type,
      source,
      source_system_slug,
      payload,
      is_simulation,
      status
    ) VALUES (
      v_tenant_id,
      v_workspace_id,
      v_owner_id,
      'kg.entity.created',
      'simulation.kg',
      'simulation',
      jsonb_build_object(
        'workspace_slug', v_workspace_slug,
        'entity_type', 'workspace',
        'note', 'Simulation event: KG entity created',
        'simulation_run', 'baseline_001'
      ),
      true,
      'stored'
    )
    ON CONFLICT DO NOTHING;
    
    v_event_count := v_event_count + 1;
  END LOOP;

  RAISE NOTICE 'Created % kg.entity.created simulation events', v_event_count;

  -- Summary
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Event Simulation Baseline Seeding Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'All events marked with is_simulation = TRUE';
  RAISE NOTICE 'All events have source_system_slug = "simulation"';
  RAISE NOTICE 'Events can be queried per workspace, company, or module';

END $$;

