export type ForesightHorizon = "TACTICAL_10DAY" | "OPERATIONAL_30DAY" | "STRATEGIC_90DAY" | "ENTERPRISE_1YEAR";
export type ForesightStatus = "GENERATING" | "COMPLETED" | "STALE" | "ARCHIVED";
export type ScenarioType = "BASELINE" | "OPTIMISTIC" | "PESSIMISTIC" | "INTERVENTION";
export type InterventionType = "PREVENTIVE" | "OPPORTUNISTIC" | "MITIGATION" | "ACCELERATION";

export interface ForesightMap {
  id?: string;
  user_id: string;
  horizon: ForesightHorizon;
  forecast_start_date: string; // ISO date string
  forecast_end_date: string; // ISO date string
  generated_at?: string;
  status?: ForesightStatus;
  foresight_data: Record<string, any>;
  risks?: Record<string, any>;
  opportunities?: Record<string, any>;
  bottlenecks?: Record<string, any>;
  recommended_actions?: Record<string, any>;
  cross_universe_insights?: Record<string, any>;
  confidence_score?: number; // 0-1
  factors_used?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface ForesightScenario {
  id?: string;
  user_id: string;
  foresight_map_id?: string;
  scenario_name: string;
  scenario_type: ScenarioType;
  scenario_description?: string;
  scenario_data: Record<string, any>;
  probability?: number; // 0-1
  impact_score?: number; // -1 to 1
  created_at?: string;
}

export interface ForesightAlert {
  id?: string;
  user_id: string;
  foresight_map_id?: string;
  alert_type: "RISK" | "OPPORTUNITY" | "BOTTLENECK" | "DEADLINE" | "RESOURCE";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  title: string;
  description: string;
  predicted_date?: string;
  affected_domains?: string[];
  recommended_action?: Record<string, any>;
  status?: "ACTIVE" | "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED";
  acknowledged_at?: string;
  resolved_at?: string;
  created_at?: string;
}

export interface ForesightTracking {
  id?: string;
  user_id: string;
  foresight_map_id?: string;
  prediction_id?: string;
  prediction_type: string;
  predicted_value: Record<string, any>;
  actual_value?: Record<string, any>;
  predicted_date: string;
  actual_date?: string;
  accuracy_score?: number; // 0-1
  variance?: number;
  factors_that_changed?: Record<string, any>;
  learned_insights?: string;
  created_at?: string;
  actual_recorded_at?: string;
}

export interface ForesightIntervention {
  id?: string;
  user_id: string;
  foresight_map_id?: string;
  intervention_type: InterventionType;
  intervention_description: string;
  target_domain?: string;
  target_date?: string;
  intervention_actions?: Record<string, any>;
  expected_outcome?: Record<string, any>;
  actual_outcome?: Record<string, any>;
  status?: "PLANNED" | "EXECUTING" | "COMPLETED" | "CANCELLED";
  executed_at?: string;
  completed_at?: string;
  created_at?: string;
}

