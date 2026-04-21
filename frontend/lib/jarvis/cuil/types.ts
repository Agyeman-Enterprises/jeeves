export type UniverseNodeType =
  | "PATIENT"
  | "STUDENT"
  | "CUSTOMER"
  | "ENTITY"
  | "PROJECT"
  | "PRODUCT"
  | "CHARACTER"
  | "AGENT"
  | "STAFF"
  | "AI_SYSTEM"
  | "ASSET"
  | "EVENT"
  | "DOCUMENT"
  | "LESSON"
  | "COURSE"
  | "TOKEN"
  | "PROTOTYPE"
  | "WORKFLOW"
  | "BUSINESS_UNIT";

export type UniverseDomain =
  | "CLINICAL"
  | "FINANCIAL"
  | "EDUCATION"
  | "MEDIA"
  | "CRYPTO"
  | "GAMING"
  | "ENGINEERING"
  | "MANUFACTURING"
  | "OPERATIONS"
  | "PERSONAL";

export type EdgeType =
  | "OWNS"
  | "DEPENDS_ON"
  | "INFLUENCES"
  | "INTERACTS_WITH"
  | "BELONGS_TO"
  | "TRIGGERS"
  | "BLOCKS"
  | "ENABLES";

export interface UniverseNode {
  id?: string;
  user_id: string;
  node_type: UniverseNodeType;
  domain: UniverseDomain;
  external_id?: string;
  source_system: string;
  label: string;
  description?: string;
  metadata?: Record<string, any>;
  properties?: Record<string, any>;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface UniverseEdge {
  id?: string;
  user_id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type: EdgeType;
  weight?: number;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface CrossUniverseEvent {
  id?: string;
  user_id: string;
  event_type: string;
  source_domain: UniverseDomain;
  target_domains: UniverseDomain[];
  source_node_id?: string;
  affected_node_ids?: string[];
  payload: Record<string, any>;
  impact_analysis?: Record<string, any>;
  routing_decision?: Record<string, any>;
  status?: "PENDING" | "ROUTED" | "PROCESSED" | "FAILED";
  processed_at?: string;
  created_at?: string;
}

export interface CrossPrediction {
  id?: string;
  user_id: string;
  prediction_type: "CROSS_DOMAIN_FORECAST" | "INTERDEPENDENCY_ANALYSIS" | "CASCADE_RISK" | "OPPORTUNITY_DETECTION";
  source_domain: UniverseDomain;
  target_domains: UniverseDomain[];
  prediction_value: Record<string, any>;
  confidence_score?: number;
  factors_used?: Record<string, any>;
  interdependency_map?: Record<string, any>;
  created_at?: string;
  expires_at?: string;
}

export interface CrossRecommendation {
  id?: string;
  user_id: string;
  recommendation_type: "RESOURCE_REALLOCATION" | "SCHEDULE_OPTIMIZATION" | "RISK_MITIGATION" | "OPPORTUNITY_PURSUIT" | "WORKLOAD_BALANCE";
  affected_domains: UniverseDomain[];
  affected_node_ids?: string[];
  recommendation_summary: string;
  recommendation_details?: Record<string, any>;
  interdependency_reasoning?: Record<string, any>;
  priority?: number;
  impact_estimate?: Record<string, any>;
  status?: "PENDING" | "ACCEPTED" | "REJECTED" | "IMPLEMENTED";
  accepted_at?: string;
  implemented_at?: string;
  created_at?: string;
}

export interface UniverseSnapshot {
  id?: string;
  user_id: string;
  snapshot_type: "DAILY" | "WEEKLY" | "MONTHLY" | "ON_DEMAND";
  snapshot_data: Record<string, any>;
  node_count?: number;
  edge_count?: number;
  active_domains?: UniverseDomain[];
  key_metrics?: Record<string, any>;
  anomalies?: Record<string, any>;
  opportunities?: Record<string, any>;
  risks?: Record<string, any>;
  created_at?: string;
}

export interface CrossAgentCoordination {
  id?: string;
  user_id: string;
  coordination_type: "SEQUENTIAL" | "PARALLEL" | "DEPENDENT" | "ORCHESTRATED";
  source_agent_slug: string;
  target_agent_slug: string;
  source_domain: UniverseDomain;
  target_domain: UniverseDomain;
  coordination_context?: Record<string, any>;
  status?: "PENDING" | "ACTIVE" | "COMPLETED" | "FAILED";
  result?: Record<string, any>;
  created_at?: string;
  completed_at?: string;
}

