import type { ClinicalEvent } from "../types";
import type { Plan } from "../../planner/types";
import { createPlan } from "../../planner/planner";
import type { JarvisTaskClassification } from "../../types";

export async function createPlanForDischarge(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Discharge summary received: ${event.payload.patient_name || event.patient_id}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Discharge summary requires medication reconciliation and follow-up planning",
      tags: ["clinical", "discharge", "medication"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "tool",
      tool: "summarize",
      input: {
        content: event.payload.discharge_summary || JSON.stringify(event.payload),
        mode: "meeting",
        query: "Extract admission reason, hospital course, meds changed, follow-ups required",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "discharge_agent",
      input: {
        event,
        action: "compare_med_lists",
        query: "Compare discharge med list with Solopractice med list, identify mismatches and interactions",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "discharge_agent",
      input: {
        event,
        action: "create_clinical_actions",
        query: "Update problem list, update med list, create follow-up visit",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "agent",
      agentSlug: "discharge_agent",
      input: {
        event,
        action: "notify_if_needed",
        query: "Notify MD only if high-risk items detected",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Discharge Summary Processing: ${event.payload.patient_name || event.patient_id}`;
  return plan;
}

