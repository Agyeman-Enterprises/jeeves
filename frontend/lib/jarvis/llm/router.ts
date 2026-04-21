import type { LLMCallArgs, LLMCallResult } from "./types";
import { isLocalLLMConfigured, callLocalLLM } from "./local";
import {
  isOpenAIConfigured,
  callOpenAILLM,
} from "./remoteOpenAI";

export async function callJarvisLLM(
  args: LLMCallArgs
): Promise<LLMCallResult> {
  // 1) Try LOCAL first (privacy-first)
  if (isLocalLLMConfigured()) {
    try {
      const result = await callLocalLLM(args);
      return result;
    } catch (error) {
      console.error("Local LLM failed, falling back to remote:", error);
    }
  }

  // 2) Fallback to OpenAI (or later Anthropic) if available
  if (isOpenAIConfigured()) {
    const result = await callOpenAILLM(args);
    return result;
  }

  // 3) If nothing available, fail loudly so caller can fallback to rules
  throw new Error("No LLM provider available (local or remote).");
}

