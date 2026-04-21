export type SituationRoomType = "CLINIC" | "FINANCIAL" | "BUSINESS_OPS" | "LIFE";
export type AlertType = "RISK" | "OPPORTUNITY" | "ANOMALY" | "BOTTLENECK" | "OVERLOAD" | "CRISIS";
export type AlertSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type RecommendationType = "ACTION" | "OPTIMIZATION" | "PREVENTION" | "OPPORTUNITY";

export interface SituationRoomSnapshot {
  id?: string;
  user_id: string;
  room_type: SituationRoomType;
  snapshot_data: Record<string, any>;
  alerts?: Record<string, any>;
  recommendations?: Record<string, any>;
  anomalies?: Record<string, any>;
  agent_status?: Record<string, any>;
  last_updated?: string;
  created_at?: string;
}

export interface SituationRoomAlert {
  id?: string;
  user_id: string;
  room_type: SituationRoomType;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  context?: Record<string, any>;
  recommended_actions?: Record<string, any>;
  status?: "ACTIVE" | "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED";
  acknowledged_at?: string;
  resolved_at?: string;
  created_at?: string;
}

export interface SituationRoomRecommendation {
  id?: string;
  user_id: string;
  room_type: SituationRoomType;
  recommendation_type: RecommendationType;
  title: string;
  description: string;
  priority?: number;
  impact_estimate?: Record<string, any>;
  implementation_steps?: Record<string, any>;
  status?: "PENDING" | "ACCEPTED" | "REJECTED" | "IMPLEMENTED";
  accepted_at?: string;
  implemented_at?: string;
  created_at?: string;
}

export interface SituationRoomMetric {
  id?: string;
  user_id: string;
  room_type: SituationRoomType;
  metric_name: string;
  metric_value?: number;
  metric_unit?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
  created_at?: string;
}

