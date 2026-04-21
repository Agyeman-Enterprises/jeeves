import type { LLMCallArgs, LLMCallResult } from "./types";

const localBaseUrl = process.env.LOCAL_LLM_BASE_URL;
const localModel = process.env.LOCAL_LLM_MODEL || "jarvis-mini";
const localApiKey = process.env.LOCAL_LLM_API_KEY;

export function isLocalLLMConfigured() {
  return !!localBaseUrl;
}

export async function callLocalLLM(
  args: LLMCallArgs
): Promise<LLMCallResult> {
  if (!localBaseUrl) {
    throw new Error("LOCAL_LLM_BASE_URL not configured");
  }

  const body = {
    model: localModel,
    messages: args.messages,
    temperature: args.temperature ?? 0,
    max_tokens: args.maxTokens ?? 512,
  };

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (localApiKey) {
    headers["Authorization"] = `Bearer ${localApiKey}`;
  }

  const res = await fetch(`${localBaseUrl}/v1/chat/completions`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `Local LLM error: ${res.status} ${res.statusText} - ${text}`
    );
  }

  const json: any = await res.json();
  const content =
    json?.choices?.[0]?.message?.content ??
    json?.choices?.[0]?.text ??
    "";

  return {
    provider: "local",
    model: localModel,
    content,
    raw: json,
  };
}

