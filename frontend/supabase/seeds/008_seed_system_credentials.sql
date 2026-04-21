-- Seed 008: System Credentials (Placeholder)
-- Creates placeholder credentials for global systems
-- NOTE: These are placeholders only - no real keys are stored

DO $$
DECLARE
  jarvis_id uuid;
  nexus_id uuid;
  ghexit_id uuid;
BEGIN
  -- Get system IDs
  SELECT id INTO jarvis_id FROM public.jarvis_global_systems WHERE slug = 'jarvis';
  SELECT id INTO nexus_id FROM public.jarvis_global_systems WHERE slug = 'nexus';
  SELECT id INTO ghexit_id FROM public.jarvis_global_systems WHERE slug = 'ghexit_telecom';

  -- Verify systems exist
  IF jarvis_id IS NULL THEN
    RAISE EXCEPTION 'Jarvis global system not found. Please run 007_seed_global_systems.sql first.';
  END IF;

  IF nexus_id IS NULL THEN
    RAISE EXCEPTION 'Nexus global system not found. Please run 007_seed_global_systems.sql first.';
  END IF;

  IF ghexit_id IS NULL THEN
    RAISE EXCEPTION 'Ghexit Telecom global system not found. Please run 007_seed_global_systems.sql first.';
  END IF;

  -- Insert placeholder credentials
  INSERT INTO public.jarvis_system_credentials (system_id, credential_type, credential_hash, scopes, metadata)
  VALUES 
    (
      jarvis_id,
      'api_key',
      'pending-integration',
      '["admin"]'::jsonb,
      jsonb_build_object('note', 'Placeholder credential - real integration pending', 'status', 'not_configured')
    ),
    (
      nexus_id,
      'api_key',
      'pending-integration',
      '["admin"]'::jsonb,
      jsonb_build_object('note', 'Placeholder credential - real integration pending', 'status', 'not_configured')
    ),
    (
      ghexit_id,
      'api_key',
      'pending-integration',
      '["admin"]'::jsonb,
      jsonb_build_object('note', 'Placeholder credential - real integration pending', 'status', 'not_configured')
    )
  ON CONFLICT (system_id, credential_type) DO UPDATE
  SET credential_hash = EXCLUDED.credential_hash,
      scopes = EXCLUDED.scopes,
      metadata = EXCLUDED.metadata,
      updated_at = now();

  -- Update global systems to indicate not configured
  UPDATE public.jarvis_global_systems
  SET connection_status = 'not_configured',
      updated_at = now()
  WHERE slug IN ('jarvis', 'nexus', 'ghexit_telecom');

  RAISE NOTICE 'Placeholder system credentials seeded.';
  RAISE NOTICE 'Jarvis credential: %', jarvis_id;
  RAISE NOTICE 'Nexus credential: %', nexus_id;
  RAISE NOTICE 'Ghexit Telecom credential: %', ghexit_id;
  RAISE NOTICE 'All systems marked as not_configured.';

END $$;

