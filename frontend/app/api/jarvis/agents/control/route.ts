import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { agent_slug, action } = body;

    if (!agent_slug || !action) {
      return NextResponse.json({ error: "Missing agent_slug or action" }, { status: 400 });
    }

    let newStatus: string;
    switch (action) {
      case "pause":
        newStatus = "PAUSED";
        break;
      case "disable":
        newStatus = "DISABLED";
        break;
      case "activate":
        newStatus = "ACTIVE";
        break;
      case "retry_failed":
        // Retry all failed runs for this agent
        const retryData: Record<string, any> = {
          status: "PENDING",
          attempt_count: 0,
          next_attempt_at: null,
        };
        await (supabaseServer as any)
          .from("jarvis_agent_runs")
          .update(retryData)
          .eq("agent_slug", agent_slug)
          .eq("status", "FAILED");
        return NextResponse.json({ ok: true, message: "Failed runs reset to PENDING" });
      default:
        return NextResponse.json({ error: "Invalid action" }, { status: 400 });
    }

    const updateData: Record<string, any> = { status: newStatus };
    const { error } = await (supabaseServer as any)
      .from("jarvis_agents")
      .update(updateData)
      .eq("slug", agent_slug);

    if (error) {
      console.error("Control agent error:", error);
      return NextResponse.json({ error: "Failed to update agent status" }, { status: 500 });
    }

    return NextResponse.json({ ok: true, status: newStatus });
  } catch (error: any) {
    console.error("Control agent error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

