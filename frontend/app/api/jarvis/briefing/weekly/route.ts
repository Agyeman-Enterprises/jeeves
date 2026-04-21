import { NextRequest, NextResponse } from "next/server";
import { aggregateEvents } from "@/lib/jarvis/briefing/aggregator";
import { extractSignals } from "@/lib/jarvis/briefing/signals";
import { rankSignals } from "@/lib/jarvis/briefing/prioritizer";
import { supabaseServer } from "@/lib/supabase/server";
import { callJarvisLLM } from "@/lib/jarvis/briefing/../llm/router";
import type { Briefing, BriefingContent } from "@/lib/jarvis/briefing/types";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    
    if (!userId) {
      return NextResponse.json({ error: "Missing user_id" }, { status: 400 });
    }

    // Get events for the past week
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - 7);
    startOfWeek.setHours(0, 0, 0, 0);

    // Aggregate events
    const events = await aggregateEvents(userId, startOfWeek, now);

    // Extract signals
    const signals = await extractSignals(userId, events);

    // Prioritize signals
    const prioritizedItems = rankSignals(signals);

    // Compose weekly briefing
    const content: BriefingContent = {
      clinical: {
        overview: "",
        priorities: prioritizedItems.filter((i) => i.type === "CLINICAL").slice(0, 10),
        stats: {
          new_messages: events.clinical.filter((e: any) => e.type === "PATIENT_MESSAGE").length,
          refills_pending: events.clinical.filter((e: any) => e.type === "MED_REFILL_REQUESTED").length,
          glp_overdue: 0,
          hospitalizations: events.clinical.filter((e: any) => e.type === "PATIENT_HOSPITALIZED").length,
          lab_results: events.clinical.filter((e: any) => e.type === "LAB_RESULT_RECEIVED").length,
        },
      },
      business: {
        overview: "",
        priorities: prioritizedItems.filter((i) => i.type === "OPERATIONAL").slice(0, 10),
        stats: {
          appointments_today: events.clinical.filter((e: any) => e.type === "NEW_APPOINTMENT_BOOKED").length,
          no_shows_projected: events.clinical.filter((e: any) => e.type === "APPOINTMENT_NO_SHOW").length,
          open_tasks: 0,
        },
      },
      financial: {
        overview: "",
        priorities: prioritizedItems.filter((i) => i.type === "FINANCIAL").slice(0, 10),
        stats: {
          total_cash: 0,
          burn_rate: 0,
          tax_estimate: 0,
          missing_receipts: 0,
        },
      },
    };

    // Generate weekly summary using LLM
    const systemPrompt = `You are Jarvis providing a weekly review. Summarize trends, risks, opportunities, and recommendations.`;
    const userPrompt = `Generate a weekly review based on this week's data:

${JSON.stringify(content, null, 2)}

Provide:
1. What Happened (summary)
2. Trends Detected
3. Risks Identified
4. Opportunities Identified
5. Recommendations for the Week Ahead (3-5 high-impact items)`;

    let summaryText = "";
    try {
      const result = await callJarvisLLM({
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt },
        ],
        purpose: "briefing",
        temperature: 0.3,
        maxTokens: 2000,
      });
      summaryText = result.content;
    } catch (error) {
      console.error("Failed to generate weekly summary:", error);
      summaryText = "Weekly review generated. See detailed sections below.";
    }

    const briefing: Briefing = {
      user_id: userId,
      type: "WEEKLY",
      period_start: startOfWeek.toISOString(),
      period_end: now.toISOString(),
      content,
      summary_text: summaryText,
      signals_included: prioritizedItems.map((i) => i.id || "").filter(Boolean),
    };

    // Store briefing
    await supabaseServer
      .from("jarvis_briefings")
      .insert({
        user_id: userId,
        type: briefing.type,
        period_start: briefing.period_start,
        period_end: briefing.period_end,
        content: briefing.content,
        summary_text: briefing.summary_text,
        signals_included: briefing.signals_included,
      } as any);

    return NextResponse.json(briefing);
  } catch (error: any) {
    console.error("Weekly briefing error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

