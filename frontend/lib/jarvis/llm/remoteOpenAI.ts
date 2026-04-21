import OpenAI from "openai";
import type { LLMCallArgs, LLMCallResult } from "./types";

const apiKey = process.env.OPENAI_API_KEY;

let openai: OpenAI | null = null;
if (apiKey) {
  openai = new OpenAI({ apiKey });
}

export function isOpenAIConfigured() {
  return !!openai;
}

export function getClassifierModel() {
  return process.env.JARVIS_LLM_MODEL || "gpt-4.1-mini";
}

export async function callOpenAILLM(
  args: LLMCallArgs
): Promise<LLMCallResult> {
  if (!openai) {
    throw new Error("OpenAI not configured");
  }

  const model = getClassifierModel();

  const completion = await openai.chat.completions.create({
    model,
    messages: args.messages,
    temperature: args.temperature ?? 0,
    max_tokens: args.maxTokens ?? 512,
  });

  const content =
    completion.choices[0]?.message?.content ??
    completion.choices[0]?.message?.content ??
    "";

  return {
    provider: "openai",
    model,
    content,
    raw: completion,
  };
}

