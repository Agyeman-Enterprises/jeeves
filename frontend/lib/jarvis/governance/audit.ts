import { supabaseServer } from "@/lib/supabase/server";
import type { AuditLog, RiskLevel, ComplianceFlag, TriggeredBy } from "./types";

export async function logAuditEvent(log: Partial<AuditLog>): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_audit_log")
    .insert({
      user_id: log.user_id,
      action_type: log.action_type!,
      domain: log.domain!,
      agent_slug: log.agent_slug,
      plan_id: log.plan_id,
      agent_run_id: log.agent_run_id,
      action_log_id: log.action_log_id,
      triggered_by: log.triggered_by!,
      trigger_details: log.trigger_details,
      action_summary: log.action_summary!,
      action_details: log.action_details!,
      justification: log.justification,
      reasoning: log.reasoning,
      status: log.status!,
      outcome: log.outcome,
      error_details: log.error_details,
      risk_level: log.risk_level || "LOW",
      compliance_flags: log.compliance_flags || [],
      requires_review: log.requires_review || false,
      reviewed_by: log.reviewed_by,
      reviewed_at: log.reviewed_at,
      patient_id: log.patient_id,
      entity_id: log.entity_id,
      workspace_id: log.workspace_id,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to log audit event: ${error?.message}`);
  }

  return (data as any).id;
}

export function determineRiskLevel(
  domain: string,
  actionType: string,
  input: Record<string, any>
): RiskLevel {
  // Clinical actions are generally higher risk
  if (domain === "clinical") {
    if (actionType.includes("refill") || actionType.includes("order")) {
      return "HIGH";
    }
    if (actionType.includes("note") || actionType.includes("message")) {
      return "MEDIUM";
    }
    return "MEDIUM";
  }

  // Financial actions
  if (domain === "financial") {
    if (actionType.includes("allocate") || actionType.includes("payment")) {
      return "HIGH";
    }
    if (actionType.includes("categorize")) {
      return "LOW";
    }
    return "MEDIUM";
  }

  // Email actions
  if (domain === "email") {
    if (actionType === "email.send") {
      // Check if external recipient
      const recipient = input.to || input.recipient;
      if (recipient && !recipient.includes("@yourdomain.com")) {
        return "MEDIUM";
      }
      return "LOW";
    }
    return "LOW";
  }

  // File operations
  if (domain === "files") {
    if (actionType === "file.delete") {
      return "MEDIUM";
    }
    return "LOW";
  }

  return "LOW";
}

export function determineComplianceFlags(
  domain: string,
  actionType: string,
  input: Record<string, any>
): ComplianceFlag[] {
  const flags: ComplianceFlag[] = [];

  // Clinical actions require HIPAA compliance
  if (domain === "clinical") {
    flags.push("HIPAA");
    flags.push("CLINICAL");
  }

  // Financial actions
  if (domain === "financial") {
    flags.push("FINANCIAL");
    // Tax-related actions
    if (actionType.includes("tax")) {
      flags.push("SOX");
    }
  }

  // Patient-facing actions
  if (input.patient_id || input.patient_email) {
    flags.push("HIPAA");
  }

  return flags;
}

export async function getAuditLogs(
  userId: string,
  filters?: {
    domain?: string;
    agent_slug?: string;
    patient_id?: string;
    entity_id?: string;
    compliance_flag?: ComplianceFlag;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }
): Promise<AuditLog[]> {
  let query = supabaseServer
    .from("jarvis_audit_log")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (filters?.domain) {
    query = query.eq("domain", filters.domain);
  }

  if (filters?.agent_slug) {
    query = query.eq("agent_slug", filters.agent_slug);
  }

  if (filters?.patient_id) {
    query = query.eq("patient_id", filters.patient_id);
  }

  if (filters?.entity_id) {
    query = query.eq("entity_id", filters.entity_id);
  }

  if (filters?.compliance_flag) {
    query = query.contains("compliance_flags", [filters.compliance_flag]);
  }

  if (filters?.start_date) {
    query = query.gte("created_at", filters.start_date);
  }

  if (filters?.end_date) {
    query = query.lte("created_at", filters.end_date);
  }

  if (filters?.limit) {
    query = query.limit(filters.limit);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get audit logs: ${error.message}`);
  }

  return (data || []) as AuditLog[];
}

