// Basic agent implementations
import { JarvisAgent, AgentContext, AgentResult } from "./types";
import { storeMemoryChunk } from "@/lib/jarvis/memory/service";

export const EchoAgent: JarvisAgent = {
  name: "echo_agent",
  description: "Echoes back the rewritten command.",
  supportedIntents: ["debug.echo"],
  async run(ctx: AgentContext): Promise<AgentResult> {
    return {
      status: "success",
      agent: "echo_agent",
      summary: `Echo: ${ctx.rewritten}`,
      data: {
        input: ctx.input,
        rewritten: ctx.rewritten,
      },
    };
  },
};

export const MemoryAgent: JarvisAgent = {
  name: "memory_agent",
  description: "Stores the rewritten text as a memory chunk.",
  supportedIntents: ["memory.add"],
  async run(ctx: AgentContext): Promise<AgentResult> {
    try {
      const memory = await storeMemoryChunk({
        userId: ctx.userId,
        workspaceId: ctx.workspaceId,
        content: ctx.rewritten,
        source: "agent.memory",
      });

      return {
        status: "success",
        agent: "memory_agent",
        summary: "Stored memory chunk.",
        data: { memoryId: memory.id },
      };
    } catch (err: any) {
      return {
        status: "error",
        agent: "memory_agent",
        summary: "Failed to store memory chunk.",
        error: String(err),
      };
    }
  },
};

export const ClassifierDebugAgent: JarvisAgent = {
  name: "classifier_debug_agent",
  description: "Returns classification / routing-related debug info.",
  supportedIntents: ["debug.classifier"],
  async run(ctx: AgentContext): Promise<AgentResult> {
    return {
      status: "success",
      agent: "classifier_debug_agent",
      summary: `Debug info for intent: ${ctx.intent}`,
      data: {
        intent: ctx.intent,
        metadata: ctx.metadata ?? {},
      },
    };
  },
};

export const basicAgents: JarvisAgent[] = [
  EchoAgent,
  MemoryAgent,
  ClassifierDebugAgent,
];

