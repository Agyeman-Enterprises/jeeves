// Router core - orchestrates the full Jarvis command processing pipeline
import { rewriteQuery } from "./rewrite";
import { classifyTask } from "../classifier/taskClassifier";
import { createJarvisDb } from "@/lib/db/jarvis";
import { createMemoryChunk } from "@/lib/db/jarvis/memory";
import { writeJournalEntry } from "@/lib/jarvis/journal/service";
import { logTimelineEvent } from "@/lib/jarvis/timeline/service";
import { storeMemoryChunk } from "@/lib/jarvis/memory/service";
import type { AgentContext } from "@/lib/jarvis/agents/types";
import { createPlanForIntent } from "@/lib/jarvis/planner";
import { runPlan } from "@/lib/jarvis/planner/execute";
import { emitEvent } from "@/lib/jarvis/events/gem/bus";

export interface RouteJarvisCommandPayload {
  text: string;
  userId: string;
  workspaceId: string;
}

export interface RouteJarvisCommandResult {
  input: string;
  rewritten: string;
  intent: string;
  confidence: number;
  result: any;
  agentResult?: any;
}

/**
 * Route a Jarvis command through the full pipeline:
 * 1. Rewrite query
 * 2. Classify task
 * 3. Write journal entry
 * 4. Execute action based on intent
 * 5. Return consistent JSON envelope
 */
export async function routeJarvisCommand(
  payload: RouteJarvisCommandPayload
): Promise<RouteJarvisCommandResult> {
  const { text, userId, workspaceId } = payload;
  const correlationId = crypto.randomUUID();

  // Emit command received event
  try {
    await emitEvent({
      type: 'jarvis.command.received',
      source: 'jarvis.command',
      workspaceId,
      userId,
      correlationId,
      payload: {
        workspaceId,
        userId,
        commandName: 'routeJarvisCommand',
        rawInput: text,
        correlationId,
      },
    });
  } catch (error) {
    console.error('[RouteJarvisCommand] Failed to emit command.received event:', error);
  }

  // Step 1: Rewrite query
  const rewritten = await rewriteQuery(text);

  // Step 2: Classify task
  const classification = await classifyTask(rewritten);

  // Step 2b: Construct agent context
  const ctx: AgentContext = {
    userId: payload.userId,
    workspaceId: payload.workspaceId,
    input: payload.text,
    rewritten,
    intent: classification.intent,
    metadata: {
      confidence: classification.confidence,
      suggestedAgent: classification.suggestedAgent,
    },
  };

  // Step 2c: Run agent if applicable
  let agentResult: any = null;
  if (
    classification.intent.startsWith("memory.") ||
    classification.intent.startsWith("debug.") ||
    classification.intent === "agent.run"
  ) {
    try {
      const plan = await createPlanForIntent(ctx);
      if (plan) {
        agentResult = await runPlan(plan, ctx);
      }
    } catch (error) {
      console.error("[RouteJarvisCommand] Agent execution error:", error);
      agentResult = {
        status: "error",
        agent: "unknown",
        summary: "Agent execution failed.",
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  // Step 3: Write journal entry
  try {
    await writeJournalEntry({
      userId: payload.userId,
      workspaceId: payload.workspaceId,
      type: classification.intent,
      content: `input=${payload.text}\nrewritten=${rewritten}`,
    });
  } catch (error) {
    // Don't fail the request if journal logging fails
    console.error("[RouteJarvisCommand] Journal logging error:", error);
  }

  // Step 3b: Log timeline event
  try {
    await logTimelineEvent({
      userId: payload.userId,
      workspaceId: payload.workspaceId,
      category: "jarvis.command",
      label: classification.intent,
      refType: "journal",
      // refId can later be wired to the created journal entry id
    });
  } catch (error) {
    // Don't fail the request if timeline logging fails
    console.error("[RouteJarvisCommand] Timeline logging error:", error);
  }

  // Step 3c: Store memory chunk for certain intents
  if (
    classification.intent === "memory.add" ||
    classification.intent === "plan.create" ||
    classification.intent === "agent.run"
  ) {
    try {
      await storeMemoryChunk({
        userId: payload.userId,
        workspaceId: payload.workspaceId,
        content: rewritten,
        source: "jarvis.command",
      });
    } catch (error) {
      // Don't fail the request if memory storage fails
      console.error("[RouteJarvisCommand] Memory storage error:", error);
    }
  }

  // Step 4: Switch on classification.intent and execute action
  let result: any;

  switch (classification.intent) {
    case "email.send":
      result = {
        action: "email.send",
        status: "pending",
        message: "Email send action queued (not yet implemented)",
      };
      break;

    case "email.summarize":
      result = {
        action: "email.summarize",
        status: "pending",
        message: "Email summarization queued (not yet implemented)",
      };
      break;

    case "email.triage":
      result = {
        action: "email.triage",
        status: "pending",
        message: "Email triage queued (not yet implemented)",
      };
      break;

    case "analytics.query":
      result = {
        action: "analytics.query",
        status: "pending",
        message: "Analytics query queued (not yet implemented)",
      };
      break;

    case "memory.add":
      try {
        // Upsert memory chunk
        const memoryResult = await createMemoryChunk({
          userId,
          workspaceId,
          chunkType: "user_input",
          chunkData: {
            text: rewritten,
            originalText: text,
            intent: classification.intent,
          } as any,
        });
        result = {
          action: "memory.add",
          status: "success",
          memoryId: memoryResult.id,
          message: "Memory chunk created successfully",
        };
      } catch (error) {
        result = {
          action: "memory.add",
          status: "error",
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }
      break;

    case "memory.recall":
      result = {
        action: "memory.recall",
        status: "pending",
        message: "Memory recall queued (not yet implemented)",
      };
      break;

    case "journal.create":
      result = {
        action: "journal.create",
        status: "success",
        message: "Journal entry created",
      };
      break;

    case "timeline.add":
      result = {
        action: "timeline.add",
        status: "pending",
        message: "Timeline event queued (not yet implemented)",
      };
      break;

    case "plan.create":
      result = {
        action: "plan.create",
        status: "pending",
        message: "Plan creation queued (not yet implemented)",
      };
      break;

    case "plan.execute":
      result = {
        action: "plan.execute",
        status: "pending",
        message: "Plan execution queued (not yet implemented)",
      };
      break;

    case "agent.run":
      result = {
        action: "agent.run",
        status: "pending",
        message: "Agent execution queued (not yet implemented)",
      };
      break;

    case "agent.status":
      result = {
        action: "agent.status",
        status: "pending",
        message: "Agent status query queued (not yet implemented)",
      };
      break;

    case "clinical.action":
      result = {
        action: "clinical.action",
        status: "pending",
        message: "Clinical action queued (not yet implemented)",
      };
      break;

    case "clinical.query":
      result = {
        action: "clinical.query",
        status: "pending",
        message: "Clinical query queued (not yet implemented)",
      };
      break;

    case "financial.action":
      result = {
        action: "financial.action",
        status: "pending",
        message: "Financial action queued (not yet implemented)",
      };
      break;

    case "financial.query":
      result = {
        action: "financial.query",
        status: "pending",
        message: "Financial query queued (not yet implemented)",
      };
      break;

    case "file.organize":
      result = {
        action: "file.organize",
        status: "pending",
        message: "File organization queued (not yet implemented)",
      };
      break;

    case "file.search":
      result = {
        action: "file.search",
        status: "pending",
        message: "File search queued (not yet implemented)",
      };
      break;

    case "schedule.create":
      result = {
        action: "schedule.create",
        status: "pending",
        message: "Schedule creation queued (not yet implemented)",
      };
      break;

    case "schedule.query":
      result = {
        action: "schedule.query",
        status: "pending",
        message: "Schedule query queued (not yet implemented)",
      };
      break;

    case "unknown":
    default:
      result = {
        action: "unknown",
        status: "error",
        message: "Could not determine intent from query",
      };
      break;
  }

  // Emit command completed/failed event
  try {
    if (result?.status === 'error' || agentResult?.status === 'error') {
      await emitEvent({
        type: 'jarvis.command.failed',
        source: 'jarvis.command',
        workspaceId,
        userId,
        correlationId,
        payload: {
          workspaceId,
          userId,
          commandName: 'routeJarvisCommand',
          errorMessage: result?.error || agentResult?.error || 'Unknown error',
          correlationId,
        },
      });
    } else {
      await emitEvent({
        type: 'jarvis.command.completed',
        source: 'jarvis.command',
        workspaceId,
        userId,
        correlationId,
        payload: {
          workspaceId,
          userId,
          commandName: 'routeJarvisCommand',
          resultSummary: result?.message || 'Command completed',
          correlationId,
        },
      });
    }
  } catch (error) {
    console.error('[RouteJarvisCommand] Failed to emit command completion event:', error);
  }

  // Step 5: Return consistent JSON envelope
  return {
    input: text,
    rewritten,
    intent: classification.intent,
    confidence: classification.confidence,
    result,
    agentResult,
  };
}
