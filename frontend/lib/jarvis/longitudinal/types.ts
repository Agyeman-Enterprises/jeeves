export type PatternType = "DAILY" | "WEEKLY" | "MONTHLY" | "ANNUAL";
export type IdentityDimension =
  | "energy"
  | "focus"
  | "stress"
  | "decision_load"
  | "autonomy_preference"
  | "work_intensity"
  | "command_frequency"
  | "decision_speed"
  | "correction_rate"
  | "frustration_threshold"
  | "fatigue_pattern"
  | "communication_tone"
  | "escalation_sensitivity"
  | "burnout_indicators"
  | "productivity_rhythm"
  | "clinical_risk_tolerance"
  | "financial_risk_tolerance"
  | "operational_autonomy";

export type DriftDirection = "INCREASING" | "DECREASING" | "SHIFTING";
export type IdentityType = "mission" | "life_purpose" | "career_arc" | "leadership_philosophy" | "ethical_orientation" | "values";
export type PredictionType = "burnout_risk" | "workload_sustainability" | "energy_decline" | "goal_drift" | "clinical_load_buildup" | "financial_decision_pressure" | "project_overload" | "time_debt";
export type WarningLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface LongitudinalIdentity {
  id?: string;
  user_id: string;
  dimension: IdentityDimension;
  baseline_value?: number;
  current_value?: number;
  trend_7days?: number;
  trend_30days?: number;
  trend_90days?: number;
  variance?: number;
  pattern_type?: "stable" | "increasing" | "decreasing" | "cyclical" | "volatile";
  confidence_score?: number;
  sample_count?: number;
  first_observed_at?: string;
  last_observed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TimePattern {
  id?: string;
  user_id: string;
  pattern_type: PatternType;
  pattern_name: string;
  time_spec: Record<string, any>;
  dimension: IdentityDimension;
  effect_value: number;
  confidence_score?: number;
  sample_count?: number;
  first_observed_at?: string;
  last_observed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface IdentityDrift {
  id?: string;
  user_id: string;
  dimension: IdentityDimension;
  previous_baseline?: number;
  new_baseline?: number;
  drift_magnitude?: number;
  drift_direction?: DriftDirection;
  detected_at?: string;
  evidence?: Record<string, any>;
  adaptation_applied?: boolean;
  created_at?: string;
}

export interface LongTermIdentity {
  id?: string;
  user_id: string;
  identity_type: IdentityType;
  content: string;
  priority?: number;
  reinforcement_count?: number;
  last_reinforced_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BehavioralIdentity {
  id?: string;
  user_id: string;
  pattern_category: string;
  pattern_data: Record<string, any>;
  baseline?: Record<string, any>;
  current?: Record<string, any>;
  trend?: Record<string, any>;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface EmotionalIdentity {
  id?: string;
  user_id: string;
  pattern_category: string;
  pattern_data: Record<string, any>;
  baseline?: Record<string, any>;
  current?: Record<string, any>;
  trend?: Record<string, any>;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface IntentionalIdentity {
  id?: string;
  user_id: string;
  pattern_category: string;
  pattern_data: Record<string, any>;
  baseline?: Record<string, any>;
  current?: Record<string, any>;
  trend?: Record<string, any>;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface FutureSelfPrediction {
  id?: string;
  user_id: string;
  prediction_type: PredictionType;
  time_horizon: string;
  predicted_value: Record<string, any>;
  confidence_score?: number;
  warning_level?: WarningLevel;
  recommendations?: Record<string, any>;
  created_at?: string;
  expires_at?: string;
}

