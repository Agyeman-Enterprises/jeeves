import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import type { HeartbeatRequest } from "@/lib/jarvis/agents/lifecycle";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as HeartbeatRequest;
    const { agent_slug, version, metrics } = body;

    const now = new Date().toISOString();

    // Update agent heartbeat
    const heartbeatData: Record<string, any> = {
      last_heartbeat: now,
      last_seen_version: version || null,
    };
    const { error } = await (supabaseServer as any)
      .from("jarvis_agents")
      .update(heartbeatData)
      .eq("slug", agent_slug);

    if (error) {
      console.error("Heartbeat error:", error);
      return NextResponse.json({ error: "Failed to update heartbeat" }, { status: 500 });
    }

    // Check if agent should be marked as DEGRADED based on metrics
    if (metrics) {
      const { data: agent } = await supabaseServer
        .from("jarvis_agents")
        .select("failure_streak, status")
        .eq("slug", agent_slug)
        .single();

      if (agent) {
        const failureStreak = (agent as any).failure_streak || 0;
        const currentStatus = (agent as any).status;

        // Mark as DEGRADED if failure streak is high
        if (failureStreak >= 5 && currentStatus === "ACTIVE") {
          const degradedData: Record<string, any> = { status: "DEGRADED" };
          await (supabaseServer as any)
            .from("jarvis_agents")
            .update(degradedData)
            .eq("slug", agent_slug);
        }
      }
    }

    return NextResponse.json({ ok: true });
  } catch (error: any) {
    console.error("Heartbeat error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

