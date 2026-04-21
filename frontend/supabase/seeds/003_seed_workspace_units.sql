-- Seed 003: Workspace Units (Companies)
-- Creates company entries in jarvis_companies for each workspace unit

DO $$
DECLARE
  v_owner_id uuid := '1ee91f2a-65aa-4c5a-bbca-f979fa0bfac8';
  v_tenant_id uuid;
  v_workspace_id uuid;
  v_company_id uuid;
  v_unit_name text;
  v_unit_type text;
  v_workspace_slug text;
BEGIN
  -- Get tenant ID
  SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'Tenant "agyeman-enterprises" not found. Please run 001_seed_tenant.sql first.';
  END IF;

  -- Global Systems units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'global-systems';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('Jarvis', 'system'),
      ('Nexus', 'system'),
      ('JarvisCore Identity', 'system'),
      ('Event Mesh', 'system'),
      ('Ghexit Telecom Layer', 'infrastructure')
    ) AS t(name, type)
  LOOP
    -- Check if company already exists
    SELECT id INTO v_company_id FROM public.jarvis_companies
    WHERE workspace_id = v_workspace_id AND name = v_unit_name;
    
    IF v_company_id IS NULL THEN
      INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
      VALUES (
        v_workspace_id,
        v_tenant_id,
        v_unit_name,
        NULL,
        jsonb_build_object('type', v_unit_type, 'workspace', 'global-systems')
      )
      RETURNING id INTO v_company_id;
      
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    ELSE
      RAISE NOTICE 'Company already exists: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Healthcare units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'healthcare';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('A. Agyeman MD Medical Corp', 'company'),
      ('Ohimaa Medical HI', 'company'),
      ('Ohimaa Medical GU', 'company'),
      ('MedRx LLC', 'company'),
      ('BookaDoc2u LLC', 'company'),
      ('AccessMD LLC', 'company'),
      ('DrAMD', 'company')
    ) AS t(name, type)
  LOOP
    INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_unit_name,
      NULL,
      jsonb_build_object('type', v_unit_type, 'workspace', 'healthcare', 'industry', 'healthcare')
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_company_id;
    
    IF v_company_id IS NOT NULL THEN
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Technology & SaaS units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'technology-saas';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('Ghexit LLC', 'company')
    ) AS t(name, type)
  LOOP
    INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_unit_name,
      NULL,
      jsonb_build_object('type', v_unit_type, 'workspace', 'technology-saas', 'industry', 'technology')
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_company_id;
    
    IF v_company_id IS NOT NULL THEN
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Creative & Retail units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'creative-retail';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('A3 Designs', 'company'),
      ('Unique Bijoux', 'company'),
      ('Needful Things', 'company'),
      ('Whiskers & Wanderlust', 'company'),
      ('Furfubu LLC', 'company')
    ) AS t(name, type)
  LOOP
    INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_unit_name,
      NULL,
      jsonb_build_object('type', v_unit_type, 'workspace', 'creative-retail', 'industry', 'retail')
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_company_id;
    
    IF v_company_id IS NOT NULL THEN
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Publishing & Media units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'publishing-media';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('Inkwell Publishing LLC', 'company'),
      ('IMHO Media LLC', 'company')
    ) AS t(name, type)
  LOOP
    INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_unit_name,
      NULL,
      jsonb_build_object('type', v_unit_type, 'workspace', 'publishing-media', 'industry', 'media')
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_company_id;
    
    IF v_company_id IS NOT NULL THEN
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Crypto & Gaming units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'crypto-gaming';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('Purrgressive Technologies', 'company'),
      ('Purrkoin LLC', 'company')
    ) AS t(name, type)
  LOOP
    INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_unit_name,
      NULL,
      jsonb_build_object('type', v_unit_type, 'workspace', 'crypto-gaming', 'industry', 'crypto')
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_company_id;
    
    IF v_company_id IS NOT NULL THEN
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Education units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'education';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('Scientia Vitae Academy', 'company'),
      ('TLS - The Learning Studio', 'company'),
      ('SVA Foundation', 'company')
    ) AS t(name, type)
  LOOP
    INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_unit_name,
      NULL,
      jsonb_build_object('type', v_unit_type, 'workspace', 'education', 'industry', 'education')
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_company_id;
    
    IF v_company_id IS NOT NULL THEN
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Engineering & Manufacturing units
  SELECT id INTO v_workspace_id FROM public.workspaces 
  WHERE tenant_id = v_tenant_id AND slug = 'engineering-manufacturing';
  
  FOR v_unit_name, v_unit_type IN
    SELECT * FROM (VALUES
      ('Inov8if LLC', 'company'),
      ('MedMaker LLC', 'company'),
      ('Symtech LLC', 'company'),
      ('KraftForge LLC', 'company')
    ) AS t(name, type)
  LOOP
    INSERT INTO public.jarvis_companies (workspace_id, tenant_id, name, domain, metadata)
    VALUES (
      v_workspace_id,
      v_tenant_id,
      v_unit_name,
      NULL,
      jsonb_build_object('type', v_unit_type, 'workspace', 'engineering-manufacturing', 'industry', 'engineering')
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_company_id;
    
    IF v_company_id IS NOT NULL THEN
      RAISE NOTICE 'Created company: % (%)', v_unit_name, v_company_id;
    END IF;
  END LOOP;

  -- Finance workspace has no units (empty array in registry)

  RAISE NOTICE 'Seeding complete! Created workspace units (companies).';

END $$;

