import { callJarvisLLM } from "../llm/router";
import type { LLMMessage } from "../llm/types";
import type { Briefing, BriefingContent, PrioritizedItem } from "./types";
import type { AggregatedEvents } from "./aggregator";

export async function composeDailyBrief(
  userId: string,
  events: AggregatedEvents,
  prioritizedItems: PrioritizedItem[],
  reflections?: string
): Promise<Briefing> {
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const endOfDay = new Date(startOfDay);
  endOfDay.setHours(23, 59, 59, 999);

  // Build structured content
  const content: BriefingContent = {
    clinical: {
      overview: "",
      priorities: prioritizedItems.filter((i) => i.type === "CLINICAL").slice(0, 5),
      stats: {
        new_messages: events.clinical.filter((e: any) => e.type === "PATIENT_MESSAGE").length,
        refills_pending: events.clinical.filter((e: any) => e.type === "MED_REFILL_REQUESTED").length,
        glp_overdue: 0, // Would need to query patient pipeline
        hospitalizations: events.clinical.filter((e: any) => e.type === "PATIENT_HOSPITALIZED").length,
        lab_results: events.clinical.filter((e: any) => e.type === "LAB_RESULT_RECEIVED").length,
      },
    },
    business: {
      overview: "",
      priorities: prioritizedItems.filter((i) => i.type === "OPERATIONAL").slice(0, 5),
      stats: {
        appointments_today: events.clinical.filter((e: any) => e.type === "NEW_APPOINTMENT_BOOKED").length,
        no_shows_projected: events.clinical.filter((e: any) => e.type === "APPOINTMENT_NO_SHOW").length,
        open_tasks: 0, // Would need to query tasks
      },
    },
    financial: {
      overview: "",
      priorities: prioritizedItems.filter((i) => i.type === "FINANCIAL").slice(0, 5),
      stats: {
        total_cash: 0, // Would need to query financial_snapshots
        burn_rate: 0,
        tax_estimate: 0,
        missing_receipts: 0,
      },
    },
    system: {
      overview: "",
      priorities: prioritizedItems.filter((i) => i.type === "SYSTEM").slice(0, 5),
      stats: {
        active_agents: 0, // Would need to query jarvis_agents
        degraded_agents: 0,
        retried_tasks: 0,
        stuck_runs: 0,
      },
    },
  };

  // Generate narrative summaries using LLM
  const systemPrompt = `You are Jarvis, an AI assistant providing a daily briefing. Generate concise, actionable summaries for each section. Be specific and prioritize actionable items.`;

  const reflectionBlock = reflections
    ? `\n\nRecent reflections (synthesized from memory):\n${reflections}`
    : "";

  const userPrompt = `Generate a daily briefing summary based on this data:

Clinical: ${JSON.stringify(content.clinical)}
Business: ${JSON.stringify(content.business)}
Financial: ${JSON.stringify(content.financial)}
System: ${JSON.stringify(content.system)}${reflectionBlock}

Provide a brief overview for each section (1-2 sentences) highlighting the most important items.`;

  try {
    const result = await callJarvisLLM({
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      purpose: "briefing",
      temperature: 0.3,
      maxTokens: 1000,
    });

    // Parse LLM response to extract section summaries
    const summary = result.content;
    content.clinical!.overview = extractSectionSummary(summary, "Clinical");
    content.business!.overview = extractSectionSummary(summary, "Business");
    content.financial!.overview = extractSectionSummary(summary, "Financial");
    content.system!.overview = extractSectionSummary(summary, "System");
  } catch (error) {
    console.error("Failed to generate briefing summaries:", error);
    // Fallback to simple summaries
    content.clinical!.overview = `${content.clinical!.stats.new_messages} new messages, ${content.clinical!.stats.refills_pending} refills pending`;
    content.business!.overview = `${content.business!.stats.appointments_today} appointments today`;
    content.financial!.overview = "Review financial overview in Nexus";
    content.system!.overview = "All systems operational";
  }

  const briefing: Briefing = {
    user_id: userId,
    type: "DAILY",
    period_start: startOfDay.toISOString(),
    period_end: endOfDay.toISOString(),
    content,
    summary_text: generateSummaryText(content),
    signals_included: prioritizedItems.map((i) => i.id || "").filter(Boolean),
  };

  return briefing;
}

// Hardcoded section headers — avoids dynamic RegExp (ReDoS risk)
const SECTION_PATTERNS: Record<string, RegExp> = {
  Clinical:  /Clinical[^:]*:([^\n]+)/i,
  Business:  /Business[^:]*:([^\n]+)/i,
  Financial: /Financial[^:]*:([^\n]+)/i,
  System:    /System[^:]*:([^\n]+)/i,
};

function extractSectionSummary(text: string, section: string): string {
  const pattern = SECTION_PATTERNS[section];
  if (!pattern) return "";
  const match = text.match(pattern);
  return match ? match[1].trim() : "";
}

function generateSummaryText(content: BriefingContent): string {
  const parts: string[] = [];

  if (content.clinical) {
    parts.push(`Clinical: ${content.clinical.stats.new_messages} messages, ${content.clinical.stats.refills_pending} refills, ${content.clinical.stats.hospitalizations} hospitalizations`);
  }

  if (content.business) {
    parts.push(`Business: ${content.business.stats.appointments_today} appointments today`);
  }

  if (content.financial) {
    parts.push(`Financial: Review in Nexus`);
  }

  if (content.system) {
    parts.push(`System: ${content.system.stats.active_agents} agents active`);
  }

  return parts.join(". ") + ".";
}

