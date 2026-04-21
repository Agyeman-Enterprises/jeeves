export type DecisionType = "ACTION" | "RECOMMENDATION" | "ROUTING" | "AUTONOMY" | "SCHEDULING";
export type UserFeedback = "ACCEPTED" | "EDITED" | "REJECTED" | "OVERRIDDEN" | "IGNORED";
export type PatternType = "TONE" | "VERBOSITY" | "TIMING" | "AUTONOMY" | "DETAIL_LEVEL" | "ACTION_TYPE";
export type TrustLevel = "LOW" | "MEDIUM" | "HIGH";
export type AutonomyAdjustment = "INCREASED" | "DECREASED" | "UNCHANGED";
export type ForecastType = "CLINIC_LOAD" | "FINANCIAL" | "BURNOUT_RISK" | "GLP_OUTCOMES" | "OPS_BOTTLENECK";
export type InsightType = "DECISION" | "PREFERENCE" | "AGENT" | "FORECAST" | "NOTIFICATION";
export type LearningDomain = "DECISIONS" | "PREFERENCES" | "AGENTS" | "FORECASTS" | "NOTIFICATIONS";
export type SuppressionLevel = "NONE" | "LOW" | "MEDIUM" | "HIGH" | "SUPPRESSED";

export interface DecisionOutcome {
  id?: string;
  user_id: string;
  decision_id?: string;
  decision_type: DecisionType;
  decision_context: Record<string, any>;
  predicted_outcome?: Record<string, any>;
  actual_outcome?: Record<string, any>;
  user_feedback?: UserFeedback;
  outcome_score?: number; // -1 to 1
  downstream_impact?: Record<string, any>;
  learned_insight?: string;
  created_at?: string;
  outcome_recorded_at?: string;
}

export interface PreferenceLearning {
  id?: string;
  user_id: string;
  pattern_type: PatternType;
  pattern_value: string;
  context?: Record<string, any>;
  acceptance_count?: number;
  edit_count?: number;
  rewrite_count?: number;
  rejection_count?: number;
  confidence_score?: number; // 0 to 1
  last_used_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AgentPerformance {
  id?: string;
  user_id: string;
  agent_slug: string;
  performance_period_start: string;
  performance_period_end: string;
  total_tasks?: number;
  successful_tasks?: number;
  failed_tasks?: number;
  average_retries?: number;
  average_completion_time_seconds?: number;
  error_types?: Record<string, number>;
  intervention_count?: number;
  success_rate?: number;
  performance_score?: number; // -1 to 1
  trust_level?: TrustLevel;
  autonomy_adjustment?: AutonomyAdjustment;
  notes?: string;
  created_at?: string;
}

export interface ForecastAccuracy {
  id?: string;
  user_id: string;
  forecast_type: ForecastType;
  forecast_id?: string;
  forecast_value: Record<string, any>;
  actual_value?: Record<string, any>;
  forecast_horizon?: string;
  error_margin?: number;
  error_percentage?: number;
  accuracy_score?: number; // 0 to 1
  factors_used?: Record<string, any>;
  learned_adjustments?: Record<string, any>;
  created_at?: string;
  actual_recorded_at?: string;
}

export interface NotificationEffectiveness {
  id?: string;
  user_id: string;
  notification_type: string;
  notification_id?: string;
  notification_content?: Record<string, any>;
  was_acknowledged?: boolean;
  was_acted_upon?: boolean;
  was_ignored?: boolean;
  time_to_acknowledge_seconds?: number;
  time_to_action_seconds?: number;
  correlated_with_issue?: boolean;
  value_score?: number; // -1 to 1
  suppression_level?: SuppressionLevel;
  created_at?: string;
}

export interface MetaInsight {
  id?: string;
  user_id: string;
  insight_type: InsightType;
  insight_category?: string;
  insight_summary: string;
  insight_details?: Record<string, any>;
  confidence?: number; // 0 to 1
  action_taken?: Record<string, any>;
  impact_score?: number; // -1 to 1
  created_at?: string;
  expires_at?: string;
}

export interface MetaLearningConfig {
  id?: string;
  user_id: string;
  learning_domain: LearningDomain;
  is_enabled?: boolean;
  learning_rate?: number; // 0 to 1
  min_confidence_threshold?: number; // 0 to 1
  review_frequency?: "DAILY" | "WEEKLY" | "MONTHLY";
  last_review_at?: string;
  constraints?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

