import { supabaseServer } from "@/lib/supabase/server";
import type { KillSwitch, KillSwitchType, KillSwitchStatus } from "./types";

export async function checkKillSwitch(
  userId: string,
  domain?: string,
  agentSlug?: string
): Promise<{ blocked: boolean; reason?: string; switchType?: KillSwitchType }> {
  // Check full shutdown first
  const { data: fullShutdown } = await supabaseServer
    .from("jarvis_kill_switches")
    .select("*")
    .eq("user_id", userId)
    .eq("switch_type", "FULL_SHUTDOWN")
    .eq("status", "ACTIVE")
    .or("expires_at.is.null,expires_at.gt." + new Date().toISOString())
    .single();

  if (fullShutdown) {
    return {
      blocked: true,
      reason: "Full shutdown is active. All actions are blocked.",
      switchType: "FULL_SHUTDOWN",
    };
  }

  // Check automation freeze
  const { data: automationFreeze } = await supabaseServer
    .from("jarvis_kill_switches")
    .select("*")
    .eq("user_id", userId)
    .eq("switch_type", "AUTOMATION_FREEZE")
    .eq("status", "ACTIVE")
    .or("expires_at.is.null,expires_at.gt." + new Date().toISOString())
    .single();

  if (automationFreeze) {
    return {
      blocked: true,
      reason: "Automation freeze is active. All automated actions are blocked.",
      switchType: "AUTOMATION_FREEZE",
    };
  }

  // Check domain kill switch
  if (domain) {
    const { data: domainSwitch } = await supabaseServer
      .from("jarvis_kill_switches")
      .select("*")
      .eq("user_id", userId)
      .eq("switch_type", "DOMAIN")
      .eq("target", domain)
      .eq("status", "ACTIVE")
      .or("expires_at.is.null,expires_at.gt." + new Date().toISOString())
      .single();

    if (domainSwitch) {
      return {
        blocked: true,
        reason: `Domain kill switch is active for ${domain}. All ${domain} actions are blocked.`,
        switchType: "DOMAIN",
      };
    }
  }

  // Check agent kill switch
  if (agentSlug) {
    const { data: agentSwitch } = await supabaseServer
      .from("jarvis_kill_switches")
      .select("*")
      .eq("user_id", userId)
      .eq("switch_type", "AGENT")
      .eq("target", agentSlug)
      .eq("status", "ACTIVE")
      .or("expires_at.is.null,expires_at.gt." + new Date().toISOString())
      .single();

    if (agentSwitch) {
      return {
        blocked: true,
        reason: `Agent kill switch is active for ${agentSlug}. All actions from this agent are blocked.`,
        switchType: "AGENT",
      };
    }
  }

  return { blocked: false };
}

export async function activateKillSwitch(
  userId: string,
  switchType: KillSwitchType,
  target: string,
  reason?: string,
  expiresAt?: string
): Promise<string> {
  // Deactivate any existing switch of the same type and target
  const deactivateUpdate: Record<string, any> = {
    status: "INACTIVE",
    deactivated_at: new Date().toISOString(),
    deactivated_by: userId,
  };
  await (supabaseServer as any)
    .from("jarvis_kill_switches")
    .update(deactivateUpdate)
    .eq("user_id", userId)
    .eq("switch_type", switchType)
    .eq("target", target)
    .eq("status", "ACTIVE");

  // Create new active switch
  const { data, error } = await supabaseServer
    .from("jarvis_kill_switches")
    .insert({
      user_id: userId,
      switch_type: switchType,
      target,
      status: "ACTIVE",
      reason,
      activated_by: userId,
      activated_at: new Date().toISOString(),
      expires_at: expiresAt,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to activate kill switch: ${error?.message}`);
  }

  return (data as any).id;
}

export async function deactivateKillSwitch(
  userId: string,
  switchType: KillSwitchType,
  target: string
): Promise<void> {
  const deactivateUpdate: Record<string, any> = {
    status: "INACTIVE",
    deactivated_at: new Date().toISOString(),
    deactivated_by: userId,
  };
  const { error } = await (supabaseServer as any)
    .from("jarvis_kill_switches")
    .update(deactivateUpdate)
    .eq("user_id", userId)
    .eq("switch_type", switchType)
    .eq("target", target)
    .eq("status", "ACTIVE");

  if (error) {
    throw new Error(`Failed to deactivate kill switch: ${error.message}`);
  }
}

export async function getActiveKillSwitches(userId: string): Promise<KillSwitch[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_kill_switches")
    .select("*")
    .eq("user_id", userId)
    .eq("status", "ACTIVE")
    .or("expires_at.is.null,expires_at.gt." + new Date().toISOString())
    .order("activated_at", { ascending: false });

  if (error) {
    throw new Error(`Failed to get active kill switches: ${error.message}`);
  }

  return (data || []) as KillSwitch[];
}

// Convenience functions for common kill switch operations
export async function freezeAgent(userId: string, agentSlug: string, reason?: string): Promise<string> {
  return activateKillSwitch(userId, "AGENT", agentSlug, reason);
}

export async function freezeDomain(userId: string, domain: string, reason?: string): Promise<string> {
  return activateKillSwitch(userId, "DOMAIN", domain, reason);
}

export async function freezeAutomation(userId: string, reason?: string): Promise<string> {
  return activateKillSwitch(userId, "AUTOMATION_FREEZE", "ALL", reason);
}

export async function fullShutdown(userId: string, reason?: string): Promise<string> {
  return activateKillSwitch(userId, "FULL_SHUTDOWN", "ALL", reason);
}

export async function resumeAgent(userId: string, agentSlug: string): Promise<void> {
  return deactivateKillSwitch(userId, "AGENT", agentSlug);
}

export async function resumeDomain(userId: string, domain: string): Promise<void> {
  return deactivateKillSwitch(userId, "DOMAIN", domain);
}

export async function resumeAutomation(userId: string): Promise<void> {
  return deactivateKillSwitch(userId, "AUTOMATION_FREEZE", "ALL");
}

export async function resumeAll(userId: string): Promise<void> {
  return deactivateKillSwitch(userId, "FULL_SHUTDOWN", "ALL");
}

