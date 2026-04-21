import { supabaseServer } from "@/lib/supabase/server";
import type { AgentResourceAllocation } from "./types";
import { getAgentPerformance } from "../meta/agents";

export async function allocateAgentResources(
  userId: string,
  agentSlug: string,
  periodStart: Date,
  periodEnd: Date
): Promise<string> {
  // Get agent performance data
  const performance = await getAgentPerformance(userId, agentSlug, 1);
  const latestPerf = performance.length > 0 ? performance[0] : null;

  // Get current agent runs
  const { data: runs } = await supabaseServer
    .from("jarvis_agent_runs")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug)
    .gte("created_at", periodStart.toISOString())
    .lte("created_at", periodEnd.toISOString());

  const allocatedTasks = (runs || []).length;
  const completedTasks = (runs || []).filter((r: any) => r.status === "COMPLETED").length;
  const failedTasks = (runs || []).filter((r: any) => r.status === "FAILED").length;

  // Calculate average success probability
  const successRate = latestPerf?.success_rate || (allocatedTasks > 0 ? completedTasks / allocatedTasks : 0.5);

  // Calculate current load percentage
  const maxCapacity = 100; // Simplified - would be based on agent capacity
  const currentLoad = Math.min(100, (allocatedTasks / maxCapacity) * 100);

  // Calculate priority distribution
  const priorityDistribution = calculatePriorityDistribution(runs || []);

  // Determine retry strategy
  const retryStrategy = {
    max_retries: latestPerf?.average_retries ? Math.ceil(latestPerf.average_retries) + 1 : 3,
    backoff_multiplier: 2,
    retry_on_failure: true,
  };

  // Determine off-peak allocation
  const offPeakAllocation = {
    enabled: currentLoad > 80,
    threshold: 80,
    move_low_priority: currentLoad > 80,
  };

  const { data, error } = await supabaseServer
    .from("jarvis_agent_resource_allocations")
    .insert({
      user_id: userId,
      agent_slug: agentSlug,
      allocation_period_start: periodStart.toISOString(),
      allocation_period_end: periodEnd.toISOString(),
      allocated_tasks: allocatedTasks,
      completed_tasks: completedTasks,
      failed_tasks: failedTasks,
      average_success_probability: successRate,
      current_load_percentage: currentLoad,
      priority_distribution: priorityDistribution,
      retry_strategy: retryStrategy,
      off_peak_allocation: offPeakAllocation,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to allocate agent resources: ${error?.message}`);
  }

  return (data as any).id;
}

function calculatePriorityDistribution(runs: any[]): Record<string, any> {
  const distribution: Record<string, number> = {
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0,
  };

  runs.forEach((run: any) => {
    const priority = run.priority || "MEDIUM";
    distribution[priority] = (distribution[priority] || 0) + 1;
  });

  return distribution;
}

export async function getAgentResourceAllocation(
  userId: string,
  agentSlug: string,
  limit: number = 10
): Promise<AgentResourceAllocation[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_resource_allocations")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug)
    .order("allocation_period_start", { ascending: false })
    .limit(limit);

  if (error) {
    throw new Error(`Failed to get agent resource allocation: ${error.message}`);
  }

  return (data || []) as AgentResourceAllocation[];
}

