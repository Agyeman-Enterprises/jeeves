import type { ClinicalEvent } from "../types";
import type { Plan } from "../../planner/types";
import { createPlan } from "../../planner/planner";
import type { JarvisTaskClassification } from "../../types";

export async function createPlanForHospitalization(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Patient hospitalized: ${event.payload.patient_name || event.patient_id}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Hospitalization event requires multi-step clinical workflow",
      tags: ["clinical", "hospitalization", "urgent"],
    } as JarvisTaskClassification,
  });

  // Override default steps with hospitalization-specific workflow
  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "hospitalization_agent",
      input: {
        event,
        action: "pre_fetch_context",
        query: "Fetch patient meds, last encounters, diagnoses from Solopractice",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "tool",
      tool: "summarize",
      input: {
        content: event.payload.summary || JSON.stringify(event.payload),
        mode: "executive",
        query: "Summarize hospitalization context",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "hospitalization_agent",
      input: {
        event,
        action: "create_clinical_tasks",
        query: "Create tasks in Solopractice, notify MA/AI, mark chart",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "agent",
      agentSlug: "hospitalization_agent",
      input: {
        event,
        action: "queue_followup",
        query: "Schedule follow-up appointment 2-5 days post-discharge",
      },
      status: "PENDING",
    },
    {
      orderIndex: 4,
      type: "tool",
      tool: "memory.write",
      input: {
        query: `Hospitalization event for patient ${event.patient_id}`,
        payload: {
          title: "Hospitalization Event",
          content: JSON.stringify(event.payload),
          tags: ["clinical", "hospitalization"],
          source: "clinical_event",
        },
      },
      status: "PENDING",
    },
  ];

  plan.title = `Hospitalization Workflow: ${event.payload.patient_name || event.patient_id}`;
  return plan;
}

