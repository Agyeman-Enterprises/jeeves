-- Seed 005: Event Mesh Routes
-- Creates placeholder event subscriptions for core system events

DO $$
DECLARE
  v_owner_id uuid := '1ee91f2a-65aa-4c5a-bbca-f979fa0bfac8';
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_subscription_id uuid;
  v_event_type text;
  v_handler_key text;
  v_name text;
BEGIN
  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Tenant "agyeman-enterprises" not found. Please run 001_seed_tenant.sql first.';
  END IF;

  -- Get Global Systems workspace (for system-level events)
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'global-systems';
  
  IF v_workspace_id IS NULL THEN
    RAISE EXCEPTION 'Workspace "global-systems" not found. Please run 002_seed_workspaces.sql first.';
  END IF;

  -- Create event subscriptions for core system events
  FOR v_event_type, v_handler_key, v_name IN
    SELECT * FROM (VALUES
      ('company.created', 'jarvis.identity', 'Company Created Event Handler'),
      ('module.created', 'jarvis.modules', 'Module Created Event Handler'),
      ('user.assigned', 'jarvis.identity', 'User Assigned Event Handler'),
      ('agent.triggered', 'jarvis.agents', 'Agent Triggered Event Handler'),
      ('kg.entity.created', 'jarvis.knowledge_graph', 'Knowledge Graph Entity Created Handler')
    ) AS t(event_type, handler_key, name)
  LOOP
    -- Check if subscription already exists
    SELECT id INTO v_subscription_id FROM public.jarvis_event_subscriptions
    WHERE workspace_id = v_workspace_id 
      AND event_type = v_event_type 
      AND handler_key = v_handler_key;
    
    IF v_subscription_id IS NULL THEN
      INSERT INTO public.jarvis_event_subscriptions (
        workspace_id,
        user_id,
        name,
        event_type,
        filter_expr,
        handler_key,
        is_active
      )
      VALUES (
        v_workspace_id,
        v_owner_id,
        v_name,
        v_event_type,
        NULL, -- No filter for now
        v_handler_key,
        true
      )
      RETURNING id INTO v_subscription_id;
      
      RAISE NOTICE 'Created event subscription: % -> % (%)', v_event_type, v_handler_key, v_subscription_id;
    ELSE
      RAISE NOTICE 'Event subscription already exists: % -> % (%)', v_event_type, v_handler_key, v_subscription_id;
    END IF;
  END LOOP;

  RAISE NOTICE 'Seeding complete! Created event mesh routes.';

END $$;

