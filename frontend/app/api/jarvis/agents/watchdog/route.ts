import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

export async function POST(req: NextRequest) {
  try {
    const now = new Date().toISOString();
    const thirtyMinutesAgo = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000).toISOString();

    // 1. Detect stuck RUNNING runs (running for >30 minutes)
    const { data: stuckRuns } = await supabaseServer
      .from("jarvis_agent_runs")
      .select("id, attempt_count, max_attempts")
      .eq("status", "RUNNING")
      .lt("started_at", thirtyMinutesAgo);

    if (stuckRuns && stuckRuns.length > 0) {
      for (const run of stuckRuns) {
        const attemptCount = (run as any).attempt_count || 0;
        const maxAttempts = (run as any).max_attempts || 3;

        if (attemptCount < maxAttempts) {
          // Mark as RETRYING
          const retryData: Record<string, any> = {
            status: "RETRYING",
            next_attempt_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
          };
          await (supabaseServer as any)
            .from("jarvis_agent_runs")
            .update(retryData)
            .eq("id", (run as any).id);
        } else {
          // Mark as FAILED
          const failedData: Record<string, any> = {
            status: "FAILED",
            error: "Run timed out after maximum attempts",
          };
          await (supabaseServer as any)
            .from("jarvis_agent_runs")
            .update(failedData)
            .eq("id", (run as any).id);
        }
      }
    }

    // 2. Check agent health (no heartbeat for >10 minutes)
    const { data: unhealthyAgents } = await supabaseServer
      .from("jarvis_agents")
      .select("slug, status")
      .or(`last_heartbeat.is.null,last_heartbeat.lt.${tenMinutesAgo}`)
      .eq("status", "ACTIVE");

    if (unhealthyAgents && unhealthyAgents.length > 0) {
      for (const agent of unhealthyAgents) {
        const degradedData: Record<string, any> = { status: "DEGRADED" };
        await (supabaseServer as any)
          .from("jarvis_agents")
          .update(degradedData)
          .eq("slug", (agent as any).slug);
      }
    }

    // 3. Promote RETRYING → PENDING for runs ready to retry
    const pendingData: Record<string, any> = { status: "PENDING" };
    await (supabaseServer as any)
      .from("jarvis_agent_runs")
      .update(pendingData)
      .eq("status", "RETRYING")
      .lte("next_attempt_at", now);

    return NextResponse.json({
      ok: true,
      stuck_runs_found: stuckRuns?.length || 0,
      unhealthy_agents_found: unhealthyAgents?.length || 0,
    });
  } catch (error: any) {
    console.error("Watchdog error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

