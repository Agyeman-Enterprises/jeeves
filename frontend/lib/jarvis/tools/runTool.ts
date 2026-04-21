import type {
  JarvisCommandInput,
  JarvisRoutedTask,
  JarvisToolResult,
  JarvisToolContext,
} from "../types";
import { toolRegistry } from "./registry";

interface RunToolArgs extends JarvisCommandInput {
  routedTask: JarvisRoutedTask;
}

export async function runTool(args: RunToolArgs): Promise<JarvisToolResult> {
  const { routedTask } = args;
  const { tool } = routedTask;

  if (!tool || tool === "none") {
    return { ok: true, tool: "none", data: null };
  }

  const def = toolRegistry[tool];
  if (!def) {
    console.warn(`Jarvis tool not registered: ${tool}`);
    return {
      ok: false,
      tool,
      error: `Tool not registered: ${tool}`,
    };
  }

  const ctx: JarvisToolContext = {
    ...args,
    routedTask,
  };

  try {
    return await def.run(ctx);
  } catch (error: any) {
    console.error(`Jarvis tool ${tool} error:`, error);
    return {
      ok: false,
      tool,
      error: error?.message ?? "Unknown tool error",
    };
  }
}

