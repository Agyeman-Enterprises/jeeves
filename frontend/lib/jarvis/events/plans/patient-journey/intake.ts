import type { ClinicalEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForIntake(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Intake form submitted: ${event.payload.patient_name || event.patient_id}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "patient-journey" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Intake submission requires chart prep packet creation",
      tags: ["patient-journey", "intake", "chart-prep"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "chartprep_agent",
      input: {
        event,
        action: "create_chart_prep_packet",
        query: "Create chart-prep packet: patient summary, key risks, med interactions, missing labs, GLP eligibility, suggested questions, suggested orders",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "med_safety_agent",
      input: {
        event,
        action: "check_med_interactions",
        query: "Check medication interactions and flag risks",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "glp_screening_agent",
      input: {
        event,
        action: "assess_glp_eligibility",
        query: "Assess GLP eligibility if applicable",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "tool",
      tool: "memory.write",
      input: {
        query: `Intake completed for patient ${event.payload.patient_name || event.patient_id}`,
        payload: {
          title: "Patient Intake",
          content: JSON.stringify(event.payload),
          tags: ["patient-journey", "intake"],
          source: "intake_form",
        },
      },
      status: "PENDING",
    },
  ];

  plan.title = `Intake Processing: ${event.payload.patient_name || event.patient_id}`;
  return plan;
}

