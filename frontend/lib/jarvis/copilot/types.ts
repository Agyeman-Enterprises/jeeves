export type AutonomyMode = "OBSERVE" | "SUGGEST" | "ASSIST" | "EXECUTE" | "CO_PILOT";
export type CoordinationType = "REBALANCE" | "RESCHEDULE" | "REALLOCATE" | "PROTECT" | "OPTIMIZE";
export type ModeTransitionTrigger = "USER" | "COGNITIVE_STATE" | "EMOTIONAL_STATE" | "URGENCY" | "RISK" | "WORKLOAD" | "BUSINESS_CONDITIONS";

export interface CoPilotState {
  id?: string;
  user_id: string;
  current_mode: AutonomyMode;
  mode_context?: Record<string, any>;
  active_domains?: string[];
  coordination_status?: Record<string, any>;
  last_mode_change?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AutonomousAction {
  id?: string;
  user_id: string;
  action_type: string;
  domain: string;
  action_description: string;
  action_details?: Record<string, any>;
  triggered_by?: "CO_PILOT" | "AGENT" | "EVENT" | "SCHEDULE";
  mode_when_executed?: AutonomyMode;
  safety_checks_passed?: boolean;
  execution_result?: Record<string, any>;
  status?: "PENDING" | "EXECUTING" | "COMPLETED" | "FAILED" | "ROLLED_BACK";
  executed_at?: string;
  completed_at?: string;
  created_at?: string;
}

export interface CoPilotCoordination {
  id?: string;
  user_id: string;
  coordination_type: CoordinationType;
  affected_domains: string[];
  coordination_reason: string;
  actions_taken: Record<string, any>;
  system_state_before?: Record<string, any>;
  system_state_after?: Record<string, any>;
  impact_assessment?: Record<string, any>;
  created_at?: string;
}

export interface ModeTransition {
  id?: string;
  user_id: string;
  from_mode?: AutonomyMode;
  to_mode: AutonomyMode;
  transition_reason: string;
  triggered_by?: ModeTransitionTrigger;
  context?: Record<string, any>;
  created_at?: string;
}

export interface CoPilotMetrics {
  id?: string;
  user_id: string;
  metric_date: string;
  actions_executed?: number;
  actions_successful?: number;
  actions_failed?: number;
  time_saved_hours?: number;
  problems_prevented?: number;
  opportunities_captured?: number;
  user_satisfaction_score?: number; // 0-1
  system_health_score?: number; // 0-1
  created_at?: string;
}

