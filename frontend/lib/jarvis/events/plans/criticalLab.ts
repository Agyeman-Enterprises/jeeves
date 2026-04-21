import type { ClinicalEvent } from "../types";
import type { Plan } from "../../planner/types";
import { createPlan } from "../../planner/planner";
import type { JarvisTaskClassification } from "../../types";

export async function createPlanForCriticalLab(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Critical lab result: ${event.payload.lab_name || "lab"}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "ACTION",
      confidence: 0.95,
      reason: "Critical lab result requires immediate clinical attention",
      tags: ["clinical", "lab", "critical", "urgent"],
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
        query: "Summarize critical lab result and clinical significance",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "hospitalization_agent", // Reuse for urgent clinical actions
      input: {
        event,
        action: "notify_md_urgent",
        query: "Notify MD immediately for critical lab result",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "tool",
      tool: "memory.write",
      input: {
        query: `Critical lab: ${event.payload.lab_name}`,
        payload: {
          title: "Critical Lab Result",
          content: JSON.stringify(event.payload),
          tags: ["clinical", "lab", "critical"],
          source: "clinical_event",
          importance: "high",
        },
      },
      status: "PENDING",
    },
  ];

  plan.title = `Critical Lab: ${event.payload.lab_name || "lab result"}`;
  plan.status = "RUNNING"; // Critical labs start immediately
  return plan;
}

