export type AgentIntent =
  | "NEEDS_FOLLOWUP"
  | "DELEGATE"
  | "HELP_REQUEST"
  | "TASK_COMPLETE"
  | "CONFLICT"
  | "BLOCKED"
  | "READY"
  | "ESCALATE"
  | "COLLABORATE"
  | "HANDOFF"
  | "BROADCAST";

export type CoordinationType = "DELEGATE" | "HANDOFF" | "COLLABORATE" | "ESCALATE";
export type ConflictType = "SCHEDULING" | "RESOURCE" | "PRIORITY" | "POLICY" | "DATA";
export type DependencyType = "BLOCKS" | "REQUIRES" | "OPTIONAL";
export type LockType = "READ" | "WRITE" | "EXCLUSIVE";
export type CoordinatorType = "nexus" | "clinic_director" | "ops_director";

export interface AgentMessage {
  id?: string;
  from_agent: string;
  to_agent?: string; // null = broadcast
  intent: AgentIntent;
  payload: Record<string, any>;
  status?: "PENDING" | "ACKNOWLEDGED" | "RESOLVED" | "IGNORED";
  acknowledged_at?: string;
  resolved_at?: string;
  created_at?: string;
}

export interface AgentCoordination {
  id?: string;
  plan_id?: string;
  plan_step_id?: string;
  from_agent: string;
  to_agent: string;
  coordination_type: CoordinationType;
  reason?: string;
  payload?: Record<string, any>;
  status?: "PENDING" | "ACCEPTED" | "REJECTED" | "COMPLETED";
  accepted_at?: string;
  completed_at?: string;
  created_at?: string;
}

export interface AgentConflict {
  id?: string;
  user_id: string;
  conflict_type: ConflictType;
  agents_involved: string[];
  conflict_description: string;
  agent_positions: Record<string, any>; // Each agent's position/argument
  resolution_status?: "PENDING" | "RESOLVED" | "ESCALATED";
  resolved_by?: string; // "jarvis" | agent slug | "user"
  resolution?: Record<string, any>;
  resolved_at?: string;
  created_at?: string;
}

export interface AgentDependency {
  id?: string;
  plan_id?: string;
  blocking_task_id: string;
  blocked_task_id: string;
  dependency_type: DependencyType;
  created_at?: string;
}

export interface AgentLock {
  id?: string;
  resource_type: string; // "patient" | "entity" | "file" | "calendar" | "task"
  resource_id: string;
  agent_slug: string;
  lock_type: LockType;
  expires_at: string;
  created_at?: string;
}

export interface ExecutiveCoordinator {
  id?: string;
  user_id: string;
  coordinator_type: CoordinatorType;
  name: string;
  description?: string;
  managed_domains: string[];
  managed_agents?: string[];
  config?: Record<string, any>;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AgentQueueItem {
  id?: string;
  agent_slug: string;
  agent_run_id: string;
  priority?: number;
  status?: "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED";
  queued_at?: string;
  started_at?: string;
  completed_at?: string;
}

export interface AgentCollaboration {
  id?: string;
  plan_id?: string;
  session_name?: string;
  agents_involved: string[];
  shared_context?: Record<string, any>;
  status?: "ACTIVE" | "COMPLETED" | "ABANDONED";
  started_at?: string;
  completed_at?: string;
}

