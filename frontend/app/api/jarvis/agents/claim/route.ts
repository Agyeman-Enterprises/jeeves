import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import type { ClaimWorkRequest, ClaimWorkResponse } from "@/lib/jarvis/agents/lifecycle";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ClaimWorkRequest;
    const { agent_slug, max_batch = 1 } = body;

    // Find PENDING or RETRYING runs for this agent
    const now = new Date().toISOString();
    const { data: runs, error } = await supabaseServer
      .from("jarvis_agent_runs")
      .select("*")
      .eq("agent_slug", agent_slug)
      .in("status", ["PENDING", "RETRYING"])
      .or(`next_attempt_at.is.null,next_attempt_at.lte.${now}`)
      .order("priority", { ascending: false })
      .order("created_at", { ascending: true })
      .limit(max_batch);

    if (error) {
      console.error("Claim work error:", error);
      return NextResponse.json({ error: "Failed to claim work" }, { status: 500 });
    }

    if (!runs || runs.length === 0) {
      return NextResponse.json({ runs: [] } as ClaimWorkResponse);
    }

    // Mark runs as RUNNING and increment attempt_count
    // Update each run individually to increment attempt_count
    for (const run of runs) {
      const currentAttemptCount = (run as any).attempt_count || 0;
      const updateData: Record<string, any> = {
        status: "RUNNING",
        attempt_count: currentAttemptCount + 1,
        started_at: now,
      };
      const { error: updateError } = await (supabaseServer as any)
        .from("jarvis_agent_runs")
        .update(updateData)
        .eq("id", (run as any).id);
      
      if (updateError) {
        console.error("Failed to update run to RUNNING:", updateError);
        return NextResponse.json({ error: "Failed to claim work" }, { status: 500 });
      }
    }

    // Format response
    const claimedRuns = runs.map((run: any) => ({
      id: run.id,
      input: run.input,
      user: {
        userId: run.user_id,
        workspaceId: run.workspace_id,
      },
      planId: run.plan_id,
      planStepId: run.plan_step_id,
    }));

    return NextResponse.json({ runs: claimedRuns } as ClaimWorkResponse);
  } catch (error: any) {
    console.error("Claim work error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

