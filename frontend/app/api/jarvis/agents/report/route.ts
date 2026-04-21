import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import type { ReportResultRequest } from "@/lib/jarvis/agents/lifecycle";
import { isRetryableError, calculateBackoff } from "@/lib/jarvis/agents/lifecycle";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ReportResultRequest;
    const { run_id, status, result, error, logs } = body;

    // Get the run to check attempt_count and agent_slug
    const { data: run, error: fetchError } = await supabaseServer
      .from("jarvis_agent_runs")
      .select("agent_slug, attempt_count, max_attempts, last_error_kind")
      .eq("id", run_id)
      .single();

    if (fetchError || !run) {
      return NextResponse.json({ error: "Run not found" }, { status: 404 });
    }

    const agentSlug = (run as any).agent_slug;
    const attemptCount = (run as any).attempt_count || 0;
    const maxAttempts = (run as any).max_attempts || 3;
    const lastErrorKind = (run as any).last_error_kind;

    const now = new Date().toISOString();
    let newStatus: "COMPLETED" | "FAILED" | "RETRYING" = status;
    let nextAttemptAt: string | null = null;

    if (status === "FAILED") {
      // Check if we should retry
      if (attemptCount < maxAttempts && isRetryableError(lastErrorKind)) {
        newStatus = "RETRYING";
        nextAttemptAt = calculateBackoff(attemptCount).toISOString();
      } else {
        newStatus = "FAILED";
      }

      // Increment failure streak for agent
      const { data: agentData } = await supabaseServer
        .from("jarvis_agents")
        .select("failure_streak")
        .eq("slug", agentSlug)
        .single();
      
      const currentFailureStreak = (agentData as any)?.failure_streak || 0;
      const failureData: Record<string, any> = {
        failure_streak: currentFailureStreak + 1,
        success_streak: 0,
      };
      await (supabaseServer as any)
        .from("jarvis_agents")
        .update(failureData)
        .eq("slug", agentSlug);
    } else if (status === "COMPLETED") {
      // Reset failure streak, increment success streak
      const { data: agentData } = await supabaseServer
        .from("jarvis_agents")
        .select("success_streak")
        .eq("slug", agentSlug)
        .single();
      
      const currentSuccessStreak = (agentData as any)?.success_streak || 0;
      const successData: Record<string, any> = {
        failure_streak: 0,
        success_streak: currentSuccessStreak + 1,
      };
      await (supabaseServer as any)
        .from("jarvis_agents")
        .update(successData)
        .eq("slug", agentSlug);

      // Update plan step if planStepId exists
      const { data: runData } = await supabaseServer
        .from("jarvis_agent_runs")
        .select("plan_step_id")
        .eq("id", run_id)
        .single();

      if (runData && (runData as any).plan_step_id) {
        const stepData: Record<string, any> = {
          status: "COMPLETED",
          result: result,
        };
        await (supabaseServer as any)
          .from("jarvis_plan_steps")
          .update(stepData)
          .eq("id", (runData as any).plan_step_id);
      }
    }

    // Update the run
    const runUpdateData: Record<string, any> = {
      status: newStatus,
      result: result || null,
      error: error || null,
      logs: logs || null,
      finished_at: now,
      next_attempt_at: nextAttemptAt,
    };
    const { error: updateError } = await (supabaseServer as any)
      .from("jarvis_agent_runs")
      .update(runUpdateData)
      .eq("id", run_id);

    if (updateError) {
      console.error("Failed to update run:", updateError);
      return NextResponse.json({ error: "Failed to update run" }, { status: 500 });
    }

    return NextResponse.json({ ok: true, status: newStatus });
  } catch (error: any) {
    console.error("Report result error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

