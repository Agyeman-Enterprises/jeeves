import { supabaseServer } from "@/lib/supabase/server";
import type { AgentLock, LockType } from "./types";

export async function acquireLock(
  resourceType: string,
  resourceId: string,
  agentSlug: string,
  lockType: LockType,
  durationSeconds: number = 300
): Promise<boolean> {
  // Use the database function for atomic lock acquisition
  const { data, error } = await (supabaseServer as any).rpc("jarvis_acquire_lock", {
    p_resource_type: resourceType,
    p_resource_id: resourceId,
    p_agent_slug: agentSlug,
    p_lock_type: lockType,
    p_duration_seconds: durationSeconds,
  });

  if (error) {
    throw new Error(`Failed to acquire lock: ${error.message}`);
  }

  return data as boolean;
}

export async function releaseLock(
  resourceType: string,
  resourceId: string,
  agentSlug: string
): Promise<void> {
  await (supabaseServer as any).rpc("jarvis_release_lock", {
    p_resource_type: resourceType,
    p_resource_id: resourceId,
    p_agent_slug: agentSlug,
  });
}

export async function checkLock(
  resourceType: string,
  resourceId: string
): Promise<AgentLock | null> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_locks")
    .select("*")
    .eq("resource_type", resourceType)
    .eq("resource_id", resourceId)
    .gt("expires_at", new Date().toISOString())
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      // No lock found
      return null;
    }
    throw new Error(`Failed to check lock: ${error.message}`);
  }

  return data as AgentLock;
}

export async function releaseExpiredLocks(): Promise<number> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_locks")
    .delete()
    .lt("expires_at", new Date().toISOString())
    .select();

  if (error) {
    throw new Error(`Failed to release expired locks: ${error.message}`);
  }

  return (data || []).length;
}

