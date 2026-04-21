-- Seed 006: Knowledge Graph Entities
-- Creates KG entity nodes for workspaces, companies, modules, and industries

DO $$
DECLARE
  v_owner_id uuid := '1ee91f2a-65aa-4c5a-bbca-f979fa0bfac8';
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_company_id uuid;
  v_module_id uuid;
  v_node_id uuid;
  v_workspace_slug text;
  v_workspace_name text;
  v_company_name text;
  v_module_name text;
  v_industry text;
BEGIN
  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Tenant "agyeman-enterprises" not found. Please run 001_seed_tenant.sql first.';
  END IF;

  -- Create tenant-level entity
  SELECT id INTO v_node_id FROM public.jarvis_universe_nodes
  WHERE user_id = v_owner_id 
    AND workspace_id IS NULL
    AND metadata->>'external_id' = 'tenant:agyeman-enterprises';
  
  IF v_node_id IS NULL THEN
    INSERT INTO public.jarvis_universe_nodes (
      user_id,
      workspace_id,
      metadata
    )
    VALUES (
      v_owner_id,
      NULL, -- Tenant-level, no workspace
      jsonb_build_object(
        'node_type', 'ENTITY',
        'domain', 'OPERATIONS',
        'label', 'Agyeman Enterprises',
        'description', 'Root organizational container for Agyeman Enterprises portfolio',
        'source_system', 'jarvis.identity',
        'external_id', 'tenant:agyeman-enterprises',
        'entity_type', 'tenant'
      )
    )
    RETURNING id INTO v_node_id;
    
    RAISE NOTICE 'Created KG node: Agyeman Enterprises (tenant) (%)', v_node_id;
  ELSE
    RAISE NOTICE 'KG node already exists: Agyeman Enterprises (tenant) (%)', v_node_id;
  END IF;

  -- Create workspace entities
  FOR v_workspace_id, v_workspace_name, v_workspace_slug IN
    SELECT id, name, slug FROM public.workspaces 
    WHERE tenant_id = v_tenant_id
  LOOP
    -- Determine domain from workspace name
    v_industry := CASE
      WHEN v_workspace_slug = 'global-systems' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'healthcare' THEN 'CLINICAL'
      WHEN v_workspace_slug = 'technology-saas' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'creative-retail' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'publishing-media' THEN 'MEDIA'
      WHEN v_workspace_slug = 'crypto-gaming' THEN 'GAMING'
      WHEN v_workspace_slug = 'education' THEN 'EDUCATION'
      WHEN v_workspace_slug = 'engineering-manufacturing' THEN 'MANUFACTURING'
      WHEN v_workspace_slug = 'finance' THEN 'FINANCIAL'
      ELSE 'OPERATIONS'
    END;

    SELECT id INTO v_node_id FROM public.jarvis_universe_nodes
    WHERE user_id = v_owner_id 
      AND workspace_id = v_workspace_id
      AND metadata->>'external_id' = 'workspace:' || v_workspace_slug;
    
    IF v_node_id IS NULL THEN
      INSERT INTO public.jarvis_universe_nodes (
        user_id,
        workspace_id,
        metadata
      )
      VALUES (
        v_owner_id,
        v_workspace_id,
        jsonb_build_object(
          'node_type', 'ENTITY',
          'domain', v_industry,
          'label', v_workspace_name,
          'description', 'Workspace: ' || v_workspace_name,
          'source_system', 'jarvis.identity',
          'external_id', 'workspace:' || v_workspace_slug,
          'entity_type', 'workspace',
          'workspace_slug', v_workspace_slug
        )
      )
      RETURNING id INTO v_node_id;
      
      RAISE NOTICE 'Created KG node: % (workspace) (%)', v_workspace_name, v_node_id;
    ELSE
      RAISE NOTICE 'KG node already exists: % (workspace) (%)', v_workspace_name, v_node_id;
    END IF;
  END LOOP;

  -- Create company entities
  FOR v_company_id, v_company_name, v_workspace_id, v_workspace_slug IN
    SELECT c.id, c.name, c.workspace_id, w.slug
    FROM public.jarvis_companies c
    JOIN public.workspaces w ON w.id = c.workspace_id
    WHERE c.tenant_id = v_tenant_id
  LOOP
    -- Determine domain from workspace
    v_industry := CASE
      WHEN v_workspace_slug = 'global-systems' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'healthcare' THEN 'CLINICAL'
      WHEN v_workspace_slug = 'technology-saas' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'creative-retail' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'publishing-media' THEN 'MEDIA'
      WHEN v_workspace_slug = 'crypto-gaming' THEN 'GAMING'
      WHEN v_workspace_slug = 'education' THEN 'EDUCATION'
      WHEN v_workspace_slug = 'engineering-manufacturing' THEN 'MANUFACTURING'
      WHEN v_workspace_slug = 'finance' THEN 'FINANCIAL'
      ELSE 'OPERATIONS'
    END;

    SELECT id INTO v_node_id FROM public.jarvis_universe_nodes
    WHERE user_id = v_owner_id 
      AND workspace_id = v_workspace_id
      AND metadata->>'external_id' = 'company:' || v_company_id::text;
    
    IF v_node_id IS NULL THEN
      INSERT INTO public.jarvis_universe_nodes (
        user_id,
        workspace_id,
        metadata
      )
      VALUES (
        v_owner_id,
        v_workspace_id,
        jsonb_build_object(
          'node_type', 'ENTITY',
          'domain', v_industry,
          'label', v_company_name,
          'description', 'Company: ' || v_company_name,
          'source_system', 'jarvis.identity',
          'external_id', 'company:' || v_company_id::text,
          'entity_type', 'company',
          'company_id', v_company_id::text,
          'workspace_slug', v_workspace_slug
        )
      )
      RETURNING id INTO v_node_id;
      
      RAISE NOTICE 'Created KG node: % (company) (%)', v_company_name, v_node_id;
    ELSE
      RAISE NOTICE 'KG node already exists: % (company) (%)', v_company_name, v_node_id;
    END IF;
  END LOOP;

  -- Create module entities
  FOR v_module_id, v_module_name, v_workspace_id, v_workspace_slug IN
    SELECT m.id, m.name, m.workspace_id, w.slug
    FROM public.modules m
    JOIN public.workspaces w ON w.id = m.workspace_id
    WHERE m.tenant_id = v_tenant_id
  LOOP
    -- Determine domain from workspace
    v_industry := CASE
      WHEN v_workspace_slug = 'global-systems' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'healthcare' THEN 'CLINICAL'
      WHEN v_workspace_slug = 'technology-saas' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'creative-retail' THEN 'OPERATIONS'
      WHEN v_workspace_slug = 'publishing-media' THEN 'MEDIA'
      WHEN v_workspace_slug = 'crypto-gaming' THEN 'GAMING'
      WHEN v_workspace_slug = 'education' THEN 'EDUCATION'
      WHEN v_workspace_slug = 'engineering-manufacturing' THEN 'MANUFACTURING'
      WHEN v_workspace_slug = 'finance' THEN 'FINANCIAL'
      ELSE 'OPERATIONS'
    END;

    SELECT id INTO v_node_id FROM public.jarvis_universe_nodes
    WHERE user_id = v_owner_id 
      AND workspace_id = v_workspace_id
      AND metadata->>'external_id' = 'module:' || v_module_id::text;
    
    IF v_node_id IS NULL THEN
      INSERT INTO public.jarvis_universe_nodes (
        user_id,
        workspace_id,
        metadata
      )
      VALUES (
        v_owner_id,
        v_workspace_id,
        jsonb_build_object(
          'node_type', 'ENTITY',
          'domain', v_industry,
          'label', v_module_name,
          'description', 'Module: ' || v_module_name,
          'source_system', 'jarvis.modules',
          'external_id', 'module:' || v_module_id::text,
          'entity_type', 'module',
          'module_id', v_module_id::text,
          'workspace_slug', v_workspace_slug
        )
      )
      RETURNING id INTO v_node_id;
      
      RAISE NOTICE 'Created KG node: % (module) (%)', v_module_name, v_node_id;
    ELSE
      RAISE NOTICE 'KG node already exists: % (module) (%)', v_module_name, v_node_id;
    END IF;
  END LOOP;

  -- Create industry entities
  FOR v_industry IN
    SELECT DISTINCT unnest(ARRAY[
      'CLINICAL',
      'FINANCIAL',
      'EDUCATION',
      'MEDIA',
      'GAMING',
      'MANUFACTURING',
      'OPERATIONS'
    ])
  LOOP
    SELECT id INTO v_node_id FROM public.jarvis_universe_nodes
    WHERE user_id = v_owner_id 
      AND workspace_id IS NULL
      AND metadata->>'external_id' = 'industry:' || lower(v_industry);
    
    IF v_node_id IS NULL THEN
      INSERT INTO public.jarvis_universe_nodes (
        user_id,
        workspace_id,
        metadata
      )
      VALUES (
        v_owner_id,
        NULL, -- Industry-level, no workspace
        jsonb_build_object(
          'node_type', 'ENTITY',
          'domain', v_industry,
          'label', v_industry || ' Industry',
          'description', 'Industry category: ' || v_industry,
          'source_system', 'jarvis.identity',
          'external_id', 'industry:' || lower(v_industry),
          'entity_type', 'industry'
        )
      )
      RETURNING id INTO v_node_id;
      
      RAISE NOTICE 'Created KG node: % (industry) (%)', v_industry, v_node_id;
    ELSE
      RAISE NOTICE 'KG node already exists: % (industry) (%)', v_industry, v_node_id;
    END IF;
  END LOOP;

  RAISE NOTICE 'Seeding complete! Created knowledge graph entities.';

END $$;

