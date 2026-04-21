-- Seed 007: Global Systems and Bindings
-- Registers Jarvis, Nexus, and Ghexit Telecom as global systems
-- Creates workspace bindings and event consumers for each system

DO $$
DECLARE
  v_owner_id uuid := '1ee91f2a-65aa-4c5a-bbca-f979fa0bfac8';
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_jarvis_system_id uuid;
  v_nexus_system_id uuid;
  v_ghexit_system_id uuid;
  v_binding_id uuid;
  v_consumer_id uuid;
  v_workspace_slug text;
BEGIN
  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Tenant "agyeman-enterprises" not found. Please run 001_seed_tenant.sql first.';
  END IF;

  -- ============================================================================
  -- Step 1: Register Global Systems
  -- ============================================================================

  -- Register Jarvis
  INSERT INTO public.jarvis_global_systems (tenant_id, slug, name, system_type, description, metadata)
  VALUES (
    v_tenant_id,
    'jarvis',
    'Jarvis AI CEO',
    'ai_ceo',
    'AI CEO assistant system that provides executive-level decision support and orchestration',
    jsonb_build_object('version', '1.0.0', 'capabilities', ARRAY['decision_support', 'orchestration', 'briefings'])
  )
  ON CONFLICT (slug) DO UPDATE
  SET name = EXCLUDED.name,
      system_type = EXCLUDED.system_type,
      description = EXCLUDED.description,
      updated_at = now()
  RETURNING id INTO v_jarvis_system_id;

  IF v_jarvis_system_id IS NULL THEN
    SELECT id INTO v_jarvis_system_id FROM public.jarvis_global_systems WHERE slug = 'jarvis';
  END IF;

  RAISE NOTICE 'Jarvis global system registered (%)', v_jarvis_system_id;

  -- Register Nexus
  INSERT INTO public.jarvis_global_systems (tenant_id, slug, name, system_type, description, metadata)
  VALUES (
    v_tenant_id,
    'nexus',
    'Nexus BizOps OS',
    'bizops_os',
    'Business operations operating system for managing portfolio, companies, and business intelligence',
    jsonb_build_object('version', '1.0.0', 'capabilities', ARRAY['portfolio_management', 'business_intelligence', 'analytics'])
  )
  ON CONFLICT (slug) DO UPDATE
  SET name = EXCLUDED.name,
      system_type = EXCLUDED.system_type,
      description = EXCLUDED.description,
      updated_at = now()
  RETURNING id INTO v_nexus_system_id;

  IF v_nexus_system_id IS NULL THEN
    SELECT id INTO v_nexus_system_id FROM public.jarvis_global_systems WHERE slug = 'nexus';
  END IF;

  RAISE NOTICE 'Nexus global system registered (%)', v_nexus_system_id;

  -- Register Ghexit Telecom
  INSERT INTO public.jarvis_global_systems (tenant_id, slug, name, system_type, description, metadata)
  VALUES (
    v_tenant_id,
    'ghexit_telecom',
    'Ghexit Telecom Infrastructure',
    'telecom_infra',
    'Telecommunications infrastructure layer for messaging, routing, and communication services',
    jsonb_build_object('version', '1.0.0', 'capabilities', ARRAY['messaging', 'routing', 'telecom'])
  )
  ON CONFLICT (slug) DO UPDATE
  SET name = EXCLUDED.name,
      system_type = EXCLUDED.system_type,
      description = EXCLUDED.description,
      updated_at = now()
  RETURNING id INTO v_ghexit_system_id;

  IF v_ghexit_system_id IS NULL THEN
    SELECT id INTO v_ghexit_system_id FROM public.jarvis_global_systems WHERE slug = 'ghexit_telecom';
  END IF;

  RAISE NOTICE 'Ghexit Telecom global system registered (%)', v_ghexit_system_id;

  -- ============================================================================
  -- Step 2: Create Workspace Bindings
  -- ============================================================================

  -- Bind all systems to all workspaces with admin access
  FOR v_workspace_id, v_workspace_slug IN
    SELECT id, slug FROM public.workspaces WHERE tenant_id = v_tenant_id
  LOOP
    -- Jarvis bindings
    INSERT INTO public.jarvis_system_workspace_bindings (system_id, workspace_id, access_level, metadata)
    VALUES (v_jarvis_system_id, v_workspace_id, 'admin', jsonb_build_object('workspace_slug', v_workspace_slug))
    ON CONFLICT (system_id, workspace_id) DO NOTHING
    RETURNING id INTO v_binding_id;
    
    -- Nexus bindings
    INSERT INTO public.jarvis_system_workspace_bindings (system_id, workspace_id, access_level, metadata)
    VALUES (v_nexus_system_id, v_workspace_id, 'admin', jsonb_build_object('workspace_slug', v_workspace_slug))
    ON CONFLICT (system_id, workspace_id) DO NOTHING;
    
    -- Ghexit Telecom bindings
    INSERT INTO public.jarvis_system_workspace_bindings (system_id, workspace_id, access_level, metadata)
    VALUES (v_ghexit_system_id, v_workspace_id, 'admin', jsonb_build_object('workspace_slug', v_workspace_slug))
    ON CONFLICT (system_id, workspace_id) DO NOTHING;
  END LOOP;

  RAISE NOTICE 'Global system workspace bindings seeded';

  -- ============================================================================
  -- Step 3: Create Event Consumers
  -- ============================================================================

  -- Jarvis event consumers - consumes all events
  INSERT INTO public.jarvis_event_consumers (system_id, event_type, handler_type, handler_config, is_active)
  VALUES (
    v_jarvis_system_id,
    '*',
    'internal',
    jsonb_build_object('route', 'jarvis'),
    true
  )
  ON CONFLICT DO NOTHING
  RETURNING id INTO v_consumer_id;

  -- Nexus event consumers
  INSERT INTO public.jarvis_event_consumers (system_id, event_type, handler_type, handler_config, is_active)
  VALUES
    (v_nexus_system_id, 'company.*', 'internal', jsonb_build_object('route', 'nexus'), true),
    (v_nexus_system_id, 'module.*', 'internal', jsonb_build_object('route', 'nexus'), true),
    (v_nexus_system_id, 'workspace.*', 'internal', jsonb_build_object('route', 'nexus'), true),
    (v_nexus_system_id, 'kg.entity.*', 'internal', jsonb_build_object('route', 'nexus'), true)
  ON CONFLICT DO NOTHING;

  -- Ghexit Telecom event consumers
  INSERT INTO public.jarvis_event_consumers (system_id, event_type, handler_type, handler_config, is_active)
  VALUES
    (v_ghexit_system_id, 'telecom.*', 'internal', jsonb_build_object('route', 'ghexit'), true),
    (v_ghexit_system_id, 'agent.triggered', 'internal', jsonb_build_object('route', 'ghexit'), true)
  ON CONFLICT DO NOTHING;

  RAISE NOTICE 'Global system event consumers seeded';

  -- Summary
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Global Systems Seeding Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Systems registered: 3';
  RAISE NOTICE 'Workspace bindings: % (per system)', (SELECT COUNT(*) FROM public.workspaces WHERE tenant_id = v_tenant_id);
  RAISE NOTICE 'Event consumers: 7 total';

END $$;

