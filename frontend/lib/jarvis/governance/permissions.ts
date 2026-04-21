import { supabaseServer } from "@/lib/supabase/server";
import type { AgentPermissions } from "./types";

export async function getAgentPermissions(
  userId: string,
  agentSlug: string
): Promise<AgentPermissions | null> {
  const { data } = await supabaseServer
    .from("jarvis_agent_permissions")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug)
    .single();

  if (data) {
    return data as AgentPermissions;
  }

  // Return default permissions if none exist
  return getDefaultPermissions(userId, agentSlug);
}

function getDefaultPermissions(
  userId: string,
  agentSlug: string
): AgentPermissions {
  // Default permissions based on agent type
  const defaults: Record<string, Partial<AgentPermissions>> = {
    // Clinical agents
    hospitalization_agent: {
      can_read: true,
      can_write: false,
      can_update: false,
      can_delete: false,
      can_message: false,
      can_email: false,
      can_patient_facing: false,
      can_clinical_actions: true,
      can_financial_actions: false,
      can_operational_actions: true,
      can_file_operations: false,
      can_scheduling: false,
      can_system_level: false,
      allowed_actions: ["clinical.task.create", "clinical.note.add"],
      blocked_actions: ["clinical.refill.queue", "clinical.order.queue"],
      requires_approval_for: ["clinical.note.add"],
    },
    glp_monitor_agent: {
      can_read: true,
      can_write: false,
      can_update: false,
      can_delete: false,
      can_message: false,
      can_email: false,
      can_patient_facing: false,
      can_clinical_actions: true,
      can_financial_actions: false,
      can_operational_actions: true,
      can_file_operations: false,
      can_scheduling: true,
      can_system_level: false,
      allowed_actions: ["clinical.appointment.schedule", "clinical.task.create"],
      blocked_actions: ["clinical.refill.queue", "clinical.order.queue"],
      requires_approval_for: ["clinical.appointment.schedule"],
    },
    scheduler_agent: {
      can_read: true,
      can_write: false,
      can_update: false,
      can_delete: false,
      can_message: false,
      can_email: false,
      can_patient_facing: false,
      can_clinical_actions: true,
      can_financial_actions: false,
      can_operational_actions: true,
      can_file_operations: false,
      can_scheduling: true,
      can_system_level: false,
      allowed_actions: ["clinical.appointment.schedule", "calendar.create"],
      blocked_actions: ["calendar.cancel"],
      requires_approval_for: [],
    },
    triage_agent: {
      can_read: true,
      can_write: false,
      can_update: false,
      can_delete: false,
      can_message: false,
      can_email: false,
      can_patient_facing: false,
      can_clinical_actions: true,
      can_financial_actions: false,
      can_operational_actions: true,
      can_file_operations: false,
      can_scheduling: false,
      can_system_level: false,
      allowed_actions: ["clinical.task.create", "ops.flag.set"],
      blocked_actions: ["email.send", "clinical.note.add"],
      requires_approval_for: ["clinical.task.create"],
    },
    // Financial agents
    financial_agent: {
      can_read: true,
      can_write: false,
      can_update: false,
      can_delete: false,
      can_message: false,
      can_email: false,
      can_patient_facing: false,
      can_clinical_actions: false,
      can_financial_actions: true,
      can_operational_actions: true,
      can_file_operations: false,
      can_scheduling: false,
      can_system_level: false,
      allowed_actions: ["financial.transaction.categorize", "financial.tax.prep", "financial.reminder.create"],
      blocked_actions: ["financial.entity.allocate"],
      requires_approval_for: ["financial.tax.prep"],
    },
    // Intake agents
    intake_agent: {
      can_read: true,
      can_write: false,
      can_update: false,
      can_delete: false,
      can_message: false,
      can_email: false,
      can_patient_facing: false,
      can_clinical_actions: true,
      can_financial_actions: false,
      can_operational_actions: true,
      can_file_operations: false,
      can_scheduling: true,
      can_system_level: false,
      allowed_actions: ["clinical.appointment.schedule", "clinical.task.create"],
      blocked_actions: ["clinical.note.add", "clinical.refill.queue"],
      requires_approval_for: [],
    },
    chartprep_agent: {
      can_read: true,
      can_write: false,
      can_update: false,
      can_delete: false,
      can_message: false,
      can_email: false,
      can_patient_facing: false,
      can_clinical_actions: true,
      can_financial_actions: false,
      can_operational_actions: true,
      can_file_operations: false,
      can_scheduling: false,
      can_system_level: false,
      allowed_actions: ["clinical.task.create"],
      blocked_actions: ["clinical.note.add", "clinical.refill.queue", "clinical.order.queue"],
      requires_approval_for: [],
    },
  };

  const defaultPerms = defaults[agentSlug] || {
    can_read: true,
    can_write: false,
    can_update: false,
    can_delete: false,
    can_message: false,
    can_email: false,
    can_patient_facing: false,
    can_clinical_actions: false,
    can_financial_actions: false,
    can_operational_actions: true,
    can_file_operations: false,
    can_scheduling: false,
    can_system_level: false,
    allowed_actions: [],
    blocked_actions: [],
    requires_approval_for: [],
  };

  return {
    user_id: userId,
    agent_slug: agentSlug,
    ...defaultPerms,
  } as AgentPermissions;
}

export async function checkAgentPermission(
  userId: string,
  agentSlug: string,
  actionType: string
): Promise<{ allowed: boolean; reason?: string }> {
  const permissions = await getAgentPermissions(userId, agentSlug);

  if (!permissions) {
    return { allowed: false, reason: "No permissions found for agent" };
  }

  // Check blocked actions
  if (permissions.blocked_actions?.includes(actionType)) {
    return { allowed: false, reason: `Action ${actionType} is blocked for agent ${agentSlug}` };
  }

  // Check allowed actions (if specified, must be in list)
  if (permissions.allowed_actions && permissions.allowed_actions.length > 0) {
    if (!permissions.allowed_actions.includes(actionType)) {
      return { allowed: false, reason: `Action ${actionType} is not in allowed list for agent ${agentSlug}` };
    }
  }

  // Check domain-specific permissions
  if (actionType.startsWith("clinical.") && !permissions.can_clinical_actions) {
    return { allowed: false, reason: `Agent ${agentSlug} cannot perform clinical actions` };
  }

  if (actionType.startsWith("financial.") && !permissions.can_financial_actions) {
    return { allowed: false, reason: `Agent ${agentSlug} cannot perform financial actions` };
  }

  if (actionType.startsWith("email.") && !permissions.can_email) {
    return { allowed: false, reason: `Agent ${agentSlug} cannot send emails` };
  }

  if (actionType.startsWith("calendar.") && !permissions.can_scheduling) {
    return { allowed: false, reason: `Agent ${agentSlug} cannot perform scheduling actions` };
  }

  if (actionType.startsWith("file.") && !permissions.can_file_operations) {
    return { allowed: false, reason: `Agent ${agentSlug} cannot perform file operations` };
  }

  return { allowed: true };
}

