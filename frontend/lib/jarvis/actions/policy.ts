import { supabaseServer } from "@/lib/supabase/server";
import type { ActionPolicy, ActionRequest, ActionDomain, ActionType } from "./types";

export async function getActionPolicy(
  userId: string,
  domain: ActionDomain,
  actionType: ActionType
): Promise<ActionPolicy | null> {
  const { data } = await supabaseServer
    .from("jarvis_action_policies")
    .select("*")
    .eq("user_id", userId)
    .eq("domain", domain)
    .eq("action_type", actionType)
    .single();

  if (data) {
    return data as ActionPolicy;
  }

  // Return default policy if none exists
  return getDefaultPolicy(domain, actionType, userId);
}

function getDefaultPolicy(
  domain: ActionDomain,
  actionType: ActionType,
  userId: string
): ActionPolicy {
  // Default policies based on domain and action type
  const defaults: Record<string, Partial<ActionPolicy>> = {
    // Clinical actions - always require MD review
    "clinical.task.create": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
      requires_md_review: true,
    },
    "clinical.note.add": {
      autonomy_level: "SUGGEST_ONLY",
      requires_approval: true,
      requires_md_review: true,
    },
    "clinical.order.queue": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
      requires_md_review: true,
    },
    "clinical.refill.queue": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
      requires_md_review: true,
    },
    "clinical.appointment.schedule": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
      requires_md_review: false,
    },
    // Financial actions - require explicit consent
    "financial.transaction.categorize": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
      requires_explicit_consent: false,
    },
    "financial.entity.allocate": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
      requires_explicit_consent: true,
    },
    "financial.tax.prep": {
      autonomy_level: "SUGGEST_ONLY",
      requires_approval: true,
      requires_explicit_consent: true,
    },
    "financial.reminder.create": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    // Email actions
    "email.send": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
    },
    "email.draft": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "email.triage": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "email.label": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    // Calendar actions
    "calendar.create": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
    },
    "calendar.update": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
    },
    "calendar.cancel": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
    },
    "calendar.move": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    // File actions
    "file.move": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "file.rename": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "file.tag": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "file.archive": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "file.delete": {
      autonomy_level: "ASK_THEN_ACT",
      requires_approval: true,
    },
    // Ops actions
    "ops.dashboard.update": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "ops.flag.set": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
    "ops.status.update": {
      autonomy_level: "AUTO_ACT",
      requires_approval: false,
    },
  };

  const key = `${domain}.${actionType}`;
  const defaultPolicy = defaults[actionType] || {
    autonomy_level: "ASK_THEN_ACT" as const,
    requires_approval: true,
  };

  return {
    user_id: userId,
    domain,
    action_type: actionType,
    autonomy_level: defaultPolicy.autonomy_level || "ASK_THEN_ACT",
    requires_approval: defaultPolicy.requires_approval ?? true,
    requires_md_review: defaultPolicy.requires_md_review ?? false,
    requires_explicit_consent: defaultPolicy.requires_explicit_consent ?? false,
    conditions: defaultPolicy.conditions,
  };
}

export async function checkActionAllowed(
  userId: string,
  request: ActionRequest
): Promise<{
  allowed: boolean;
  policy: ActionPolicy;
  reason?: string;
}> {
  const policy = await getActionPolicy(userId, request.domain, request.action_type);

  // Check conditions
  if (policy.conditions) {
    // Check time-based conditions (e.g., business hours)
    if (policy.conditions.business_hours_only) {
      const hour = new Date().getHours();
      if (hour < 9 || hour > 17) {
        return {
          allowed: false,
          policy,
          reason: "Action only allowed during business hours",
        };
      }
    }
  }

  return {
    allowed: true,
    policy,
  };
}

