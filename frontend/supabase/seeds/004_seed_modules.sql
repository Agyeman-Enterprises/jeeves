-- Seed 004: Modules
-- Creates module entries for each workspace

DO $$
DECLARE
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_module_id uuid;
  v_module_name text;
  v_module_slug text;
  v_workspace_slug text;
BEGIN
  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Tenant "agyeman-enterprises" not found. Please run 001_seed_tenant.sql first.';
  END IF;

  -- Helper function to create slug from name
  CREATE OR REPLACE FUNCTION slugify(text) RETURNS text AS $$
    SELECT lower(regexp_replace(regexp_replace($1, '[^a-zA-Z0-9\s-]', '', 'g'), '\s+', '-', 'g'));
  $$ LANGUAGE sql IMMUTABLE;

  -- Global Systems modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'global-systems';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('Global Identity Module'),
      ('Agent Orchestration Module'),
      ('Event Router Module'),
      ('Ghexit Telecom Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Global Systems workspace',
      jsonb_build_object('workspace', 'global-systems', 'category', 'system'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Healthcare modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'healthcare';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('SoloPractice Module'),
      ('ScribeMD Module'),
      ('MyHealth Ally Module'),
      ('MedRx GLP Module'),
      ('Telemed Engine Module'),
      ('AccessMD Scheduling Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Healthcare workspace',
      jsonb_build_object('workspace', 'healthcare', 'category', 'healthcare'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Technology & SaaS modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'technology-saas';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('Synapse CRM Module'),
      ('BizBuilder Module'),
      ('WhoozOn Module'),
      ('FlyRyt Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Technology & SaaS workspace',
      jsonb_build_object('workspace', 'technology-saas', 'category', 'technology'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Creative & Retail modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'creative-retail';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('Furfubu Companion AI Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Creative & Retail workspace',
      jsonb_build_object('workspace', 'creative-retail', 'category', 'retail'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Publishing & Media modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'publishing-media';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('Publishing Engine Module'),
      ('Radio Streaming Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Publishing & Media workspace',
      jsonb_build_object('workspace', 'publishing-media', 'category', 'media'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Crypto & Gaming modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'crypto-gaming';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('Election Empire Module'),
      ('Meowtopia Lore Engine Module'),
      ('Purrkoin Blockchain Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Crypto & Gaming workspace',
      jsonb_build_object('workspace', 'crypto-gaming', 'category', 'gaming'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Education modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'education';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('Curriculum Engine Module'),
      ('Learning Delivery Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Education workspace',
      jsonb_build_object('workspace', 'education', 'category', 'education'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Engineering & Manufacturing modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'engineering-manufacturing';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('MediCore Module'),
      ('Reducicast Module'),
      ('ResusRunner Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Engineering & Manufacturing workspace',
      jsonb_build_object('workspace', 'engineering-manufacturing', 'category', 'engineering'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Finance modules
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'finance';
  
  FOR v_module_name IN
    SELECT * FROM (VALUES
      ('TaxRx Module'),
      ('EntityTaxPro Module'),
      ('Ultimate AI Trader Module')
    ) AS t(name)
  LOOP
    v_module_slug := slugify(v_module_name);
    
    INSERT INTO public.modules (workspace_id, tenant_id, name, slug, version, description, metadata, is_active)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_module_name,
      v_module_slug,
      '1.0.0',
      v_module_name || ' for Finance workspace',
      jsonb_build_object('workspace', 'finance', 'category', 'finance'),
      true
    )
    ON CONFLICT (workspace_id, slug) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id INTO v_module_id;
    
    IF v_module_id IS NULL THEN
      SELECT id INTO v_module_id FROM public.modules 
      WHERE workspace_id = v_workspace_id AND slug = v_module_slug;
    END IF;
    
    RAISE NOTICE 'Module: % (%)', v_module_name, v_module_id;
  END LOOP;

  -- Clean up helper function
  DROP FUNCTION IF EXISTS slugify(text);

  RAISE NOTICE 'Seeding complete! Created all modules.';

END $$;

