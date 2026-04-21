export type ResourceType = "COGNITIVE" | "TEMPORAL" | "OPERATIONAL" | "FINANCIAL" | "CREATIVE_STRATEGIC";
export type AllocationStatus = "PENDING" | "ALLOCATED" | "ACTIVE" | "COMPLETED" | "CANCELLED" | "REALLOCATED";
export type EmotionalLoad = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type RiskTolerance = "LOW" | "MODERATE" | "HIGH";
export type CapabilityFit = "DR_A_REQUIRED" | "STAFF_CAN_DO" | "AGENT_CAN_DO" | "AUTOMATED";
export type RecommendationType = "REALLOCATE" | "POSTPONE" | "PRIORITIZE" | "DELEGATE" | "AUTOMATE" | "ELIMINATE";

export interface CognitiveBudget {
  id?: string;
  user_id: string;
  budget_date: string; // ISO date string
  total_energy_percentage: number; // 0-100
  deep_work_capacity_hours?: number;
  decision_capacity_count?: number;
  emotional_load?: EmotionalLoad;
  risk_tolerance?: RiskTolerance;
  cognitive_state?: Record<string, any>;
  recommended_tasks?: Record<string, any>;
  tasks_to_avoid?: Record<string, any>;
  optimal_focus_zones?: Record<string, any>;
  created_at?: string;
}

export interface ResourceAllocation {
  id?: string;
  user_id: string;
  resource_type: ResourceType;
  allocation_target: string;
  target_id?: string;
  allocated_amount: number;
  allocation_unit: string; // "HOURS" | "DOLLARS" | "COGNITIVE_UNITS" | "AGENT_TASKS" | "STAFF_HOURS"
  priority?: number;
  importance_score?: number; // 0-1
  urgency_score?: number; // 0-1
  effort_level?: number; // 0-1
  output_multiplier?: number; // 0-1
  energy_match_score?: number; // 0-1
  opportunity_cost?: number;
  capability_fit?: CapabilityFit;
  status?: AllocationStatus;
  allocated_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ResourceConstraint {
  id?: string;
  user_id: string;
  resource_type: ResourceType;
  constraint_name: string;
  constraint_value: number;
  constraint_unit: string;
  period?: "DAILY" | "WEEKLY" | "MONTHLY" | "ANNUAL";
  is_hard_limit?: boolean;
  applies_to?: string;
  created_at?: string;
  updated_at?: string;
}

export interface StrategicPriorityMap {
  id?: string;
  user_id: string;
  week_start_date: string; // ISO date string
  priority_map: Record<string, any>;
  must_happen?: Record<string, any>;
  should_happen?: Record<string, any>;
  can_happen?: Record<string, any>;
  must_not_happen?: Record<string, any>;
  business_unit_priorities?: Record<string, any>;
  resource_allocation_summary?: Record<string, any>;
  created_at?: string;
}

export interface AgentResourceAllocation {
  id?: string;
  user_id: string;
  agent_slug: string;
  allocation_period_start: string;
  allocation_period_end: string;
  allocated_tasks?: number;
  completed_tasks?: number;
  failed_tasks?: number;
  average_success_probability?: number; // 0-1
  current_load_percentage?: number; // 0-100
  priority_distribution?: Record<string, any>;
  retry_strategy?: Record<string, any>;
  off_peak_allocation?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface FinancialAllocation {
  id?: string;
  user_id: string;
  entity_id?: string;
  allocation_type: "INVESTMENT" | "OPERATING" | "CAPEX" | "TAX" | "RESERVE";
  allocated_amount: number;
  allocation_period?: "WEEKLY" | "MONTHLY" | "QUARTERLY" | "ANNUAL";
  roi_projection?: Record<string, any>;
  risk_assessment?: Record<string, any>;
  runway_impact?: Record<string, any>;
  status?: AllocationStatus;
  allocated_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AllocationRecommendation {
  id?: string;
  user_id: string;
  recommendation_type: RecommendationType;
  resource_type: ResourceType;
  current_allocation?: Record<string, any>;
  recommended_allocation?: Record<string, any>;
  reasoning?: Record<string, any>;
  impact_estimate?: Record<string, any>;
  priority?: number;
  status?: "PENDING" | "ACCEPTED" | "REJECTED" | "IMPLEMENTED";
  accepted_at?: string;
  implemented_at?: string;
  created_at?: string;
}

