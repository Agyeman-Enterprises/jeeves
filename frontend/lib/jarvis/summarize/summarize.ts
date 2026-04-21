import { callJarvisLLM } from "../llm/router";
import type { LLMMessage } from "../llm/types";

export interface SummarizeArgs {
  content: string;
  mode?: "general" | "email" | "meeting" | "actions" | "executive";
}

export interface SummarizeResult {
  summary: string;
  provider: string;
}

function buildSystemPrompt(mode: string) {
  switch (mode) {
    case "email":
      return `
Summarize the email or thread clearly.

Focus on:
- Intent
- Key details
- Required responses
- Deadlines

Output a short, precise summary.
`.trim();

    case "meeting":
      return `
Summarize the meeting content.

Output:
- Key decisions
- Action items (with owners if mentioned)
- Risks
- Deadlines
- Issues raised

Keep it structured and concise.
`.trim();

    case "actions":
      return `
Extract action items. Output only:
- Clear task statements
- Owners (if obvious)
- Deadlines (if stated)
`.trim();

    case "executive":
      return `
Summarize with an executive briefing style.

Include:
- High-level overview
- What changed
- What matters
- What to watch
- Decisions needed
`.trim();

    default:
      return `
Produce a clean, concise summary.
`.trim();
  }
}

export async function summarizeContent(
  args: SummarizeArgs
): Promise<SummarizeResult> {
  const { content, mode = "general" } = args;

  const system: LLMMessage = {
    role: "system",
    content: buildSystemPrompt(mode),
  };

  const user: LLMMessage = {
    role: "user",
    content,
  };

  const result = await callJarvisLLM({
    messages: [system, user],
    purpose: "summarization",
    temperature: 0.1,
    maxTokens: 512,
  });

  return {
    summary: result.content,
    provider: result.provider,
  };
}

