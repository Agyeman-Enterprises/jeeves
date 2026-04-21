import { supabaseServer } from "@/lib/supabase/server";
import type { AgentLoadPrediction, TimeHorizon } from "./types";

export async function simulateAgentLoad(
  userId: string,
  parameters: Record<string, any>
): Promise<Record<string, any>> {
  const agentSlug = parameters.agent_slug;
  const timeHorizon = (parameters.time_horizon || "1MONTH") as TimeHorizon;

  // Get agent run history
  const { data: agentRuns } = await supabaseServer
    .from("jarvis_agent_runs")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug || "")
    .order("created_at", { ascending: false })
    .limit(500);

  // Get queue status
  const { data: queueItems } = await supabaseServer
    .from("jarvis_agent_queues")
    .select("*")
    .eq("agent_slug", agentSlug || "")
    .eq("status", "QUEUED");

  // Calculate current load
  const pendingRuns = (agentRuns as any[] || []).filter((r: any) => r.status === "PENDING" || r.status === "RUNNING");
  const queuedTasks = (queueItems || []).length;

  // Predict future load
  const avgTasksPerWeek = (agentRuns || []).length / Math.max(4, 1); // Assume 4 weeks of data
  const weeks = getWeeksFromHorizon(timeHorizon);
  const predictedTasks = Math.floor(avgTasksPerWeek * weeks);

  // Estimate processing time
  const avgProcessingTime = calculateAvgProcessingTime(agentRuns || []);
  const predictedLoadHours = (predictedTasks * avgProcessingTime) / 60;

  // Calculate overload probability
  const maxCapacity = parameters.max_capacity_per_week || 40; // Default 40 tasks per week
  const overloadProbability = (predictedTasks / (maxCapacity * weeks)) > 1 ? 1 : (predictedTasks / (maxCapacity * weeks));

  const recommendations: string[] = [];
  if (overloadProbability > 0.9) {
    recommendations.push("Agent will be severely overloaded");
    recommendations.push("Consider redistributing tasks to other agents");
    recommendations.push("Consider adding more instances of this agent");
  } else if (overloadProbability > 0.75) {
    recommendations.push("Agent approaching capacity");
    recommendations.push("Monitor queue depth closely");
  }

  return {
    agent_slug: agentSlug,
    time_horizon: timeHorizon,
    current_pending_tasks: pendingRuns.length,
    current_queued_tasks: queuedTasks,
    predicted_tasks: predictedTasks,
    predicted_load_hours: predictedLoadHours,
    overload_probability: overloadProbability,
    recommendations,
    confidence_score: 0.7,
  };
}

function calculateAvgProcessingTime(agentRuns: any[]): number {
  // Calculate average processing time in minutes
  const completedRuns = agentRuns.filter((r) => r.status === "COMPLETED" && r.started_at && r.finished_at);
  
  if (completedRuns.length === 0) {
    return 5; // Default 5 minutes
  }

  const totalTime = completedRuns.reduce((sum, r) => {
    const start = new Date(r.started_at).getTime();
    const end = new Date(r.finished_at).getTime();
    return sum + (end - start) / 1000 / 60; // Convert to minutes
  }, 0);

  return totalTime / completedRuns.length;
}

function getWeeksFromHorizon(horizon: TimeHorizon): number {
  switch (horizon) {
    case "1WEEK":
      return 1;
    case "1MONTH":
      return 4;
    case "3MONTHS":
      return 12;
    case "6MONTHS":
      return 26;
    case "1YEAR":
      return 52;
    default:
      return 4;
  }
}

