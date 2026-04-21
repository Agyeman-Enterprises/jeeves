import { supabaseServer } from "@/lib/supabase/server";
import { checkActionAllowed } from "./policy";
import { executeAction } from "./executor";
import type { ActionRequest, ActionResult, ActionLog, ActionApproval } from "./types";
import { selectPersona } from "../persona/selector";
import type { PersonaContext } from "../persona/types";
import { checkKillSwitch } from "../governance/killswitch";
import { checkAgentPermission } from "../governance/permissions";
import { logAuditEvent, determineRiskLevel, determineComplianceFlags } from "../governance/audit";
import { getAutonomyMode } from "../autonomy/modes";

export async function processAction(
  userId: string,
  request: ActionRequest,
  agentSlug?: string
): Promise<ActionResult> {
  // 0. Kill Switch Check (highest priority)
  const killSwitchCheck = await checkKillSwitch(userId, request.domain, agentSlug);
  if (killSwitchCheck.blocked) {
    // Log blocked action
    await logAuditEvent({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      agent_slug: agentSlug,
      triggered_by: agentSlug ? "agent" : "system",
      action_summary: `Action blocked by kill switch: ${killSwitchCheck.reason}`,
      action_details: request.input,
      status: "BLOCKED",
      risk_level: "HIGH",
      compliance_flags: determineComplianceFlags(request.domain, request.action_type, request.input),
    });

    return {
      success: false,
      action_log_id: "",
      status: "REJECTED",
      error: killSwitchCheck.reason,
    };
  }

  // 0.5. Agent Permission Check
  if (agentSlug) {
    const permissionCheck = await checkAgentPermission(userId, agentSlug, request.action_type);
    if (!permissionCheck.allowed) {
      await logAuditEvent({
        user_id: userId,
        action_type: request.action_type,
        domain: request.domain,
        agent_slug: agentSlug,
        triggered_by: "agent",
        action_summary: `Action blocked by permission matrix: ${permissionCheck.reason}`,
        action_details: request.input,
        status: "BLOCKED",
        risk_level: determineRiskLevel(request.domain, request.action_type, request.input),
        compliance_flags: determineComplianceFlags(request.domain, request.action_type, request.input),
      });

      return {
        success: false,
        action_log_id: "",
        status: "REJECTED",
        error: permissionCheck.reason,
      };
    }
  }

  // 1. Policy Check
  const policyCheck = await checkActionAllowed(userId, request);
  if (!policyCheck.allowed) {
    // Log the blocked action
    await logAuditEvent({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      agent_slug: agentSlug,
      triggered_by: agentSlug ? "agent" : "system",
      action_summary: `Action blocked by policy: ${policyCheck.reason}`,
      action_details: request.input,
      status: "BLOCKED",
      risk_level: determineRiskLevel(request.domain, request.action_type, request.input),
      compliance_flags: determineComplianceFlags(request.domain, request.action_type, request.input),
    });

    const logId = await logAction({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      autonomy_level: policyCheck.policy.autonomy_level,
      status: "REJECTED",
      policy_id: policyCheck.policy.id,
      plan_id: request.plan_id,
      agent_run_id: request.agent_run_id,
      input: request.input,
      approval_required: false,
      error: policyCheck.reason,
    });

    return {
      success: false,
      action_log_id: logId,
      status: "REJECTED",
      error: policyCheck.reason,
    };
  }

  const policy = policyCheck.policy;

  // 1.5. Autonomy Mode Check
  const autonomyMode = await getAutonomyMode(userId, request.domain, agentSlug, request.action_type);
  
  // Override policy autonomy level based on current autonomy mode
  if (autonomyMode === "ASSISTIVE") {
    // Force suggest-only mode
    const logId = await logAction({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      autonomy_level: "SUGGEST_ONLY",
      status: "PENDING",
      policy_id: policy.id,
      plan_id: request.plan_id,
      agent_run_id: request.agent_run_id,
      input: request.input,
      approval_required: false,
    });

    return {
      success: true,
      action_log_id: logId,
      status: "PENDING",
      output: { suggestion: "Action suggested in ASSISTIVE mode - awaiting explicit instruction" },
    };
  }

  // Adjust policy based on autonomy mode
  if (autonomyMode === "DELEGATED" && policy.autonomy_level === "ASK_THEN_ACT") {
    policy.autonomy_level = "AUTO_ACT";
    policy.requires_approval = false;
  } else if (autonomyMode === "AUTONOMOUS" && policy.autonomy_level !== "SUGGEST_ONLY") {
    policy.autonomy_level = "AUTO_ACT";
    policy.requires_approval = false;
  }

  // 2. Persona / Context Check
  const personaContext: PersonaContext = {
    domain: request.domain,
    task_classification: request.action_type,
    is_patient_interaction: request.domain === "clinical" && request.input.patient_id,
    is_internal_team: request.domain === "ops",
    is_technical_task: request.domain === "files",
    communication_channel: "internal",
  };

  const persona = await selectPersona(userId, personaContext);

  // 3. Determine execution path based on autonomy level
  if (policy.autonomy_level === "SUGGEST_ONLY") {
    // Just log and return suggestion
    const logId = await logAction({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      autonomy_level: policy.autonomy_level,
      status: "PENDING",
      policy_id: policy.id,
      plan_id: request.plan_id,
      agent_run_id: request.agent_run_id,
      input: request.input,
      approval_required: false,
    });

    return {
      success: true,
      action_log_id: logId,
      status: "PENDING",
      output: { suggestion: "Action suggested, awaiting user approval" },
    };
  }

  if (policy.autonomy_level === "ASK_THEN_ACT" || policy.requires_approval) {
    // Create approval request
    const logId = await logAction({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      autonomy_level: policy.autonomy_level,
      status: "PENDING",
      policy_id: policy.id,
      plan_id: request.plan_id,
      agent_run_id: request.agent_run_id,
      input: request.input,
      approval_required: true,
    });

    const approvalId = await createApprovalRequest({
      user_id: userId,
      action_log_id: logId,
      action_type: request.action_type,
      domain: request.domain,
      summary: generateActionSummary(request),
      details: request.input,
      urgency: request.urgency || "NORMAL",
    });

    return {
      success: true,
      action_log_id: logId,
      status: "PENDING",
      requires_approval: true,
      approval_id: approvalId,
    };
  }

  // 4. Auto-execute (AUTO_ACT)
  try {
    const executionResult = await executeAction(userId, request, persona);

    const logId = await logAction({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      autonomy_level: policy.autonomy_level,
      status: executionResult.success ? "EXECUTED" : "FAILED",
      policy_id: policy.id,
      plan_id: request.plan_id,
      agent_run_id: request.agent_run_id,
      input: request.input,
      output: executionResult.output,
      error: executionResult.error,
      approval_required: false,
      executed_at: executionResult.success ? new Date().toISOString() : undefined,
    });

    // 5. Audit + Memory
    await auditAction(userId, logId, request, executionResult, agentSlug);

    return {
      success: executionResult.success,
      action_log_id: logId,
      status: executionResult.success ? "EXECUTED" : "FAILED",
      output: executionResult.output,
      error: executionResult.error,
    };
  } catch (error: any) {
    const logId = await logAction({
      user_id: userId,
      action_type: request.action_type,
      domain: request.domain,
      autonomy_level: policy.autonomy_level,
      status: "FAILED",
      policy_id: policy.id,
      plan_id: request.plan_id,
      agent_run_id: request.agent_run_id,
      input: request.input,
      error: error.message,
      approval_required: false,
    });

    return {
      success: false,
      action_log_id: logId,
      status: "FAILED",
      error: error.message,
    };
  }
}

async function logAction(log: Partial<ActionLog>): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_action_logs")
    .insert({
      user_id: log.user_id,
      action_type: log.action_type,
      domain: log.domain,
      autonomy_level: log.autonomy_level,
      status: log.status,
      policy_id: log.policy_id,
      plan_id: log.plan_id,
      agent_run_id: log.agent_run_id,
      input: log.input,
      output: log.output,
      error: log.error,
      approval_required: log.approval_required,
      approved_by: log.approved_by,
      approved_at: log.approved_at,
      executed_at: log.executed_at,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to log action: ${error?.message}`);
  }

  return (data as any).id;
}

async function createApprovalRequest(approval: Partial<ActionApproval>): Promise<string> {
  // Set expiration (default 24 hours)
  const expiresAt = new Date();
  expiresAt.setHours(expiresAt.getHours() + 24);

  const { data, error } = await supabaseServer
    .from("jarvis_action_approvals")
    .insert({
      user_id: approval.user_id,
      action_log_id: approval.action_log_id,
      action_type: approval.action_type,
      domain: approval.domain,
      summary: approval.summary,
      details: approval.details,
      urgency: approval.urgency || "NORMAL",
      expires_at: expiresAt.toISOString(),
      status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create approval request: ${error?.message}`);
  }

  return (data as any).id;
}

function generateActionSummary(request: ActionRequest): string {
  // Generate human-readable summary based on action type
  const summaries: Record<string, (input: any) => string> = {
    "email.send": (input) => `Send email to ${input.to || "recipient"}: ${input.subject || "No subject"}`,
    "calendar.create": (input) => `Create calendar event: ${input.title || "Untitled"} on ${input.start_time || "TBD"}`,
    "clinical.task.create": (input) => `Create task for ${input.assignee || "MA/AI"}: ${input.description || "No description"}`,
    "clinical.refill.queue": (input) => `Queue medication refill: ${input.medication || "Unknown medication"}`,
    "financial.transaction.categorize": (input) => `Categorize transaction: ${input.amount || "$0"} as ${input.category || "uncategorized"}`,
    "file.move": (input) => `Move file: ${input.filename || "Unknown"} to ${input.destination || "Unknown"}`,
  };

  const generator = summaries[request.action_type];
  if (generator) {
    return generator(request.input);
  }

  return `Execute ${request.action_type} action`;
}

async function auditAction(
  userId: string,
  logId: string,
  request: ActionRequest,
  result: { success: boolean; output?: any; error?: string },
  agentSlug?: string
): Promise<void> {
  const riskLevel = determineRiskLevel(request.domain, request.action_type, request.input);
  const complianceFlags = determineComplianceFlags(request.domain, request.action_type, request.input);

  // Add to comprehensive audit log
  await logAuditEvent({
    user_id: userId,
    action_type: request.action_type,
    domain: request.domain,
    agent_slug: agentSlug,
    action_log_id: logId,
    plan_id: request.plan_id,
    agent_run_id: request.agent_run_id,
    triggered_by: agentSlug ? "agent" : "system",
    action_summary: generateActionSummary(request),
    action_details: request.input,
    justification: `Action executed as part of ${agentSlug ? `agent ${agentSlug}` : "system workflow"}`,
    status: result.success ? "SUCCESS" : "FAILED",
    outcome: result.output,
    error_details: result.error,
    risk_level: riskLevel,
    compliance_flags: complianceFlags,
    requires_review: riskLevel === "HIGH" || riskLevel === "CRITICAL" || complianceFlags.length > 0,
    patient_id: request.input.patient_id,
    entity_id: request.input.entity_id,
    workspace_id: request.context?.workspace,
  });

  // Add to journal
  await supabaseServer
    .from("jarvis_journal_entries")
    .insert({
      user_id: userId,
      query: `Action executed: ${request.action_type}`,
      meta: {
        action_log_id: logId,
        action_type: request.action_type,
        domain: request.domain,
        result,
        agent_slug: agentSlug,
      },
    } as any);

  // Add to timeline
  await supabaseServer
    .from("jarvis_timeline_events")
    .insert({
      user_id: userId,
      event_type: "JARVIS_ACTION",
      label: request.action_type,
      description: generateActionSummary(request),
      payload: {
        action_log_id: logId,
        request,
        result,
        agent_slug: agentSlug,
      },
    } as any);
}

