import { supabaseServer } from "@/lib/supabase/server";
import type { AgentCoordination, CoordinationType } from "./types";

export async function createCoordination(
  planId: string | undefined,
  planStepId: string | undefined,
  fromAgent: string,
  toAgent: string,
  coordinationType: CoordinationType,
  reason?: string,
  payload?: Record<string, any>
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_coordination")
    .insert({
      plan_id: planId,
      plan_step_id: planStepId,
      from_agent: fromAgent,
      to_agent: toAgent,
      coordination_type: coordinationType,
      reason,
      payload,
      status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create coordination: ${error?.message}`);
  }

  return (data as any).id;
}

export async function acceptCoordination(coordinationId: string): Promise<void> {
  const updateData: Record<string, any> = {
    status: "ACCEPTED",
    accepted_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_coordination")
    .update(updateData)
    .eq("id", coordinationId);
}

export async function rejectCoordination(coordinationId: string, reason?: string): Promise<void> {
  const updateData: Record<string, any> = {
    status: "REJECTED",
    accepted_at: new Date().toISOString(),
    payload: { rejection_reason: reason },
  };
  await (supabaseServer as any)
    .from("jarvis_agent_coordination")
    .update(updateData)
    .eq("id", coordinationId);
}

export async function completeCoordination(coordinationId: string): Promise<void> {
  const updateData: Record<string, any> = {
    status: "COMPLETED",
    completed_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_coordination")
    .update(updateData)
    .eq("id", coordinationId);
}

export async function getPendingCoordinations(agentSlug: string): Promise<AgentCoordination[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_coordination")
    .select("*")
    .eq("to_agent", agentSlug)
    .eq("status", "PENDING")
    .order("created_at", { ascending: true });

  if (error) {
    throw new Error(`Failed to get pending coordinations: ${error.message}`);
  }

  return (data || []) as AgentCoordination[];
}

