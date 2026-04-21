-- Seed 001: Agyeman Enterprises Tenant
-- Creates the root tenant for Agyeman Enterprises

DO $$
DECLARE
  v_tenant_id uuid;
BEGIN
  -- Insert or get Agyeman Enterprises tenant
  INSERT INTO public.tenants (name, slug, metadata)
  VALUES (
    'Agyeman Enterprises',
    'agyeman-enterprises',
    '{"description": "Root organizational container for Agyeman Enterprises portfolio"}'::jsonb
  )
  ON CONFLICT (slug) DO UPDATE
  SET name = EXCLUDED.name,
      metadata = EXCLUDED.metadata,
      updated_at = now()
  RETURNING id INTO v_tenant_id;

  -- Get tenant ID if it already existed
  IF v_tenant_id IS NULL THEN
    SELECT id INTO v_tenant_id FROM public.tenants WHERE slug = 'agyeman-enterprises';
  END IF;

  RAISE NOTICE 'Tenant ID: %', v_tenant_id;
  RAISE NOTICE 'Tenant: Agyeman Enterprises (%)', v_tenant_id;

END $$;

