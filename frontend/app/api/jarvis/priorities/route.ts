// JJ priorities — reads top goals from JJ /brain/goals (JJ Supabase, ranked by effective_weight)
import { NextResponse } from "next/server";

const JJ_URL = process.env.JARVIS_BACKEND_URL ?? "http://localhost:4004";
const JJ_API_KEY = process.env.JARVIS_API_KEY ?? "";

export async function GET() {
  try {
    const res = await fetch(`${JJ_URL}/brain/goals`, {
      cache: "no-store",
      headers: JJ_API_KEY ? { Authorization: `Bearer ${JJ_API_KEY}` } : {},
      signal: AbortSignal.timeout(12_000),
    });
    if (!res.ok) {
      return NextResponse.json({ ok: false, error: `JJ returned ${res.status}` }, { status: res.status });
    }
    const goals = await res.json();
    // Normalise to the shape the home page expects
    const priorities = Array.isArray(goals) ? goals.slice(0, 5) : [];
    return NextResponse.json({
      ok: true,
      data: {
        total: priorities.length,
        priorities,
        summary: priorities.map((g: Record<string, unknown>) => g.label ?? g.goal_name).join(", "),
        decision_prompt: "Focus on your top goals today.",
      },
    });
  } catch (err) {
    console.warn("[API /jarvis/priorities] JJ offline:", err instanceof Error ? err.message : err);
    return NextResponse.json({ ok: true, data: { total: 0, priorities: [], summary: "", decision_prompt: "" } });
  }
}
