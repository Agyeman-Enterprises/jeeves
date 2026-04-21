// JJ Supabase server client — always points at tzjygaxpzrtevlnganjs (JJ's Cloud DB)
// NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY set via Coolify env vars.
import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _supabaseServer: SupabaseClient<any> | null = null;

function getSupabaseServer() {
  if (_supabaseServer) {
    return _supabaseServer;
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !serviceRoleKey) {
    // During build, env vars might not be available - create a placeholder client
    // This will fail at runtime if env vars are still missing, which is expected
    _supabaseServer = createClient<any>(
      supabaseUrl || "https://placeholder.supabase.co",
      serviceRoleKey || "placeholder-key",
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false,
        },
      }
    );
    return _supabaseServer;
  }

  // NOTE: service role should only be used server-side
  _supabaseServer = createClient<any>(supabaseUrl, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });

  return _supabaseServer;
}

// Export as a getter to ensure lazy initialization
export const supabaseServer = getSupabaseServer();

