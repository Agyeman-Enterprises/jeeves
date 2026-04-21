export type AutonomyMode = "ASSISTIVE" | "COLLABORATIVE" | "DELEGATED" | "AUTONOMOUS";
export type CalibrationType = "INCREASE" | "DECREASE" | "MAINTAIN";
export type TriggeredBy = "user" | "behavior" | "risk" | "confidence" | "system";

export interface AutonomySettings {
  id?: string;
  user_id: string;
  global_mode: AutonomyMode;
  behavior_score?: number; // 0.0 to 1.0
  auto_calibration_enabled?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DomainAutonomy {
  id?: string;
  user_id: string;
  domain: string; // "clinical" | "financial" | "operations" | "communications" | "files" | "internal_ai"
  allowed_modes: AutonomyMode[];
  default_mode: AutonomyMode;
  current_mode: AutonomyMode;
  rules?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface AgentAutonomy {
  id?: string;
  user_id: string;
  agent_slug: string;
  autonomy_mode?: AutonomyMode;
  is_override?: boolean;
  reason?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TaskAutonomy {
  id?: string;
  user_id: string;
  action_type: string;
  autonomy_mode: AutonomyMode;
  is_override?: boolean;
  reason?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AutonomyHistory {
  id?: string;
  user_id: string;
  domain?: string;
  agent_slug?: string;
  action_type?: string;
  previous_mode?: AutonomyMode;
  new_mode: AutonomyMode;
  reason?: string;
  triggered_by?: TriggeredBy;
  confidence_score?: number;
  created_at?: string;
}

export interface AutonomyCalibration {
  id?: string;
  user_id: string;
  domain?: string;
  calibration_type: CalibrationType;
  previous_mode?: AutonomyMode;
  new_mode?: AutonomyMode;
  behavior_evidence?: Record<string, any>;
  confidence_score?: number;
  applied?: boolean;
  created_at?: string;
}

