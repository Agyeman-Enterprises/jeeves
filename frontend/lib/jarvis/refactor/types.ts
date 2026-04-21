export type RefactoringLevel = "PARAMETRIC" | "STRUCTURAL" | "MODULAR" | "FULL_BRAIN_SCHEMA";
export type RefactoringStatus = "PROPOSED" | "APPROVED" | "REJECTED" | "IMPLEMENTING" | "COMPLETED" | "FAILED" | "ROLLED_BACK";
export type AuditType =
  | "SCHEMA"
  | "AGENT_PERFORMANCE"
  | "SITUATION_ROOM"
  | "FORESIGHT"
  | "PERSONAL_STATE"
  | "EVENT_ROUTING"
  | "MEMORY_GRAPH"
  | "SIMULATION"
  | "FINANCIAL";
export type EvolutionType = "CREATED" | "MODIFIED" | "SPLIT" | "MERGED" | "DEPRECATED" | "REPLACED";
export type SchemaEvolutionType =
  | "COLUMN_ADDED"
  | "COLUMN_MODIFIED"
  | "COLUMN_REMOVED"
  | "INDEX_ADDED"
  | "INDEX_REMOVED"
  | "TABLE_CREATED"
  | "TABLE_MODIFIED";

export interface SelfAudit {
  id?: string;
  user_id: string;
  audit_date: string; // ISO date string
  audit_type: AuditType;
  audit_results: Record<string, any>;
  issues_detected?: Record<string, any>;
  root_cause_analysis?: Record<string, any>;
  recommendations?: Record<string, any>;
  status?: "RUNNING" | "COMPLETED" | "FAILED";
  created_at?: string;
}

export interface RefactoringProposal {
  id?: string;
  user_id: string;
  proposal_name: string;
  proposal_description: string;
  refactoring_level: RefactoringLevel;
  target_component: string;
  current_state?: Record<string, any>;
  proposed_state?: Record<string, any>;
  expected_benefits?: Record<string, any>;
  risk_assessment?: Record<string, any>;
  implementation_steps?: Record<string, any>;
  estimated_impact?: Record<string, any>;
  status?: RefactoringStatus;
  approved_by_user?: boolean;
  approved_at?: string;
  implemented_at?: string;
  rollback_plan?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface RefactoringImplementation {
  id?: string;
  user_id: string;
  proposal_id?: string;
  implementation_type: string;
  component_name: string;
  changes_made: Record<string, any>;
  before_state?: Record<string, any>;
  after_state?: Record<string, any>;
  implementation_agent?: string;
  status?: RefactoringStatus;
  started_at?: string;
  completed_at?: string;
  error_log?: Record<string, any>;
  created_at?: string;
}

export interface RefactoringPerformance {
  id?: string;
  user_id: string;
  implementation_id?: string;
  metric_name: string;
  before_value?: number;
  after_value?: number;
  improvement_percentage?: number;
  measurement_period_start?: string;
  measurement_period_end?: string;
  created_at?: string;
}

export interface AgentEvolution {
  id?: string;
  user_id: string;
  agent_slug: string;
  evolution_type: EvolutionType;
  evolution_reason?: string;
  before_state?: Record<string, any>;
  after_state?: Record<string, any>;
  parent_agent_slug?: string;
  performance_impact?: Record<string, any>;
  created_at?: string;
}

export interface SchemaEvolution {
  id?: string;
  user_id: string;
  table_name: string;
  evolution_type: SchemaEvolutionType;
  change_description?: string;
  migration_sql?: string;
  before_schema?: Record<string, any>;
  after_schema?: Record<string, any>;
  reason?: string;
  impact_analysis?: Record<string, any>;
  status?: RefactoringStatus;
  applied_at?: string;
  created_at?: string;
}

