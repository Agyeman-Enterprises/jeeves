/**
 * Supabase Admin Client (Service Role)
 * USE THIS ONLY for admin operations that bypass RLS
 * NEVER expose this client to the browser
 * 
 * @example
 * import { createAdminClient } from '@/auth-template/lib/supabase/admin';
 * const supabase = createAdminClient();
 * // This bypasses Row Level Security
 * const { data } = await supabase.from('users').select();
 */

import { createClient } from '@supabase/supabase-js';

export function createAdminClient() {
  const supabaseUrl = process.env['NEXT_PUBLIC_SUPABASE_URL'];
  const supabaseServiceKey = process.env['SUPABASE_SERVICE_ROLE_KEY'];

  if (!supabaseUrl || !supabaseServiceKey) {
    throw new Error(
      'Missing Supabase admin environment variables. ' +
      'Ensure NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set.'
    );
  }

  return createClient(supabaseUrl, supabaseServiceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
