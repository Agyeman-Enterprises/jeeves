import type { FinancialEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForTaxUpdate(
  event: FinancialEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Tax estimate updated: ${event.payload.entity_name || "entity"}`,
    messages: [],
    workspaceContext: { app: "nexus", location: "financial" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Tax estimate update requires position review and action planning",
      tags: ["financial", "tax", "planning"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "tool",
      tool: "summarize",
      input: {
        content: JSON.stringify(event.payload),
        mode: "executive",
        query: "Summarize tax position by entity and overall",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "tax_prep_agent",
      input: {
        event,
        action: "get_safe_harbor_recommendations",
        query: "Ask Nexus for safe harbor recommendations",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "tax_prep_agent",
      input: {
        event,
        action: "create_tax_tasks",
        query: "Create tasks: move $X into tax reserve account, schedule payment by date",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "tool",
      tool: "memory.write",
      input: {
        query: `Tax estimate update: ${event.payload.entity_name || "entity"}`,
        payload: {
          title: "Tax Estimate Update",
          content: JSON.stringify(event.payload),
          tags: ["financial", "tax"],
          source: "taxrx",
          importance: "high",
        },
      },
      status: "PENDING",
    },
  ];

  plan.title = `Tax Position Update: ${event.payload.entity_name || "entity"}`;
  return plan;
}

