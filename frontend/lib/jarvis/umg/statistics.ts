import { supabaseServer } from "@/lib/supabase/server";
import type { UMGStatistics } from "./types";

export async function generateGraphStatistics(
  userId: string,
  snapshotDate?: string
): Promise<UMGStatistics> {
  const date = snapshotDate ? new Date(snapshotDate) : new Date();
  const dateStr = date.toISOString().split("T")[0];

  // Get all nodes
  const { data: nodes } = await supabaseServer
    .from("jarvis_universe_nodes")
    .select("id, node_type, domain")
    .eq("user_id", userId);

  // Get all edges
  const { data: edges } = await supabaseServer
    .from("jarvis_universe_edges")
    .select("id, edge_type, source_node_id, target_node_id")
    .in(
      "source_node_id",
      (nodes || []).map((n: any) => n.id)
    );

  const totalNodes = (nodes || []).length;
  const totalEdges = (edges || []).length;

  // Count nodes by category (using node_type as proxy)
  const nodesByCategory: Record<string, number> = {};
  (nodes || []).forEach((n: any) => {
    const category = mapNodeTypeToCategory(n.node_type);
    nodesByCategory[category] = (nodesByCategory[category] || 0) + 1;
  });

  // Count nodes by domain
  const nodesByDomain: Record<string, number> = {};
  (nodes || []).forEach((n: any) => {
    nodesByDomain[n.domain] = (nodesByDomain[n.domain] || 0) + 1;
  });

  // Count edges by type
  const edgesByType: Record<string, number> = {};
  (edges || []).forEach((e: any) => {
    edgesByType[e.edge_type] = (edgesByType[e.edge_type] || 0) + 1;
  });

  // Calculate average node degree
  const nodeDegrees: Record<string, number> = {};
  (edges || []).forEach((e: any) => {
    nodeDegrees[e.source_node_id] = (nodeDegrees[e.source_node_id] || 0) + 1;
    nodeDegrees[e.target_node_id] = (nodeDegrees[e.target_node_id] || 0) + 1;
  });
  const averageNodeDegree =
    Object.keys(nodeDegrees).length > 0
      ? Object.values(nodeDegrees).reduce((a, b) => a + b, 0) / Object.keys(nodeDegrees).length
      : 0;

  // Calculate graph density (simplified)
  const maxPossibleEdges = totalNodes * (totalNodes - 1);
  const graphDensity = maxPossibleEdges > 0 ? totalEdges / maxPossibleEdges : 0;

  // Get temporal coverage
  const { data: nodeTimestamps } = await supabaseServer
    .from("jarvis_universe_nodes")
    .select("created_at")
    .eq("user_id", userId)
    .order("created_at", { ascending: true })
    .limit(1);

  const { data: latestNode } = await supabaseServer
    .from("jarvis_universe_nodes")
    .select("created_at")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1);

  const earliestTimestamp = (nodeTimestamps || []).length > 0 ? (nodeTimestamps as any[])[0]?.created_at : null;
  const latestTimestamp = (latestNode || []).length > 0 ? (latestNode as any[])[0]?.created_at : null;
  const temporalCoverage = {
    earliest: earliestTimestamp || null,
    latest: latestTimestamp || null,
  };

  const statistics: UMGStatistics = {
    user_id: userId,
    snapshot_date: dateStr,
    total_nodes: totalNodes,
    total_edges: totalEdges,
    nodes_by_category: nodesByCategory,
    nodes_by_domain: nodesByDomain,
    edges_by_type: edgesByType,
    average_node_degree: averageNodeDegree,
    largest_connected_component: totalNodes, // Simplified - would calculate actual components
    graph_density: graphDensity,
    temporal_coverage: temporalCoverage,
  };

  // Store statistics
  await storeGraphStatistics(userId, statistics);

  return statistics;
}

function mapNodeTypeToCategory(nodeType: string): string {
  // Map node types to categories
  if (["PATIENT", "STUDENT", "STAFF"].includes(nodeType)) return "PERSON";
  if (["ENTITY", "BUSINESS_UNIT"].includes(nodeType)) return "ENTITY";
  if (["DOCUMENT", "FILE", "PRODUCT", "ASSET"].includes(nodeType)) return "OBJECT";
  if (["PROJECT", "WORKFLOW", "PLAN"].includes(nodeType)) return "TASK_PLAN";
  if (nodeType.includes("EVENT")) return "EVENT";
  return "CONCEPT";
}

async function storeGraphStatistics(userId: string, stats: UMGStatistics): Promise<void> {
  await supabaseServer
    .from("jarvis_umg_statistics")
    .upsert({
      ...stats,
    } as any, {
      onConflict: "user_id,snapshot_date",
    });
}

export async function getGraphStatistics(
  userId: string,
  snapshotDate?: string
): Promise<UMGStatistics | null> {
  const date = snapshotDate ? new Date(snapshotDate) : new Date();
  const dateStr = date.toISOString().split("T")[0];

  const { data } = await supabaseServer
    .from("jarvis_umg_statistics")
    .select("*")
    .eq("user_id", userId)
    .eq("snapshot_date", dateStr)
    .single();

  if (data) {
    return data as UMGStatistics;
  }

  return null;
}

