import type { ClinicalEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForOngoingCare(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Ongoing care: ${event.payload.patient_name || event.patient_id}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Ongoing care requires triage, monitoring, and task creation",
      tags: ["patient-journey", "ongoing-care", "monitoring"],
    } as JarvisTaskClassification,
  });

  const eventType = event.type;
  const steps: any[] = [];

  if (eventType === "PATIENT_MESSAGE") {
    steps.push({
      orderIndex: steps.length,
      type: "agent",
      agentSlug: "triage_agent",
      input: {
        event,
        action: "triage_message",
        query: "Automatically triage patient message, escalate to MD only when needed",
      },
      status: "PENDING",
    });
  }

  if (eventType === "PATIENT_HOSPITALIZED") {
    steps.push({
      orderIndex: steps.length,
      type: "agent",
      agentSlug: "hospitalization_agent",
      input: {
        event,
        action: "process_hospitalization",
        query: "Process hospitalization, summarize visit, update treatment plans",
      },
      status: "PENDING",
    });
  }

  if (eventType === "DISCHARGE_SUMMARY_RECEIVED") {
    steps.push({
      orderIndex: steps.length,
      type: "agent",
      agentSlug: "discharge_agent",
      input: {
        event,
        action: "process_discharge",
        query: "Process discharge summary, update treatment plans",
      },
      status: "PENDING",
    });
  }

  steps.push({
    orderIndex: steps.length,
    type: "agent",
    agentSlug: "carecontinuity_agent",
    input: {
      event,
      action: "create_tasks",
      query: "Create tasks for MA/AI, ensure continuity of care",
      status: "PENDING",
    },
  });

  plan.steps = steps;
  plan.title = `Ongoing Care: ${event.payload.patient_name || event.patient_id}`;
  return plan;
}

