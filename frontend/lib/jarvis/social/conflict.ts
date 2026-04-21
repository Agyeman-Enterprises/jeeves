import { supabaseServer } from "@/lib/supabase/server";
import type { AgentConflict, ConflictType } from "./types";

export async function createConflict(
  userId: string,
  conflictType: ConflictType,
  agentsInvolved: string[],
  conflictDescription: string,
  agentPositions: Record<string, any>
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_conflicts")
    .insert({
      user_id: userId,
      conflict_type: conflictType,
      agents_involved: agentsInvolved,
      conflict_description: conflictDescription,
      agent_positions: agentPositions,
      resolution_status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create conflict: ${error?.message}`);
  }

  return (data as any).id;
}

export async function resolveConflict(
  conflictId: string,
  resolvedBy: "jarvis" | string,
  resolution: Record<string, any>
): Promise<void> {
  const updateData: Record<string, any> = {
    resolution_status: "RESOLVED",
    resolved_by: resolvedBy,
    resolution,
    resolved_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_conflicts")
    .update(updateData)
    .eq("id", conflictId);
}

export async function escalateConflict(conflictId: string): Promise<void> {
  const updateData: Record<string, any> = {
    resolution_status: "ESCALATED",
    resolved_by: "user",
  };
  await (supabaseServer as any)
    .from("jarvis_agent_conflicts")
    .update(updateData)
    .eq("id", conflictId);
}

export async function getPendingConflicts(userId: string): Promise<AgentConflict[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_conflicts")
    .select("*")
    .eq("user_id", userId)
    .eq("resolution_status", "PENDING")
    .order("created_at", { ascending: true });

  if (error) {
    throw new Error(`Failed to get pending conflicts: ${error.message}`);
  }

  return (data || []) as AgentConflict[];
}

// Conflict resolution logic
export async function resolveConflictAutomatically(
  conflictId: string,
  conflict: AgentConflict
): Promise<{ resolved: boolean; resolution?: Record<string, any> }> {
  // Use behavior models, persona context, safety rules, domain priorities
  // This is a simplified version - in production, this would use the full decision engine

  switch (conflict.conflict_type) {
    case "SCHEDULING":
      // Prioritize clinical urgency
      const clinicalAgent = conflict.agents_involved.find((a) => a.includes("clinical") || a.includes("glp"));
      if (clinicalAgent) {
        return {
          resolved: true,
          resolution: {
            decision: "Favor clinical urgency",
            chosen_agent: clinicalAgent,
            reasoning: "Clinical needs take priority over operational efficiency",
          },
        };
      }
      break;

    case "PRIORITY":
      // Use risk assessment
      const highRiskAgent = conflict.agents_involved.find((a) => a.includes("triage") || a.includes("hospitalization"));
      if (highRiskAgent) {
        return {
          resolved: true,
          resolution: {
            decision: "Favor high-risk agent",
            chosen_agent: highRiskAgent,
            reasoning: "High-risk clinical situations take priority",
          },
        };
      }
      break;

    case "RESOURCE":
      // First come, first served with priority adjustment
      return {
        resolved: true,
        resolution: {
          decision: "Queue with priority",
          reasoning: "Resources allocated based on task priority and arrival time",
        },
      };

    default:
      // Escalate to user
      await escalateConflict(conflictId);
      return { resolved: false };
  }

  return { resolved: false };
}

