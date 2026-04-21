/**
 * /api/cron/reflect
 *
 * Nightly reflection synthesizer — runs at 3am via Vercel cron.
 * Reverie architecture: Memory Stream → Reflection Loop → insight storage.
 *
 * For each active user:
 *   1. Load recent high-importance memories (last 7 days, importance >= 6)
 *   2. Ask the LLM to synthesize 5 key insights
 *   3. Store as jarvis_journal_entries with entry_type = 'reflection'
 *
 * Secured by CRON_SECRET header (set in Vercel env vars).
 */

import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import { callJarvisLLM } from "@/lib/jarvis/llm/router";

const CRON_SECRET = process.env.CRON_SECRET ?? "";

export async function POST(req: NextRequest) {
  // Vercel sends the cron secret in the Authorization header
  const authHeader = req.headers.get("authorization");
  if (CRON_SECRET && authHeader !== `Bearer ${CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();

  // Find all users who have memory chunks in the last 7 days
  const { data: activeUsers, error: userErr } = await supabaseServer
    .from("jarvis_memory_chunks")
    .select("user_id")
    .gte("created_at", sevenDaysAgo)
    .not("content", "is", null);

  if (userErr) {
    console.error("[reflect] Failed to query active users:", userErr.message);
    return NextResponse.json({ error: userErr.message }, { status: 500 });
  }

  const uniqueUserIds = [...new Set((activeUsers ?? []).map((r: any) => r.user_id as string))];
  if (uniqueUserIds.length === 0) {
    return NextResponse.json({ ok: true, processed: 0, message: "No active users" });
  }

  const results: Array<{ userId: string; status: string; insights?: number }> = [];

  for (const userId of uniqueUserIds) {
    try {
      // Load high-importance memories from the last 7 days
      const { data: memories, error: memErr } = await supabaseServer
        .from("jarvis_memory_chunks")
        .select("role, content, importance, created_at, agent")
        .eq("user_id", userId)
        .gte("created_at", sevenDaysAgo)
        .gte("importance", 6)
        .order("created_at", { ascending: false })
        .limit(60);

      if (memErr || !memories?.length) {
        results.push({ userId, status: "skipped_no_memories" });
        continue;
      }

      // Format memories for the LLM
      const memoryBlock = memories
        .map((m: any) => {
          const ts = new Date(m.created_at).toLocaleDateString("en-US", {
            weekday: "short",
            month: "short",
            day: "numeric",
          });
          const agent = m.agent ? ` [${m.agent}]` : "";
          return `${ts}${agent} (${m.role}): ${m.content}`;
        })
        .join("\n");

      const llmResult = await callJarvisLLM({
        purpose: "reflection",
        temperature: 0.4,
        maxTokens: 512,
        messages: [
          {
            role: "system",
            content:
              "You are JARVIS, an AI chief of staff. Review recent conversation memories and return insights.",
          },
          {
            role: "user",
            content: `Review these recent conversation memories and synthesize exactly 5 key insights about patterns, decisions, priorities, and themes.\n\nMEMORIES:\n${memoryBlock}\n\nReturn ONLY a JSON array of 5 strings, each being one insight. No preamble.\nExample: ["Insight 1", "Insight 2", "Insight 3", "Insight 4", "Insight 5"]`,
          },
        ],
      });

      let insights: string[] = [];
      try {
        const jsonMatch = llmResult.content.match(/\[[\s\S]*\]/);
        insights = JSON.parse(jsonMatch?.[0] ?? "[]");
      } catch {
        insights = [];
      }

      if (insights.length === 0) {
        results.push({ userId, status: "no_insights_parsed" });
        continue;
      }

      const content = insights.join("\n\n");
      const summary = insights[0];
      const tags = ["reflection", "auto-generated"];

      const { error: insertErr } = await supabaseServer
        .from("jarvis_journal_entries")
        .insert({
          user_id: userId,
          entry_type: "reflection",
          content,
          summary,
          tags,
          session_id: null,
        } as any);

      if (insertErr) {
        console.error("[reflect] Failed to insert reflection", { userId, error: insertErr.message });
        results.push({ userId, status: "insert_failed" });
      } else {
        results.push({ userId, status: "ok", insights: insights.length });
      }
    } catch (err: unknown) {
      console.error("[reflect] Error processing user", { userId, error: (err as Error).message });
      results.push({ userId, status: "error" });
    }
  }

  const ok = results.filter((r) => r.status === "ok").length;
  console.log(`[reflect] Processed ${ok}/${uniqueUserIds.length} users`);
  return NextResponse.json({ ok: true, processed: uniqueUserIds.length, succeeded: ok, results });
}
