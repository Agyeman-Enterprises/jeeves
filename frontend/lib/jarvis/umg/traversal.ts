import { supabaseServer } from "@/lib/supabase/server";
import type { GraphPath, RelatedNodes } from "./types";
import { findPath, getRelatedNodes as getRelatedNodesFromGraph } from "../cuil/graph";
import type { UniverseNode, UniverseEdge } from "../cuil/types";

export async function findGraphPath(
  userId: string,
  sourceNodeId: string,
  targetNodeId: string,
  maxDepth: number = 5,
  edgeTypes?: string[]
): Promise<GraphPath> {
  // Check cache first
  const cacheKey = `path:${sourceNodeId}:${targetNodeId}:${maxDepth}:${edgeTypes?.join(",") || ""}`;
  const cached = await getCachedQuery(userId, cacheKey);
  if (cached) {
    return cached.result as GraphPath;
  }

  // Find path using graph traversal
  const path = await findPath(userId, sourceNodeId, targetNodeId, maxDepth);

  // Build result
  const result: GraphPath = {
    path: path.map((e) => e.target_node_id),
    depth: path.length,
    found: path.length > 0,
    edges: path.map((e) => ({
      source: e.source_node_id,
      target: e.target_node_id,
      type: e.edge_type,
      weight: e.weight || 1.0,
    })),
  };

  // Cache result
  await cacheQuery(userId, cacheKey, "PATH_FINDING", result, 3600); // Cache for 1 hour

  return result;
}

export async function getRelatedNodes(
  userId: string,
  nodeId: string,
  edgeTypes?: string[],
  maxDepth: number = 1,
  limit: number = 50
): Promise<RelatedNodes> {
  // Check cache first
  const cacheKey = `related:${nodeId}:${maxDepth}:${edgeTypes?.join(",") || ""}:${limit}`;
  const cached = await getCachedQuery(userId, cacheKey);
  if (cached) {
    return cached.result as RelatedNodes;
  }

  // Get related nodes
  const nodes = await getRelatedNodesFromGraph(nodeId, undefined, maxDepth);

  // Filter by edge types if specified
  let filteredNodes = nodes;
  if (edgeTypes && edgeTypes.length > 0) {
    const edges = await getNodeEdges(nodeId, "both");
    const filteredNodeIds = new Set(
      edges.filter((e) => edgeTypes.includes(e.edge_type)).map((e) => 
        e.source_node_id === nodeId ? e.target_node_id : e.source_node_id
      )
    );
    filteredNodes = nodes.filter((n) => n.id && filteredNodeIds.has(n.id));
  }

  // Limit results
  const limitedNodes = filteredNodes.slice(0, limit);

  // Get edge information for each related node
  const edges = await getNodeEdges(nodeId, "both");
  const nodesWithEdges = limitedNodes.map((node) => {
    const edge = edges.find(
      (e) => e.source_node_id === node.id || e.target_node_id === node.id
    );
    return {
      node_id: node.id || "",
      edge_type: edge?.edge_type || "",
      weight: edge?.weight || 1.0,
    };
  });

  const result: RelatedNodes = {
    nodes: nodesWithEdges,
    total: filteredNodes.length,
  };

  // Cache result
  await cacheQuery(userId, cacheKey, "RELATIONSHIP_QUERY", result, 1800); // Cache for 30 minutes

  return result;
}

async function getNodeEdges(nodeId: string, direction: "outgoing" | "incoming" | "both"): Promise<UniverseEdge[]> {
  const { data } = await supabaseServer
    .from("jarvis_universe_edges")
    .select("*")
    .or(
      direction === "both"
        ? `source_node_id.eq.${nodeId},target_node_id.eq.${nodeId}`
        : direction === "outgoing"
        ? `source_node_id.eq.${nodeId}`
        : `target_node_id.eq.${nodeId}`
    );

  return (data || []) as UniverseEdge[];
}

async function getCachedQuery(
  userId: string,
  queryHash: string
): Promise<{ result: any; expires_at: string } | null> {
  const { data } = await supabaseServer
    .from("jarvis_umg_traversal_cache")
    .select("*")
    .eq("user_id", userId)
    .eq("query_hash", queryHash)
    .gt("expires_at", new Date().toISOString())
    .single();

  if (data) {
    return {
      result: (data as any).result,
      expires_at: (data as any).expires_at,
    };
  }

  return null;
}

async function cacheQuery(
  userId: string,
  queryHash: string,
  queryType: "PATH_FINDING" | "RELATIONSHIP_QUERY" | "SEMANTIC_SEARCH" | "TEMPORAL_QUERY",
  result: any,
  ttlSeconds: number
): Promise<void> {
  const expiresAt = new Date();
  expiresAt.setSeconds(expiresAt.getSeconds() + ttlSeconds);

  await supabaseServer
    .from("jarvis_umg_traversal_cache")
    .upsert({
      user_id: userId,
      query_hash: queryHash,
      query_type: queryType,
      result,
      expires_at: expiresAt.toISOString(),
    } as any, {
      onConflict: "user_id,query_hash",
    });
}

export async function queryGraph(
  userId: string,
  queryPattern: Record<string, any>,
  queryType: "RELATIONSHIP" | "PATH" | "SEMANTIC" | "TEMPORAL" | "AGGREGATE"
): Promise<any> {
  // This is a placeholder for complex graph queries
  // In production, this would parse the query pattern and execute appropriate graph operations

  switch (queryType) {
    case "RELATIONSHIP":
      // Find nodes with specific relationships
      return await queryRelationships(userId, queryPattern);
    case "PATH":
      // Find paths between nodes
      return await queryPaths(userId, queryPattern);
    case "SEMANTIC":
      // Semantic search
      return await querySemantic(userId, queryPattern);
    case "TEMPORAL":
      // Temporal queries
      return await queryTemporal(userId, queryPattern);
    case "AGGREGATE":
      // Aggregate queries
      return await queryAggregate(userId, queryPattern);
    default:
      throw new Error(`Unknown query type: ${queryType}`);
  }
}

async function queryRelationships(userId: string, pattern: Record<string, any>): Promise<any> {
  // Placeholder - would implement relationship query logic
  return { results: [] };
}

async function queryPaths(userId: string, pattern: Record<string, any>): Promise<any> {
  // Placeholder - would implement path query logic
  return { paths: [] };
}

async function querySemantic(userId: string, pattern: Record<string, any>): Promise<any> {
  // Placeholder - would implement semantic query logic
  return { results: [] };
}

async function queryTemporal(userId: string, pattern: Record<string, any>): Promise<any> {
  // Placeholder - would implement temporal query logic
  return { results: [] };
}

async function queryAggregate(userId: string, pattern: Record<string, any>): Promise<any> {
  // Placeholder - would implement aggregate query logic
  return { aggregates: {} };
}

