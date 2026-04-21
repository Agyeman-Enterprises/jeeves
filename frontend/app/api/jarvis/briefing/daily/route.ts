import { NextRequest, NextResponse } from "next/server";
import { aggregateEvents } from "@/lib/jarvis/briefing/aggregator";
import { extractSignals } from "@/lib/jarvis/briefing/signals";
import { rankSignals } from "@/lib/jarvis/briefing/prioritizer";
import { composeDailyBrief } from "@/lib/jarvis/briefing/composer";
import { supabaseServer } from "@/lib/supabase/server";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    
    if (!userId) {
      return NextResponse.json({ error: "Missing user_id" }, { status: 400 });
    }

    // Get events for today
    const now = new Date();
    const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const endOfDay = new Date(startOfDay);
    endOfDay.setHours(23, 59, 59, 999);

    // Aggregate events
    const events = await aggregateEvents(userId, startOfDay, endOfDay);

    // Extract signals
    const signals = await extractSignals(userId, events);

    // Prioritize signals
    const prioritizedItems = rankSignals(signals);

    // Load most recent reflection (synthesized nightly by /api/cron/reflect)
    const reflectionQuery = (supabaseServer as any)
      .from("jarvis_journal_entries")
      .select("content")
      .eq("user_id", userId)
      .eq("entry_type", "reflection")
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    const { data: reflectionRow } = await reflectionQuery;
    const reflections = reflectionRow?.content as string | undefined;

    // Pull enterprise data from NEXUS briefing (alerts, decisions, entity health)
    // Runs concurrently with local data — failure is non-fatal
    let nexusBriefing: Record<string, unknown> | null = null;
    try {
      const nexusUrl = process.env.NEXUS_URL ?? process.env.NEXT_PUBLIC_NEXUS_URL ?? "http://localhost:3001";
      const nexusRes = await fetch(`${nexusUrl}/api/jarvis/briefing`, {
        headers: {
          "x-internal-key": process.env.NEXUS_INTERNAL_KEY ?? "",
          "x-user-id": userId,
        },
        signal: AbortSignal.timeout(5000),
      });
      if (nexusRes.ok) {
        nexusBriefing = await nexusRes.json();
      }
    } catch {
      // NEXUS unavailable — compose personal briefing without enterprise data
    }

    // Merge NEXUS enterprise context into reflections string for the LLM
    let enrichedReflections = reflections ?? "";
    if (nexusBriefing) {
      const alerts = (nexusBriefing.alerts as any[]) ?? [];
      const decisions = (nexusBriefing.pending_decisions as any[]) ?? [];
      const atRisk = (nexusBriefing.entities_at_risk as any[]) ?? [];
      const nexusSummary = [
        alerts.length > 0
          ? `Enterprise alerts: ${alerts.map((a: any) => `${a.title} (${a.severity})`).join(", ")}`
          : null,
        decisions.length > 0
          ? `Pending decisions: ${decisions.map((d: any) => d.title).join(", ")}`
          : null,
        atRisk.length > 0
          ? `Entities needing attention: ${atRisk.map((e: any) => e.name).join(", ")}`
          : null,
      ]
        .filter(Boolean)
        .join("\n");
      if (nexusSummary) {
        enrichedReflections = enrichedReflections
          ? `${enrichedReflections}\n\n${nexusSummary}`
          : nexusSummary;
      }
    }

    // Compose briefing (reflections + NEXUS enterprise data injected into LLM prompt)
    const briefing = await composeDailyBrief(userId, events, prioritizedItems, enrichedReflections || undefined);

    // Store briefing
    const { data, error } = await supabaseServer
      .from("jarvis_briefings")
      .insert({
        user_id: userId,
        type: briefing.type,
        period_start: briefing.period_start,
        period_end: briefing.period_end,
        content: briefing.content,
        summary_text: briefing.summary_text,
        signals_included: briefing.signals_included,
      } as any)
      .select()
      .single();

    if (error) {
      console.error("Failed to store briefing:", error);
    }

    return NextResponse.json(briefing);
  } catch (error: any) {
    console.error("Daily briefing error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

