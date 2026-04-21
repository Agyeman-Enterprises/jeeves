import { supabaseServer } from "@/lib/supabase/server";
import type { AgentMessage, AgentIntent } from "./types";

export async function sendAgentMessage(
  fromAgent: string,
  toAgent: string | null,
  intent: AgentIntent,
  payload: Record<string, any>
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_messages")
    .insert({
      from_agent: fromAgent,
      to_agent: toAgent,
      intent,
      payload,
      status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to send agent message: ${error?.message}`);
  }

  return (data as any).id;
}

export async function broadcastMessage(
  fromAgent: string,
  intent: AgentIntent,
  payload: Record<string, any>
): Promise<string> {
  return sendAgentMessage(fromAgent, null, intent, payload);
}

export async function acknowledgeMessage(messageId: string, agentSlug: string): Promise<void> {
  const updateData: Record<string, any> = {
    status: "ACKNOWLEDGED",
    acknowledged_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_messages")
    .update(updateData)
    .eq("id", messageId);
}

export async function resolveMessage(messageId: string): Promise<void> {
  const updateData: Record<string, any> = {
    status: "RESOLVED",
    resolved_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_messages")
    .update(updateData)
    .eq("id", messageId);
}

export async function getPendingMessages(
  agentSlug?: string,
  intent?: AgentIntent
): Promise<AgentMessage[]> {
  let query = supabaseServer
    .from("jarvis_agent_messages")
    .select("*")
    .eq("status", "PENDING")
    .order("created_at", { ascending: true });

  if (agentSlug) {
    query = query.or(`to_agent.eq.${agentSlug},to_agent.is.null`);
  }

  if (intent) {
    query = query.eq("intent", intent);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get pending messages: ${error.message}`);
  }

  return (data || []) as AgentMessage[];
}

// Helper functions for common message patterns
export async function requestHelp(
  fromAgent: string,
  taskDescription: string,
  requiredCapabilities: string[],
  context: Record<string, any>
): Promise<string> {
  return sendAgentMessage(fromAgent, null, "HELP_REQUEST", {
    task_description: taskDescription,
    required_capabilities: requiredCapabilities,
    context,
  });
}

export async function delegateTask(
  fromAgent: string,
  toAgent: string,
  taskId: string,
  reason: string,
  context: Record<string, any>
): Promise<string> {
  return sendAgentMessage(fromAgent, toAgent, "DELEGATE", {
    task_id: taskId,
    reason,
    context,
  });
}

export async function reportCompletion(
  fromAgent: string,
  taskId: string,
  result: Record<string, any>
): Promise<string> {
  return broadcastMessage(fromAgent, "TASK_COMPLETE", {
    task_id: taskId,
    result,
  });
}

export async function reportConflict(
  fromAgent: string,
  conflictDescription: string,
  otherAgents: string[],
  position: Record<string, any>
): Promise<string> {
  return sendAgentMessage(fromAgent, null, "CONFLICT", {
    conflict_description: conflictDescription,
    other_agents: otherAgents,
    position,
  });
}

