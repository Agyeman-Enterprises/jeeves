// Nexus financial snapshots and tax positions repository (read-only)
import { createNexusDb } from "@/lib/db/nexus";
import type { Database } from "@/lib/supabase/types";

type SnapshotRow = Database["public"]["Tables"]["nexus_financial_snapshots"]["Row"];
type TaxRow = Database["public"]["Tables"]["nexus_tax_positions"]["Row"];

export async function listSnapshotsForEntity(input: {
  userId: string;
  workspaceId: string;
  entityId: string;
  limit?: number;
}): Promise<SnapshotRow[]> {
  const db = createNexusDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;
  const { userId, workspaceId, entityId, limit = 30 } = input;

  const { data, error } = await client
    .from("nexus_financial_snapshots")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId)
    .eq("entity_id" as any, entityId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return (data || []) as SnapshotRow[];
}

export async function listTaxPositions(input: {
  userId: string;
  workspaceId: string;
  entityId?: string;
}): Promise<TaxRow[]> {
  const db = createNexusDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;
  const { userId, workspaceId, entityId } = input;

  let query = client
    .from("nexus_tax_positions")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId);

  if (entityId) {
    query = query.eq("entity_id" as any, entityId);
  }

  const { data, error } = await query;
  if (error) throw error;
  return (data || []) as TaxRow[];
}

