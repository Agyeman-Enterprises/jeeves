import type { FinancialEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForExpense(
  event: FinancialEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Expense recorded: ${event.payload.description || event.category || "expense"}`,
    messages: [],
    workspaceContext: { app: "nexus", location: "financial" },
    classification: {
      kind: "ACTION",
      confidence: 0.8,
      reason: "Expense requires categorization and tax strategy review",
      tags: ["financial", "expense", "tax"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "expense_categorization_agent",
      input: {
        event,
        action: "categorize_expense",
        query: "Tag expense as clinical vs R&D vs admin vs personal",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "expense_categorization_agent",
      input: {
        event,
        action: "check_threshold",
        query: "If above threshold, ask if recurring or one-off",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "expense_categorization_agent",
      input: {
        event,
        action: "tax_strategy_check",
        query: "If deductible and large, add to Tax Strategy Watchlist",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "agent",
      agentSlug: "expense_categorization_agent",
      input: {
        event,
        action: "equipment_check",
        query: "If equipment, update depreciation schedule or flag for EntityTaxPro",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Expense Processing: ${event.payload.description || event.category}`;
  return plan;
}

