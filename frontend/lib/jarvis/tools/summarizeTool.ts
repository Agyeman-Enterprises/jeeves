import type { JarvisToolContext, JarvisToolResult } from "../types";
import { summarizeContent } from "../summarize/summarize";

export async function summarizeTool(
  ctx: JarvisToolContext
): Promise<JarvisToolResult> {
  const mode = ctx.routedTask.payload?.mode ?? "general";

  const summary = await summarizeContent({
    content: ctx.query,
    mode,
  });

  return {
    ok: true,
    tool: "summarize",
    data: summary,
  };
}

