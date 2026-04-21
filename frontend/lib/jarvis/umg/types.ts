export type UMGNodeCategory = "PERSON" | "ENTITY" | "OBJECT" | "CONCEPT" | "EVENT" | "TASK_PLAN";
export type UMGEdgeRelationship =
  | "DEPENDS_ON"
  | "CAUSED_BY"
  | "PART_OF"
  | "OWNED_BY"
  | "RELATED_TO"
  | "PARENT_OF"
  | "SUBTASK_OF"
  | "AFFECTED_BY"
  | "FOLLOWS_FROM"
  | "BELONGS_TO_UNIVERSE"
  | "PRODUCED_BY_AGENT"
  | "ASSIGNED_TO"
  | "CORRELATES_WITH"
  | "INFLUENCES"
  | "TRIGGERS"
  | "BLOCKS"
  | "ENABLES"
  | "PRECEDES"
  | "SUCCEEDS"
  | "CONTAINS"
  | "REFERENCES"
  | "SIMILAR_TO"
  | "OPPOSITE_OF"
  | "VERSION_OF"
  | "DERIVED_FROM";

export type QueryType = "RELATIONSHIP" | "PATH" | "SEMANTIC" | "TEMPORAL" | "AGGREGATE";

export interface UMGEmbedding {
  id?: string;
  user_id: string;
  node_id: string;
  embedding_model: string;
  embedding?: number[]; // Vector embedding
  text_content?: string;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface UMGEventMap {
  id?: string;
  user_id: string;
  event_id: string;
  source_node_id?: string;
  affected_node_ids?: string[];
  created_edges?: string[];
  graph_impact?: Record<string, any>;
  created_at?: string;
}

export interface UMGTraversalCache {
  id?: string;
  user_id: string;
  query_hash: string;
  query_type: "PATH_FINDING" | "RELATIONSHIP_QUERY" | "SEMANTIC_SEARCH" | "TEMPORAL_QUERY";
  result: Record<string, any>;
  expires_at: string;
  created_at?: string;
}

export interface UMGStatistics {
  id?: string;
  user_id: string;
  snapshot_date: string;
  total_nodes: number;
  total_edges: number;
  nodes_by_category?: Record<string, number>;
  nodes_by_domain?: Record<string, number>;
  edges_by_type?: Record<string, number>;
  average_node_degree?: number;
  largest_connected_component?: number;
  graph_density?: number;
  temporal_coverage?: Record<string, any>;
  created_at?: string;
}

export interface UMGQuery {
  id?: string;
  user_id: string;
  query_name: string;
  query_description?: string;
  query_pattern: Record<string, any>;
  query_type: QueryType;
  is_saved?: boolean;
  execution_count?: number;
  last_executed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface GraphPath {
  path: string[];
  depth: number;
  found: boolean;
  edges?: Array<{ source: string; target: string; type: string; weight: number }>;
}

export interface RelatedNodes {
  nodes: Array<{
    node_id: string;
    edge_type: string;
    weight: number;
  }>;
  total: number;
}

