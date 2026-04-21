// Nexus financial transactions repository (read-only)
import { createNexusDb } from "@/lib/db/nexus";
import type { Database } from "@/lib/supabase/types";

type TxRow = Database["public"]["Tables"]["nexus_financial_transactions"]["Row"];

export async function listTransactionsForEntity(input: {
  userId: string;
  workspaceId: string;
  entityId: string;
  limit?: number;
}): Promise<TxRow[]> {
  const db = createNexusDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;
  const { userId, workspaceId, entityId, limit = 100 } = input;

  const { data, error } = await client
    .from("nexus_financial_transactions")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId)
    .eq("entity_id" as any, entityId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return (data || []) as TxRow[];
}

export async function listRecentTransactions(input: {
  userId: string;
  workspaceId: string;
  limit?: number;
}): Promise<TxRow[]> {
  const db = createNexusDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;
  const { userId, workspaceId, limit = 100 } = input;

  const { data, error } = await client
    .from("nexus_financial_transactions")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return (data || []) as TxRow[];
}

