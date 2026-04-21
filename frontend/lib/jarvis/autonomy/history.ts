import { supabaseServer } from "@/lib/supabase/server";
import type { AutonomyHistory, AutonomyMode, TriggeredBy } from "./types";

export async function logAutonomyChange(
  userId: string,
  change: {
    domain?: string;
    agent_slug?: string;
    action_type?: string;
    previous_mode?: AutonomyMode;
    new_mode: AutonomyMode;
    reason?: string;
    triggered_by?: TriggeredBy;
    confidence_score?: number;
  }
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_autonomy_history")
    .insert({
      user_id: userId,
      domain: change.domain,
      agent_slug: change.agent_slug,
      action_type: change.action_type,
      previous_mode: change.previous_mode,
      new_mode: change.new_mode,
      reason: change.reason,
      triggered_by: change.triggered_by || "system",
      confidence_score: change.confidence_score,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to log autonomy change: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getAutonomyHistory(
  userId: string,
  filters?: {
    domain?: string;
    agent_slug?: string;
    limit?: number;
  }
): Promise<AutonomyHistory[]> {
  let query = supabaseServer
    .from("jarvis_autonomy_history")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (filters?.domain) {
    query = query.eq("domain", filters.domain);
  }

  if (filters?.agent_slug) {
    query = query.eq("agent_slug", filters.agent_slug);
  }

  if (filters?.limit) {
    query = query.limit(filters.limit);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get autonomy history: ${error.message}`);
  }

  return (data || []) as AutonomyHistory[];
}

