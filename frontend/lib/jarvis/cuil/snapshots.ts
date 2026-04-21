import { supabaseServer } from "@/lib/supabase/server";
import type { UniverseSnapshot, UniverseDomain } from "./types";
import { getNodesByDomain } from "./graph";

export async function createUniverseSnapshot(
  userId: string,
  snapshotType: UniverseSnapshot["snapshot_type"] = "DAILY"
): Promise<string> {
  // Get all nodes and edges
  const { data: nodes } = await supabaseServer
    .from("jarvis_universe_nodes")
    .select("id, domain, node_type")
    .eq("user_id", userId);

  const { data: edges } = await supabaseServer
    .from("jarvis_universe_edges")
    .select("id")
    .in(
      "source_node_id",
      (nodes || []).map((n: any) => n.id)
    );

  // Get active domains
  const activeDomains = [
    ...new Set((nodes || []).map((n: any) => n.domain)),
  ] as UniverseDomain[];

  // Calculate key metrics
  const keyMetrics: Record<string, any> = {};
  for (const domain of activeDomains) {
    const domainNodes = (nodes || []).filter((n: any) => n.domain === domain);
    keyMetrics[domain] = {
      node_count: domainNodes.length,
      node_types: domainNodes.reduce((acc: Record<string, number>, n: any) => {
        acc[n.node_type] = (acc[n.node_type] || 0) + 1;
        return acc;
      }, {}),
    };
  }

  // Create snapshot
  const { data, error } = await supabaseServer
    .from("jarvis_universe_snapshots")
    .insert({
      user_id: userId,
      snapshot_type: snapshotType,
      snapshot_data: {
        nodes: nodes || [],
        edges: edges || [],
        timestamp: new Date().toISOString(),
      },
      node_count: (nodes || []).length,
      edge_count: (edges || []).length,
      active_domains: activeDomains,
      key_metrics: keyMetrics,
      anomalies: {}, // Would be populated by anomaly detection
      opportunities: {}, // Would be populated by opportunity detection
      risks: {}, // Would be populated by risk analysis
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create universe snapshot: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getLatestSnapshot(
  userId: string,
  snapshotType?: UniverseSnapshot["snapshot_type"]
): Promise<UniverseSnapshot | null> {
  let query = supabaseServer
    .from("jarvis_universe_snapshots")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1);

  if (snapshotType) {
    query = query.eq("snapshot_type", snapshotType);
  }

  const { data } = await query.single();

  if (data) {
    return data as UniverseSnapshot;
  }

  return null;
}

export async function getSnapshotHistory(
  userId: string,
  snapshotType?: UniverseSnapshot["snapshot_type"],
  limit: number = 30
): Promise<UniverseSnapshot[]> {
  let query = supabaseServer
    .from("jarvis_universe_snapshots")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (snapshotType) {
    query = query.eq("snapshot_type", snapshotType);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get snapshot history: ${error.message}`);
  }

  return (data || []) as UniverseSnapshot[];
}

