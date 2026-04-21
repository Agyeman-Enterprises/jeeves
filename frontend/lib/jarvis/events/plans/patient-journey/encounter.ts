import type { ClinicalEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForEncounter(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Encounter support: ${event.payload.patient_name || event.patient_id}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Encounter requires chart prep retrieval and clinical support",
      tags: ["patient-journey", "encounter", "clinical"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "chartprep_agent",
      input: {
        event,
        action: "retrieve_chart_prep",
        query: "Retrieve chart prep packet for encounter",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "clinical_support_agent",
      input: {
        event,
        action: "suggest_problem_list",
        query: "Suggest problem list updates, structured note fields, assessment & plan items",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "clinical_support_agent",
      input: {
        event,
        action: "suggest_glp_dosing",
        query: "Suggest GLP dosing changes if applicable",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "agent",
      agentSlug: "clinical_support_agent",
      input: {
        event,
        action: "suggest_followup_intervals",
        query: "Suggest follow-up intervals, medical justification paragraphs, ICD/CPT suggestions",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Encounter Support: ${event.payload.patient_name || event.patient_id}`;
  return plan;
}

