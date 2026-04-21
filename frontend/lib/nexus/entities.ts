// Nexus financial entities repository (read-only)
import { createNexusDb } from "@/lib/db/nexus";
import type { Database } from "@/lib/supabase/types";

type EntityRow = Database["public"]["Tables"]["nexus_financial_entities"]["Row"];

export async function listFinancialEntities(input: {
  userId: string;
  workspaceId: string;
}): Promise<EntityRow[]> {
  const db = createNexusDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;

  const { data, error } = await client
    .from("nexus_financial_entities")
    .select("*")
    .eq("user_id", input.userId)
    .eq("workspace_id", input.workspaceId)
    .order("created_at", { ascending: true });

  if (error) throw error;
  return (data || []) as EntityRow[];
}

export async function getFinancialEntityById(input: {
  userId: string;
  workspaceId: string;
  id: string;
}): Promise<EntityRow | null> {
  const db = createNexusDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;

  const { data, error } = await client
    .from("nexus_financial_entities")
    .select("*")
    .eq("user_id", input.userId)
    .eq("workspace_id", input.workspaceId)
    .eq("id", input.id)
    .maybeSingle();

  if (error) throw error;
  return (data as EntityRow) || null;
}

