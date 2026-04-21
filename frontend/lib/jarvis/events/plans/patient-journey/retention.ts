import type { ClinicalEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForRetention(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Patient retention/reactivation: ${event.payload.patient_name || event.patient_id || "inactive patients"}`,
    messages: [],
    workspaceContext: { app: "nexus", location: "patient-journey" },
    classification: {
      kind: "ACTION",
      confidence: 0.85,
      reason: "Retention requires reactivation workflows and engagement",
      tags: ["patient-journey", "retention", "reactivation"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "patient_engagement_agent",
      input: {
        event,
        action: "identify_inactive_patients",
        query: "Identify: inactive >90 days, overdue GLP follow-ups, chronic disease no follow-up, ghosted after prescriptions, finished intake but never booked",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "reactivation_agent",
      input: {
        event,
        action: "create_reactivation_flows",
        query: "Create reactivation flows: 'We noticed you might be due for your next visit—would you like to schedule?', 'You're eligible for personalized wellness plan updates.', 'Your labs suggest we should review your medication soon.'",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "marketing_agent",
      input: {
        event,
        action: "send_engagement_campaigns",
        query: "Send targeted engagement campaigns based on patient profile",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Patient Retention/Reactivation: ${event.payload.patient_name || "inactive patients"}`;
  return plan;
}

