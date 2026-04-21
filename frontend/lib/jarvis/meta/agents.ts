import { supabaseServer } from "@/lib/supabase/server";
import type { AgentPerformance, TrustLevel, AutonomyAdjustment } from "./types";

export async function evaluateAgentPerformance(
  userId: string,
  agentSlug: string,
  periodStart: Date,
  periodEnd: Date
): Promise<string> {
  // Get agent runs for this period
  const { data: runsData } = await supabaseServer
    .from("jarvis_agent_runs")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug)
    .gte("created_at", periodStart.toISOString())
    .lte("created_at", periodEnd.toISOString());

  if (!runsData || runsData.length === 0) {
    throw new Error("No agent runs found for evaluation period");
  }

  const runs = runsData as any[];
  const totalTasks = runs.length;
  const successfulTasks = runs.filter((r: any) => r.status === "COMPLETED").length;
  const failedTasks = runs.filter((r: any) => r.status === "FAILED").length;
  const successRate = totalTasks > 0 ? successfulTasks / totalTasks : 0;

  // Calculate average retries
  const retries = runs.map((r: any) => r.retry_count || 0);
  const averageRetries = retries.length > 0 ? retries.reduce((a, b) => a + b, 0) / retries.length : 0;

  // Calculate average completion time
  const completionTimes = runs
    .filter((r: any) => r.status === "COMPLETED" && r.completed_at && r.created_at)
    .map((r: any) => {
      const start = new Date(r.created_at).getTime();
      const end = new Date(r.completed_at).getTime();
      return (end - start) / 1000; // seconds
    });
  const averageCompletionTime = completionTimes.length > 0
    ? completionTimes.reduce((a, b) => a + b, 0) / completionTimes.length
    : null;

  // Count error types
  const errorTypes: Record<string, number> = {};
  runs.filter((r: any) => r.status === "FAILED" && r.error).forEach((r: any) => {
    const errorType = r.error?.split(":")[0] || "UNKNOWN";
    errorTypes[errorType] = (errorTypes[errorType] || 0) + 1;
  });

  // Calculate performance score (-1 to 1)
  // Higher success rate = higher score
  // Lower retries = higher score
  // Lower completion time = higher score (if available)
  let performanceScore = successRate * 2 - 1; // Convert 0-1 to -1 to 1
  performanceScore -= averageRetries * 0.1; // Penalize retries
  performanceScore = Math.max(-1, Math.min(1, performanceScore));

  // Determine trust level
  const trustLevel: TrustLevel = performanceScore > 0.7 ? "HIGH" : performanceScore > 0.3 ? "MEDIUM" : "LOW";

  // Determine autonomy adjustment
  const autonomyAdjustment: AutonomyAdjustment =
    performanceScore > 0.5 ? "INCREASED" : performanceScore < -0.3 ? "DECREASED" : "UNCHANGED";

  // Create performance record
  const { data, error } = await supabaseServer
    .from("jarvis_agent_performance")
    .insert({
      user_id: userId,
      agent_slug: agentSlug,
      performance_period_start: periodStart.toISOString(),
      performance_period_end: periodEnd.toISOString(),
      total_tasks: totalTasks,
      successful_tasks: successfulTasks,
      failed_tasks: failedTasks,
      average_retries: averageRetries,
      average_completion_time_seconds: averageCompletionTime,
      error_types: errorTypes,
      success_rate: successRate,
      performance_score: performanceScore,
      trust_level: trustLevel,
      autonomy_adjustment: autonomyAdjustment,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to evaluate agent performance: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getAgentPerformance(
  userId: string,
  agentSlug: string,
  limit: number = 10
): Promise<AgentPerformance[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_agent_performance")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug)
    .order("performance_period_end", { ascending: false })
    .limit(limit);

  if (error) {
    throw new Error(`Failed to get agent performance: ${error.message}`);
  }

  return (data || []) as AgentPerformance[];
}

export async function getAgentTrustLevel(userId: string, agentSlug: string): Promise<TrustLevel> {
  const { data } = await supabaseServer
    .from("jarvis_agent_performance")
    .select("trust_level")
    .eq("user_id", userId)
    .eq("agent_slug", agentSlug)
    .order("performance_period_end", { ascending: false })
    .limit(1)
    .single();

  if (data) {
    return (data as any).trust_level || "MEDIUM";
  }

  return "MEDIUM"; // Default trust level
}

