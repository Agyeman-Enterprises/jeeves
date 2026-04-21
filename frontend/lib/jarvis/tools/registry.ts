import type {
  JarvisToolDefinition,
  JarvisToolResult,
  JarvisToolContext,
} from "../types";
import { readMemory, writeMemory } from "../memory/memory";
import { appendJournalInternal } from "../journal/journal_internal";
import { summarizeTool } from "./summarizeTool";

// Stubbed external tools
async function analyticsSummaryTool(
  ctx: JarvisToolContext
): Promise<JarvisToolResult> {
  // TODO: connect to Nexus analytics once available
  return {
    ok: true,
    tool: "analytics.summary",
    data: {
      message:
        "Analytics summary tool stub. Wire this to Nexus dashboards later.",
      query: ctx.query,
    },
  };
}

async function emailDraftTool(
  ctx: JarvisToolContext
): Promise<JarvisToolResult> {
  // TODO: connect to Gmail/Outlook integration
  return {
    ok: true,
    tool: "email.draft",
    data: {
      message:
        "Email drafting stub. Wire to email provider (e.g., Gmail/Outlook).",
      query: ctx.query,
    },
  };
}

async function scheduleCreateTool(
  ctx: JarvisToolContext
): Promise<JarvisToolResult> {
  // TODO: connect to calendar provider
  return {
    ok: true,
    tool: "schedule.create",
    data: {
      message:
        "Schedule creation stub. Wire to calendar provider (Google/Microsoft).",
      query: ctx.query,
    },
  };
}

async function fileListTool(
  ctx: JarvisToolContext
): Promise<JarvisToolResult> {
  // TODO: connect to Nexus file system / storage
  return {
    ok: true,
    tool: "file.list",
    data: {
      message: "File listing stub. Wire to Nexus file storage.",
      query: ctx.query,
    },
  };
}

export const toolRegistry: Record<string, JarvisToolDefinition> = {
  "memory.read": {
    name: "memory.read",
    description: "Read long-term memory items from Supabase.",
    run: async (ctx: JarvisToolContext): Promise<JarvisToolResult> => {
      const data = await readMemory({
        user: ctx.user,
        query: ctx.query,
      });
      return { ok: true, tool: "memory.read", data };
    },
  },
  "memory.write": {
    name: "memory.write",
    description: "Write a long-term memory item.",
    run: async (ctx: JarvisToolContext): Promise<JarvisToolResult> => {
      const data = await writeMemory({
        user: ctx.user,
        query: ctx.query,
        payload: ctx.routedTask.payload,
      });
      return { ok: true, tool: "memory.write", data };
    },
  },
  "journal.append": {
    name: "journal.append",
    description: "Append auxiliary info into the Jarvis journal.",
    run: async (ctx: JarvisToolContext): Promise<JarvisToolResult> => {
      const data = await appendJournalInternal({
        user: ctx.user,
        query: ctx.query,
        payload: ctx.routedTask.payload,
      });
      return { ok: true, tool: "journal.append", data };
    },
  },
  "analytics.summary": {
    name: "analytics.summary",
    description: "Summarize analytics / metrics for Nexus dashboards.",
    run: analyticsSummaryTool,
  },
  "email.draft": {
    name: "email.draft",
    description: "Draft an email based on the user's request.",
    run: emailDraftTool,
  },
  "schedule.create": {
    name: "schedule.create",
    description: "Create a calendar event or appointment.",
    run: scheduleCreateTool,
  },
  "file.list": {
    name: "file.list",
    description: "List files relevant to the user's context/query.",
    run: fileListTool,
  },
  "summarize": {
    name: "summarize",
    description: "Summarize content into structured or brief formats.",
    run: summarizeTool,
  },
};

