import type { ClinicalEvent } from "../types";
import type { Plan } from "../../planner/types";
import { createPlan } from "../../planner/planner";
import type { JarvisTaskClassification } from "../../types";

export async function createPlanForRefill(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Med refill requested: ${event.payload.medication_name || "medication"}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "ACTION",
      confidence: 0.85,
      reason: "Medication refill requires safety check and clinical review",
      tags: ["clinical", "medication", "refill"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "med_refill_agent",
      input: {
        event,
        action: "pull_patient_profile",
        query: "Pull patient med + risk profile from Solopractice",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "med_refill_agent",
      input: {
        event,
        action: "safety_check",
        query: "LLM safety check comparing conditions, last labs",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "med_refill_agent",
      input: {
        event,
        action: "check_glp_eligibility",
        query: "If GLP: check MedRx model for eligibility",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "agent",
      agentSlug: "med_refill_agent",
      input: {
        event,
        action: "draft_refill_note",
        query: "Draft refill note for Solopractice",
      },
      status: "PENDING",
    },
    {
      orderIndex: 4,
      type: "agent",
      agentSlug: "med_refill_agent",
      input: {
        event,
        action: "create_refill_task",
        query: "Create Solopractice refill task",
      },
      status: "PENDING",
    },
    {
      orderIndex: 5,
      type: "agent",
      agentSlug: "med_refill_agent",
      input: {
        event,
        action: "notify_if_restricted",
        query: "Notify MD only for restricted meds",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Med Refill: ${event.payload.medication_name || "medication"}`;
  return plan;
}

