// Planner - builds plans for agent execution
import type { AgentContext } from "@/lib/jarvis/agents/types";
import { findAgentForIntent } from "@/lib/jarvis/agents/registry";
import { createJarvisDb } from "@/lib/db/jarvis";
import type { Database } from "@/lib/supabase/types";

export type PlanStep = {
  id?: string;
  agentName: string;
  intent: string;
  status: "pending" | "running" | "done" | "error";
  order: number;
};

export type Plan = {
  id?: string;
  userId: string;
  workspaceId: string;
  intent: string;
  steps: PlanStep[];
};

export async function createPlanForIntent(ctx: AgentContext): Promise<Plan | null> {
  const agent = findAgentForIntent(ctx.intent);
  if (!agent) {
    return null;
  }

  const db = createJarvisDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;

  // Insert into jarvis_plans
  const planResult = await client
    .from("jarvis_plans")
    .insert({
      user_id: ctx.userId,
      workspace_id: ctx.workspaceId,
      intent: ctx.intent,
      name: `Plan for ${ctx.intent}`,
    } as any)
    .select("*")
    .single();

  const { data: planRow, error: planError } = planResult as { data: any; error: any };

  if (planError || !planRow) {
    console.error("Failed to create plan:", planError);
    return null;
  }

  const stepResult = await client
    .from("jarvis_plan_steps")
    .insert({
      user_id: ctx.userId,
      workspace_id: ctx.workspaceId,
      plan_id: planRow.id,
      order: 1,
      agent_name: agent.name,
      intent: ctx.intent,
      status: "pending",
    } as any)
    .select("*")
    .single();

  const { data: stepRow, error: stepError } = stepResult as { data: any; error: any };

  if (stepError || !stepRow) {
    console.error("Failed to create plan step:", stepError);
    return null;
  }

  const plan: Plan = {
    id: planRow.id,
    userId: ctx.userId,
    workspaceId: ctx.workspaceId,
    intent: ctx.intent,
    steps: [
      {
        id: stepRow.id,
        agentName: agent.name,
        intent: ctx.intent,
        status: "pending",
        order: 1,
      },
    ],
  };

  return plan;
}

