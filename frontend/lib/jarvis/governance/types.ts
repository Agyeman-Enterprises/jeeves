export type KillSwitchType = "AGENT" | "DOMAIN" | "AUTOMATION_FREEZE" | "FULL_SHUTDOWN";
export type KillSwitchStatus = "ACTIVE" | "INACTIVE";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ComplianceFlag = "HIPAA" | "FINRA" | "SOX" | "CLINICAL" | "FINANCIAL" | "GDPR";
export type AuditStatus = "SUCCESS" | "FAILED" | "BLOCKED" | "PENDING";
export type TriggeredBy = "user" | "agent" | "system" | "scheduled";

export interface AgentPermissions {
  id?: string;
  user_id: string;
  agent_slug: string;
  can_read: boolean;
  can_write: boolean;
  can_update: boolean;
  can_delete: boolean;
  can_message: boolean;
  can_email: boolean;
  can_patient_facing: boolean;
  can_clinical_actions: boolean;
  can_financial_actions: boolean;
  can_operational_actions: boolean;
  can_file_operations: boolean;
  can_scheduling: boolean;
  can_system_level: boolean;
  allowed_actions?: string[];
  blocked_actions?: string[];
  requires_approval_for?: string[];
  conditions?: Record<string, any>;
}

export interface AuditLog {
  id?: string;
  user_id: string;
  action_type: string;
  domain: string;
  agent_slug?: string;
  plan_id?: string;
  agent_run_id?: string;
  action_log_id?: string;
  triggered_by: TriggeredBy;
  trigger_details?: Record<string, any>;
  action_summary: string;
  action_details: Record<string, any>;
  justification?: string;
  reasoning?: Record<string, any>;
  status: AuditStatus;
  outcome?: Record<string, any>;
  error_details?: string;
  risk_level: RiskLevel;
  compliance_flags?: ComplianceFlag[];
  requires_review: boolean;
  reviewed_by?: string;
  reviewed_at?: string;
  patient_id?: string;
  entity_id?: string;
  workspace_id?: string;
  created_at?: string;
}

export interface KillSwitch {
  id?: string;
  user_id: string;
  switch_type: KillSwitchType;
  target: string; // Agent slug, domain name, or "ALL"
  status: KillSwitchStatus;
  reason?: string;
  activated_by?: string;
  activated_at?: string;
  deactivated_by?: string;
  deactivated_at?: string;
  expires_at?: string;
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface SafetyRule {
  max_frequency_per_hour?: number;
  max_frequency_per_day?: number;
  allowed_recipients?: string[];
  blocked_recipients?: string[];
  allowed_times?: { start: string; end: string };
  requires_2fa?: boolean;
  max_amount?: number;
  requires_second_approval?: boolean;
  [key: string]: any;
}

