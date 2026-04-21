export type AutonomyLevel = "SUGGEST_ONLY" | "ASK_THEN_ACT" | "AUTO_ACT";
export type ActionStatus = "PENDING" | "APPROVED" | "EXECUTED" | "REJECTED" | "FAILED";
export type ActionDomain = "clinical" | "financial" | "email" | "calendar" | "files" | "ops";
export type Urgency = "LOW" | "NORMAL" | "HIGH" | "URGENT";

export type ActionType =
  // Email actions
  | "email.send"
  | "email.draft"
  | "email.triage"
  | "email.label"
  // Calendar actions
  | "calendar.create"
  | "calendar.update"
  | "calendar.cancel"
  | "calendar.move"
  // Clinical actions
  | "clinical.task.create"
  | "clinical.note.add"
  | "clinical.order.queue"
  | "clinical.refill.queue"
  | "clinical.appointment.schedule"
  // Financial actions
  | "financial.transaction.categorize"
  | "financial.entity.allocate"
  | "financial.tax.prep"
  | "financial.reminder.create"
  // File actions
  | "file.move"
  | "file.rename"
  | "file.tag"
  | "file.archive"
  | "file.delete"
  // Ops actions
  | "ops.dashboard.update"
  | "ops.flag.set"
  | "ops.status.update";

export interface ActionPolicy {
  id?: string;
  user_id: string;
  domain: ActionDomain;
  action_type: ActionType;
  autonomy_level: AutonomyLevel;
  requires_approval: boolean;
  requires_md_review?: boolean;
  requires_explicit_consent?: boolean;
  conditions?: Record<string, any>;
}

export interface ActionRequest {
  action_type: ActionType;
  domain: ActionDomain;
  input: Record<string, any>;
  plan_id?: string;
  agent_run_id?: string;
  urgency?: Urgency;
  context?: Record<string, any>;
}

export interface ActionResult {
  success: boolean;
  action_log_id: string;
  status: ActionStatus;
  output?: Record<string, any>;
  error?: string;
  requires_approval?: boolean;
  approval_id?: string;
}

export interface ActionLog {
  id?: string;
  user_id: string;
  action_type: ActionType;
  domain: ActionDomain;
  autonomy_level: AutonomyLevel;
  status: ActionStatus;
  policy_id?: string;
  plan_id?: string;
  agent_run_id?: string;
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  approval_required: boolean;
  approved_by?: string;
  approved_at?: string;
  executed_at?: string;
  created_at?: string;
}

export interface ActionApproval {
  id?: string;
  user_id: string;
  action_log_id: string;
  action_type: ActionType;
  domain: ActionDomain;
  summary: string;
  details: Record<string, any>;
  urgency: Urgency;
  expires_at?: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
  reviewed_at?: string;
  created_at?: string;
}

