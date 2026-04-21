import { supabaseServer } from "@/lib/supabase/server";
import type { AgentQueueItem } from "./types";

export async function enqueueTask(
  agentSlug: string,
  agentRunId: string,
  priority: number = 1
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_queues")
    .insert({
      agent_slug: agentSlug,
      agent_run_id: agentRunId,
      priority,
      status: "QUEUED",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to enqueue task: ${error?.message}`);
  }

  return (data as any).id;
}

export async function dequeueTask(agentSlug: string): Promise<AgentQueueItem | null> {
  // Get the highest priority queued task for this agent
  const { data, error } = await supabaseServer
    .from("jarvis_agent_queues")
    .select("*")
    .eq("agent_slug", agentSlug)
    .eq("status", "QUEUED")
    .order("priority", { ascending: false })
    .order("queued_at", { ascending: true })
    .limit(1)
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      // No tasks in queue
      return null;
    }
    throw new Error(`Failed to dequeue task: ${error.message}`);
  }

  // Mark as processing
  const updateData: Record<string, any> = {
    status: "PROCESSING",
    started_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_queues")
    .update(updateData)
    .eq("id", (data as any).id);

  return data as AgentQueueItem;
}

export async function completeQueuedTask(queueId: string): Promise<void> {
  const updateData: Record<string, any> = {
    status: "COMPLETED",
    completed_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_queues")
    .update(updateData)
    .eq("id", queueId);
}

export async function failQueuedTask(queueId: string): Promise<void> {
  const updateData: Record<string, any> = {
    status: "FAILED",
    completed_at: new Date().toISOString(),
  };
  await (supabaseServer as any)
    .from("jarvis_agent_queues")
    .update(updateData)
    .eq("id", queueId);
}

export async function getQueueStatus(agentSlug: string): Promise<{
  queued: number;
  processing: number;
  completed: number;
  failed: number;
}> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_queues")
    .select("status")
    .eq("agent_slug", agentSlug);

  if (error) {
    throw new Error(`Failed to get queue status: ${error.message}`);
  }

  const tasks = (data || []) as { status: string }[];

  return {
    queued: tasks.filter((t) => t.status === "QUEUED").length,
    processing: tasks.filter((t) => t.status === "PROCESSING").length,
    completed: tasks.filter((t) => t.status === "COMPLETED").length,
    failed: tasks.filter((t) => t.status === "FAILED").length,
  };
}

