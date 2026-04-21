// Plan executor - runs plans and updates status
import type { AgentContext, AgentResult } from "@/lib/jarvis/agents/types";
import type { Plan } from "./index";
import { findAgentForIntent } from "@/lib/jarvis/agents/registry";
import { createJarvisDb } from "@/lib/db/jarvis";
import type { Database } from "@/lib/supabase/types";

export async function runPlan(plan: Plan, ctx: AgentContext): Promise<AgentResult | null> {
  if (!plan.steps.length) return null;

  const step = plan.steps[0];
  const agent = findAgentForIntent(step.intent) ?? findAgentByName(step.agentName);

  if (!agent) {
    return {
      status: "error",
      agent: "unknown",
      summary: `No agent found for intent: ${step.intent}`,
      error: "AGENT_NOT_FOUND",
    };
  }

  const db = createJarvisDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;

  // Mark step as running
  if (step.id) {
    try {
      const updateQuery = (client as any)
        .from("jarvis_plan_steps")
        .update({
          status: "running",
        })
        .eq("id", step.id);
      const updateResult = await updateQuery;
      // Ignore result, just log errors if any
      if (updateResult?.error) {
        console.error("Failed to update step status to running:", updateResult.error);
      }
    } catch (error) {
      console.error("Error updating step status to running:", error);
    }
  }

  let result: AgentResult;

  try {
    result = await agent.run(ctx);
  } catch (err: any) {
    result = {
      status: "error",
      agent: agent.name,
      summary: "Agent execution failed.",
      error: String(err),
    };
  }

  // Update step status
  if (step.id) {
    try {
      const updateQuery = (client as any)
        .from("jarvis_plan_steps")
        .update({
          status: result.status === "success" ? "done" : "error",
        })
        .eq("id", step.id);
      const updateResult = await updateQuery;
      // Ignore result, just log errors if any
      if (updateResult?.error) {
        console.error("Failed to update step status:", updateResult.error);
      }
    } catch (error) {
      console.error("Error updating step status:", error);
    }
  }

  return result;
}

function findAgentByName(name: string) {
  const { getRegisteredAgents } = require("./../agents/registry");
  const agents = getRegisteredAgents() as any[];
  return agents.find((a) => a.name === name) ?? null;
}
