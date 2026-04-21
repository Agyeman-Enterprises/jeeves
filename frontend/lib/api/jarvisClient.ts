// lib/api/jarvisClient.ts
// Routes through the Next.js proxy to avoid CORS (server-side fetch to FastAPI on port 8001).

const BACKEND = "/api/proxy";

export type JarvisCommandPayload = {
  command?: string;
  message?: string;
  workspace?: string;
  metadata?: Record<string, any>;
};

export type JarvisBackendResponse = {
  ok: boolean;
  reply: string;
  agent?: string;
  classification?: string;
};

export async function sendJarvisCommand(
  payload: JarvisCommandPayload
): Promise<JarvisBackendResponse> {
  // Build the query string from whatever field was passed
  const query =
    payload.command ||
    payload.message ||
    payload.metadata?.naturalLanguage ||
    "";

  if (!query.trim()) {
    return { ok: false, reply: "No command provided." };
  }

  try {
    const res = await fetch(`${BACKEND}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, context: payload.metadata ?? {} }),
    });

    if (!res.ok) {
      console.error("[sendJarvisCommand] HTTP error", res.status);
      return { ok: false, reply: `Backend error (${res.status}). Is JARVIS running?` };
    }

    const data = await res.json();
    return {
      ok: true,
      reply: data.content ?? data.messages?.[1]?.text ?? "No response.",
      agent: data.agent,
    };
  } catch (err) {
    console.error("[sendJarvisCommand] fetch failed:", err);
    return {
      ok: false,
      reply: "Could not reach JARVIS backend. Make sure it's running on port 8001.",
    };
  }
}
