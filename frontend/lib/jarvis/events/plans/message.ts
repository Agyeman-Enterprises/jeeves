import type { ClinicalEvent } from "../types";
import type { Plan } from "../../planner/types";
import { createPlan } from "../../planner/planner";
import type { JarvisTaskClassification } from "../../types";

export async function createPlanForMessage(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Patient message: ${event.payload.subject || "message"}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "EMAIL",
      confidence: 0.8,
      reason: "Patient message requires triage and response",
      tags: ["clinical", "message", "patient"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "tool",
      tool: "summarize",
      input: {
        content: event.payload.message || JSON.stringify(event.payload),
        mode: "email",
        query: "Summarize patient message for triage",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "tool",
      tool: "memory.write",
      input: {
        query: `Patient message: ${event.payload.subject}`,
        payload: {
          title: "Patient Message",
          content: event.payload.message || JSON.stringify(event.payload),
          tags: ["clinical", "message"],
          source: "myhealthally",
        },
      },
      status: "PENDING",
    },
  ];

  plan.title = `Patient Message: ${event.payload.subject || "message"}`;
  return plan;
}

