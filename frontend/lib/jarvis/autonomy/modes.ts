import { supabaseServer } from "@/lib/supabase/server";
import type { AutonomyMode, DomainAutonomy, AgentAutonomy, TaskAutonomy } from "./types";

export async function getAutonomyMode(
  userId: string,
  domain?: string,
  agentSlug?: string,
  actionType?: string
): Promise<AutonomyMode> {
  // 1. Check task-specific override (highest priority)
  if (actionType) {
    const taskAutonomy = await getTaskAutonomy(userId, actionType);
    if (taskAutonomy) {
      return taskAutonomy.autonomy_mode;
    }
  }

  // 2. Check agent-specific override
  if (agentSlug) {
    const agentAutonomy = await getAgentAutonomy(userId, agentSlug);
    if (agentAutonomy?.is_override && agentAutonomy.autonomy_mode) {
      return agentAutonomy.autonomy_mode;
    }
  }

  // 3. Check domain-specific settings
  if (domain) {
    const domainAutonomy = await getDomainAutonomy(userId, domain);
    if (domainAutonomy) {
      return domainAutonomy.current_mode;
    }
  }

  // 4. Fall back to global mode
  const globalSettings = await getGlobalAutonomySettings(userId);
  return globalSettings.global_mode;
}

export async function getGlobalAutonomySettings(userId: string) {
  const { data } = await supabaseServer
    .from("jarvis_autonomy_settings")
    .select("*")
    .eq("user_id", userId)
    .single();

  if (data) {
    return data as any;
  }

  // Create default settings
  return createDefaultAutonomySettings(userId);
}

async function createDefaultAutonomySettings(userId: string) {
  const { data } = await supabaseServer
    .from("jarvis_autonomy_settings")
    .insert({
      user_id: userId,
      global_mode: "COLLABORATIVE",
      behavior_score: 0.5,
      auto_calibration_enabled: true,
    } as any)
    .select()
    .single();

  return data as any;
}

export async function getDomainAutonomy(
  userId: string,
  domain: string
): Promise<DomainAutonomy | null> {
  const { data } = await supabaseServer
    .from("jarvis_domain_autonomy")
    .select("*")
    .eq("user_id", userId)
    .eq("domain", domain)
    .single();

  if (data) {
    return data as DomainAutonomy;
  }

  // Create default domain autonomy
  return createDefaultDomainAutonomy(userId, domain);
}

async function createDefaultDomainAutonomy(
  userId: string,
  domain: string
): Promise<DomainAutonomy> {
  const defaults: Record<string, Partial<DomainAutonomy>> = {
    clinical: {
      allowed_modes: ["ASSISTIVE", "COLLABORATIVE"],
      default_mode: "COLLABORATIVE",
      current_mode: "COLLABORATIVE",
      rules: {
        never_autonomous: true,
        always_preview_patient_facing: true,
        always_escalate_high_risk: true,
      },
    },
    financial: {
      allowed_modes: ["ASSISTIVE", "COLLABORATIVE"],
      default_mode: "COLLABORATIVE",
      current_mode: "COLLABORATIVE",
      rules: {
        delegated_allowed_for_categorization: true,
        never_autonomous_for_transactions: true,
        tax_actions_always_manual: true,
      },
    },
    operations: {
      allowed_modes: ["COLLABORATIVE", "DELEGATED", "AUTONOMOUS"],
      default_mode: "DELEGATED",
      current_mode: "DELEGATED",
      rules: {
        scheduling_rules_configurable: true,
        can_manage_ma_tasks_autonomously: true,
      },
    },
    communications: {
      allowed_modes: ["COLLABORATIVE", "DELEGATED"],
      default_mode: "COLLABORATIVE",
      current_mode: "COLLABORATIVE",
      rules: {
        patient_communication: "COLLABORATIVE",
        staff_communication: "DELEGATED",
        internal_ai_communication: "AUTONOMOUS",
      },
    },
    files: {
      allowed_modes: ["DELEGATED", "AUTONOMOUS"],
      default_mode: "DELEGATED",
      current_mode: "DELEGATED",
      rules: {
        never_delete_without_consent: true,
        auto_organization_allowed: true,
      },
    },
    internal_ai: {
      allowed_modes: ["AUTONOMOUS"],
      default_mode: "AUTONOMOUS",
      current_mode: "AUTONOMOUS",
      rules: {
        fully_autonomous: true,
        pure_computation: true,
      },
    },
  };

  const defaultConfig = defaults[domain] || {
    allowed_modes: ["COLLABORATIVE"],
    default_mode: "COLLABORATIVE",
    current_mode: "COLLABORATIVE",
  };

  const { data } = await supabaseServer
    .from("jarvis_domain_autonomy")
    .insert({
      user_id: userId,
      domain,
      ...defaultConfig,
    } as any)
    .select()
    .single();

  return data as DomainAutonomy;
}

export async function getAgentAutonomy(
  userId: string,
  agentSlug: string
): Promise<AgentAutonomy | null> {
  const { data } = await supabaseServer
    .from("jarvis_agent_autonomy")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug)
    .single();

  if (data) {
    return data as AgentAutonomy;
  }

  return null;
}

export async function getTaskAutonomy(
  userId: string,
  actionType: string
): Promise<TaskAutonomy | null> {
  const { data } = await supabaseServer
    .from("jarvis_task_autonomy")
    .select("*")
    .eq("user_id", userId)
    .eq("action_type", actionType)
    .single();

  if (data) {
    return data as TaskAutonomy;
  }

  return null;
}

export async function setGlobalAutonomyMode(
  userId: string,
  mode: AutonomyMode
): Promise<void> {
  const updateData: Record<string, any> = {
    global_mode: mode,
    updated_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_autonomy_settings")
    .update(updateData)
    .eq("user_id", userId);
}

export async function setDomainAutonomyMode(
  userId: string,
  domain: string,
  mode: AutonomyMode
): Promise<void> {
  // Verify mode is allowed for this domain
  const domainAutonomy = await getDomainAutonomy(userId, domain);
  if (!domainAutonomy.allowed_modes.includes(mode)) {
    throw new Error(`Mode ${mode} is not allowed for domain ${domain}`);
  }

  const updateData: Record<string, any> = {
    current_mode: mode,
    updated_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_domain_autonomy")
    .update(updateData)
    .eq("user_id", userId)
    .eq("domain", domain);
}

export async function setAgentAutonomyMode(
  userId: string,
  agentSlug: string,
  mode: AutonomyMode | null,
  isOverride: boolean = true,
  reason?: string
): Promise<void> {
  if (mode === null) {
    // Remove override
    await (supabaseServer as any)
      .from("jarvis_agent_autonomy")
      .delete()
      .eq("user_id", userId)
      .eq("agent_slug", agentSlug);
    return;
  }

  const insertData: Record<string, any> = {
    user_id: userId,
    agent_slug: agentSlug,
    autonomy_mode: mode,
    is_override: isOverride,
    reason,
    updated_at: new Date().toISOString(),
  };

  await (supabaseServer as any)
    .from("jarvis_agent_autonomy")
    .upsert(insertData, { onConflict: "user_id,agent_slug" });
}

export async function setTaskAutonomyMode(
  userId: string,
  actionType: string,
  mode: AutonomyMode,
  isOverride: boolean = true,
  reason?: string
): Promise<void> {
  const insertData: Record<string, any> = {
    user_id: userId,
    action_type: actionType,
    autonomy_mode: mode,
    is_override: isOverride,
    reason,
    updated_at: new Date().toISOString(),
  };

  await (supabaseServer as any)
    .from("jarvis_task_autonomy")
    .upsert(insertData, { onConflict: "user_id,action_type" });
}

