export type EmotionalState =
  | "neutral"
  | "stressed"
  | "overwhelmed"
  | "focused"
  | "frustrated"
  | "tired"
  | "energized";

export type SignalType =
  | "typing_pattern"
  | "timing"
  | "behavioral_change"
  | "emotional_cue"
  | "calendar_context"
  | "system_stress";

export type AdaptationType =
  | "tone"
  | "timing"
  | "autonomy"
  | "verbosity"
  | "notifications"
  | "escalation";

export interface MentalState {
  id?: string;
  user_id: string;
  stress_level: number; // 0-100
  fatigue_level: number; // 0-100
  focus_level: number; // 0-100
  decision_load: number; // 0-100
  emotional_state: EmotionalState;
  cognitive_bandwidth: number; // 0-100
  energy_level: number; // 0-100
  state_vector?: Record<string, any>;
  detected_at?: string;
  created_at?: string;
}

export interface BehavioralSignal {
  id?: string;
  user_id: string;
  signal_type: SignalType;
  signal_data: Record<string, any>;
  detected_at?: string;
  created_at?: string;
}

export interface EnergyPattern {
  id?: string;
  user_id: string;
  day_of_week?: number; // 0-6
  hour_of_day?: number; // 0-23
  avg_energy_level?: number;
  avg_focus_level?: number;
  avg_stress_level?: number;
  pattern_type?: "peak" | "valley" | "steady" | "variable";
  confidence_score?: number;
  sample_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface StateAdaptation {
  id?: string;
  user_id: string;
  mental_state_id?: string;
  adaptation_type: AdaptationType;
  previous_value?: string;
  new_value?: string;
  reason?: string;
  applied_at?: string;
  created_at?: string;
}

export interface EmotionalRule {
  id?: string;
  user_id: string;
  state_condition: Record<string, any>;
  adaptations: Record<string, any>;
  priority?: number;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SupportMode {
  id?: string;
  user_id: string;
  triggered_by: "burnout" | "overwhelm" | "cognitive_exhaustion" | "user_request";
  state_snapshot?: Record<string, any>;
  adaptations_applied?: Record<string, any>;
  status?: "ACTIVE" | "INACTIVE";
  activated_at?: string;
  deactivated_at?: string;
}

