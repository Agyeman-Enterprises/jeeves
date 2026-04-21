import type {
  JarvisCommandInput,
  JarvisTaskClassification,
} from "../types";
import type { Plan, PlanStep } from "./types";

interface CreatePlanArgs extends JarvisCommandInput {
  classification: JarvisTaskClassification;
}

export async function createPlan(args: CreatePlanArgs): Promise<Plan> {
  const { user, workspaceContext, classification, query } = args;

  const base: Plan = {
    user,
    workspaceId: workspaceContext?.app ? workspaceContext.app : null,
    title: `Plan for: ${query}`,
    status: "PENDING",
    classification,
    steps: [],
  };

  const steps: PlanStep[] = [];

  switch (classification.kind) {
    case "SCHEDULE":
      steps.push({
        orderIndex: 0,
        type: "tool",
        tool: "schedule.create",
        input: { query },
        status: "PENDING",
      });
      break;

    case "EMAIL":
      steps.push({
        orderIndex: 0,
        type: "tool",
        tool: "email.draft",
        input: { query },
        status: "PENDING",
      });
      break;

    case "ANALYTICS":
      steps.push({
        orderIndex: 0,
        type: "tool",
        tool: "analytics.summary",
        input: { query, workspaceContext },
        status: "PENDING",
      });
      break;

    // Example: hospitalization workflow -> agent-based
    default:
      // For now: generic plan with single agent
      steps.push({
        orderIndex: 0,
        type: "agent",
        agentSlug: "hospitalization_agent", // we will override this from events
        input: { query, workspaceContext },
        status: "PENDING",
      });
  }

  base.steps = steps;
  return base;
}

