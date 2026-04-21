import type {
  JarvisTaskClassification,
  JarvisCommandInput,
  JarvisTaskKind,
} from "../types";
import { callJarvisLLM } from "../llm/router";
import type { LLMMessage } from "../llm/types";

interface LLMClassifyArgs extends JarvisCommandInput {
  ruleBased: JarvisTaskClassification;
}

type RawKind =
  | "QUESTION"
  | "ACTION"
  | "SCHEDULE"
  | "FILE_OP"
  | "EMAIL"
  | "ANALYTICS"
  | "UNKNOWN";

export async function classifyTaskWithLLM(
  args: LLMClassifyArgs
): Promise<JarvisTaskClassification | null> {
  const { query, messages = [], workspaceContext, ruleBased } = args;

  const systemContent = `
You are Jarvis's task classifier for a private assistant.

PRIVACY RULE:
- You are running in a private environment. Do not assume you can call external APIs yourself.
- Only classify the task as instructed.

You must return STRICT JSON with keys:
- kind: one of ["QUESTION","ACTION","SCHEDULE","FILE_OP","EMAIL","ANALYTICS","UNKNOWN"]
- confidence: number between 0 and 1
- reason: short string explaining your reasoning
- tags: array of short strings

Do not include any extra keys.
Do not include any natural language outside of the JSON.
`;

  const systemMessage: LLMMessage = {
    role: "system",
    content: systemContent.trim(),
  };

  const userMessage: LLMMessage = {
    role: "user",
    content: JSON.stringify({
      query,
      workspaceContext,
      recentMessages: messages.slice(-5),
      ruleBased,
    }),
  };

  let result;
  try {
    result = await callJarvisLLM({
      messages: [systemMessage, userMessage],
      purpose: "classification",
      temperature: 0,
      maxTokens: 256,
    });
  } catch (error) {
    // No LLM configured or failed → skip
    console.error("LLM classification failed:", error);
    return null;
  }

  const content = result.content;
  let parsed: {
    kind: RawKind;
    confidence: number;
    reason: string;
    tags: string[];
  };

  try {
    parsed = JSON.parse(content);
  } catch (err) {
    console.error("LLM classify JSON parse error:", err, content);
    return null;
  }

  const kind: JarvisTaskKind = parsed.kind;
  return {
    kind,
    confidence: Math.min(1, Math.max(0, parsed.confidence ?? 0.7)),
    reason:
      parsed.reason ||
      `LLM classification via ${result.provider}:${result.model}`,
    tags: parsed.tags || [],
  };
}

