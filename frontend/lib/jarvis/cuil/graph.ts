import { supabaseServer } from "@/lib/supabase/server";
import type { UniverseNode, UniverseEdge, UniverseNodeType, UniverseDomain, EdgeType } from "./types";

export async function createNode(node: Omit<UniverseNode, "id" | "created_at" | "updated_at">): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_universe_nodes")
    .upsert({
      ...node,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "user_id,source_system,external_id",
    })
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create node: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getNode(
  userId: string,
  sourceSystem: string,
  externalId: string
): Promise<UniverseNode | null> {
  const { data } = await supabaseServer
    .from("jarvis_universe_nodes")
    .select("*")
    .eq("user_id", userId)
    .eq("source_system", sourceSystem)
    .eq("external_id", externalId)
    .single();

  if (data) {
    return data as UniverseNode;
  }

  return null;
}

export async function getNodesByDomain(
  userId: string,
  domain: UniverseDomain,
  nodeType?: UniverseNodeType
): Promise<UniverseNode[]> {
  let query = supabaseServer
    .from("jarvis_universe_nodes")
    .select("*")
    .eq("user_id", userId)
    .eq("domain", domain);

  if (nodeType) {
    query = query.eq("node_type", nodeType);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get nodes: ${error.message}`);
  }

  return (data || []) as UniverseNode[];
}

export async function createEdge(edge: Omit<UniverseEdge, "id" | "created_at" | "updated_at">): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_universe_edges")
    .upsert({
      ...edge,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "source_node_id,target_node_id,edge_type",
    })
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create edge: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getNodeEdges(
  nodeId: string,
  direction: "outgoing" | "incoming" | "both" = "both"
): Promise<UniverseEdge[]> {
  let query = supabaseServer.from("jarvis_universe_edges").select("*");

  if (direction === "outgoing" || direction === "both") {
    query = query.or(`source_node_id.eq.${nodeId}${direction === "both" ? ",target_node_id.eq." + nodeId : ""}`);
  } else {
    query = query.eq("target_node_id", nodeId);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get edges: ${error.message}`);
  }

  return (data || []) as UniverseEdge[];
}

export async function findPath(
  userId: string,
  sourceNodeId: string,
  targetNodeId: string,
  maxDepth: number = 5
): Promise<UniverseEdge[]> {
  // Simplified path finding - in production, this would use a proper graph algorithm
  // For now, we'll do a breadth-first search up to maxDepth
  const visited = new Set<string>();
  const queue: Array<{ nodeId: string; path: UniverseEdge[] }> = [{ nodeId: sourceNodeId, path: [] }];

  while (queue.length > 0 && queue[0].path.length < maxDepth) {
    const { nodeId, path } = queue.shift()!;

    if (nodeId === targetNodeId) {
      return path;
    }

    if (visited.has(nodeId)) {
      continue;
    }
    visited.add(nodeId);

    // Get outgoing edges
    const edges = await getNodeEdges(nodeId, "outgoing");
    for (const edge of edges) {
      if (!visited.has(edge.target_node_id)) {
        queue.push({ nodeId: edge.target_node_id, path: [...path, edge] });
      }
    }
  }

  return []; // No path found
}

export async function getRelatedNodes(
  nodeId: string,
  edgeTypes?: EdgeType[],
  maxDepth: number = 2
): Promise<UniverseNode[]> {
  const relatedNodeIds = new Set<string>();
  const visited = new Set<string>();
  const queue: Array<{ nodeId: string; depth: number }> = [{ nodeId, depth: 0 }];

  while (queue.length > 0) {
    const { nodeId: currentId, depth } = queue.shift()!;

    if (depth >= maxDepth || visited.has(currentId)) {
      continue;
    }
    visited.add(currentId);

    const edges = await getNodeEdges(currentId, "both");
    for (const edge of edges) {
      if (edgeTypes && !edgeTypes.includes(edge.edge_type)) {
        continue;
      }

      const relatedId = edge.source_node_id === currentId ? edge.target_node_id : edge.source_node_id;
      if (!visited.has(relatedId)) {
        relatedNodeIds.add(relatedId);
        queue.push({ nodeId: relatedId, depth: depth + 1 });
      }
    }
  }

  // Fetch node details
  const { data } = await supabaseServer
    .from("jarvis_universe_nodes")
    .select("*")
    .in("id", Array.from(relatedNodeIds));

  return (data || []) as UniverseNode[];
}

