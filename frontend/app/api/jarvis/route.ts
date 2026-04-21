"use server";
// JJ — main chat route. Routes directly to JJ /jang/chat (JANG graph).
// JJ is the merged Jeeves+JARVIS butler. Single FastAPI service on port 4004.

import { NextResponse } from "next/server";

const JJ_URL = process.env.JARVIS_BACKEND_URL ?? "http://localhost:4004";
const JJ_API_KEY = process.env.JARVIS_API_KEY ?? "";

function authHeaders(): Record<string, string> {
  return JJ_API_KEY ? { Authorization: `Bearer ${JJ_API_KEY}` } : {};
}

export async function POST(req: Request) {
  try {
    const { input, session_id, context } = await req.json();

    if (!input) {
      return NextResponse.json({ error: "Input is required" }, { status: 400 });
    }

    const res = await fetch(`${JJ_URL}/jang/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        message: input,
        session_id: session_id ?? "default",
        context: context ?? {},
      }),
      signal: AbortSignal.timeout(30000),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`JJ error ${res.status}: ${text}`);
    }

    const data = await res.json();
    return NextResponse.json({
      success: true,
      reply: data.response ?? data.agent_response ?? "No response.",
      agent: "jj",
      sources_used: data.sources_used ?? [],
      importance_score: data.importance_score ?? 0,
      orchestrated_by: "jj",
    });
  } catch (error) {
    console.error("[/api/jarvis] JJ error:", error);
    return NextResponse.json(
      { error: "Failed to process request", details: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}
