// JJ personal context — reads from JJ Supabase (tzjygaxpzrtevlnganjs)
// Tables: jeeves_events (calendar), jeeves_tasks (tasks)
// Cloud is primary authority — no local fallback needed here.
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const { supabaseServer: supabase } = await import("@/lib/supabase/server");
    const now = new Date().toISOString();

    // Next calendar event (jeeves_events in JJ Supabase)
    const { data: nextEvent } = await supabase
      .from("jeeves_events")
      .select("*")
      .gte("start_time", now)
      .order("start_time", { ascending: true })
      .limit(1)
      .maybeSingle();

    // Active tasks (jeeves_tasks in JJ Supabase)
    const { data: tasks } = await supabase
      .from("jeeves_tasks")
      .select("*")
      .eq("status", "active")
      .order("priority", { ascending: true })
      .limit(3);

    return NextResponse.json({
      weather: null,      // weather not tracked in JJ v2
      nextEvent: nextEvent || null,
      tasks: tasks || [],
    });
  } catch (err) {
    console.warn("[API /jarvis/personal] Supabase error:", err);
    return NextResponse.json({ weather: null, nextEvent: null, tasks: [] });
  }
}

