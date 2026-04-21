import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    // Get all agents
    const { data: agents } = await supabaseServer
      .from("jarvis_agents")
      .select("*")
      .eq("is_active", true);

    if (!agents) {
      return NextResponse.json({ agents: [], stats: {} });
    }

    // Get run counts per agent
    const agentStats = await Promise.all(
      agents.map(async (agent: any) => {
        const agentSlug = agent.slug;

        const [pending, running, failed] = await Promise.all([
          supabaseServer
            .from("jarvis_agent_runs")
            .select("id", { count: "exact", head: true })
            .eq("agent_slug", agentSlug)
            .eq("status", "PENDING"),
          supabaseServer
            .from("jarvis_agent_runs")
            .select("id", { count: "exact", head: true })
            .eq("agent_slug", agentSlug)
            .eq("status", "RUNNING"),
          supabaseServer
            .from("jarvis_agent_runs")
            .select("id", { count: "exact", head: true })
            .eq("agent_slug", agentSlug)
            .eq("status", "FAILED")
            .gte("created_at", new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()),
        ]);

        return {
          slug: agentSlug,
          name: agent.name,
          status: agent.status || "ACTIVE",
          domain: agent.domain,
          last_heartbeat: agent.last_heartbeat,
          success_streak: agent.success_streak || 0,
          failure_streak: agent.failure_streak || 0,
          pending_runs: (pending as any).count || 0,
          running_runs: (running as any).count || 0,
          failed_runs_24h: (failed as any).count || 0,
        };
      })
    );

    // Calculate totals
    const stats = {
      total_pending: agentStats.reduce((sum, a) => sum + a.pending_runs, 0),
      total_running: agentStats.reduce((sum, a) => sum + a.running_runs, 0),
      total_failed_last_24h: agentStats.reduce((sum, a) => sum + a.failed_runs_24h, 0),
    };

    return NextResponse.json({
      agents: agentStats,
      stats,
    });
  } catch (error: any) {
    console.error("Dashboard error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

