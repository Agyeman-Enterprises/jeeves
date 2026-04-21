import type { FinancialEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForCashflowAlert(
  event: FinancialEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Cash flow alert: ${event.payload.entity_name || "entity"}`,
    messages: [],
    workspaceContext: { app: "nexus", location: "financial" },
    classification: {
      kind: "ACTION",
      confidence: 0.95,
      reason: "Cash flow alert requires immediate analysis and action planning",
      tags: ["financial", "cashflow", "urgent", "alert"],
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
        query: "Summarize the driver: higher rent? less revenue? more staff?",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "cashflow_monitor_agent",
      input: {
        event,
        action: "suggest_options",
        query: "Suggest options: cut expenses, promote higher-margin services, raise prices",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "cashflow_monitor_agent",
      input: {
        event,
        action: "execute_if_approved",
        query: "If approved: call pricing change routines, campaign triggers, schedule adjustments",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Cash Flow Alert: ${event.payload.entity_name || "entity"}`;
  plan.status = "RUNNING"; // Cash flow alerts start immediately
  return plan;
}

