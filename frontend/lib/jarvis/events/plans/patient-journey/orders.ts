import type { ClinicalEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForOrders(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Orders/Tasks/Refills: ${event.payload.patient_name || event.patient_id}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "clinical" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Orders require analysis, safety checks, and follow-up scheduling",
      tags: ["patient-journey", "orders", "clinical"],
    } as JarvisTaskClassification,
  });

  const eventType = event.type;
  const steps: any[] = [];

  if (eventType === "LAB_RESULT_RECEIVED") {
    steps.push({
      orderIndex: 0,
      type: "agent",
      agentSlug: "lab_interpretation_agent",
      input: {
        event,
        action: "analyze_labs",
        query: "Analyze lab results: flag abnormal, suggest changes, summarize course",
      },
      status: "PENDING",
    });
  }

  if (eventType === "MED_REFILL_REQUESTED") {
    steps.push({
      orderIndex: steps.length,
      type: "agent",
      agentSlug: "med_refill_agent",
      input: {
        event,
        action: "safety_check_and_draft",
        query: "Safety check, draft orders, escalate only high-risk",
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

  // Follow guideline-based workflows
  steps.push({
    orderIndex: steps.length,
    type: "agent",
    agentSlug: "glp_monitor_agent",
    input: {
      event,
      action: "check_glp_guidelines",
      query: "Follow GLP guidelines: 3 months for GLP, 2-4 weeks for med changes",
      status: "PENDING",
    },
  });

  steps.push({
    orderIndex: steps.length,
    type: "agent",
    agentSlug: "followup_agent",
    input: {
      event,
      action: "auto_schedule_followups",
      query: "Auto-schedule follow-ups: 2-4 weeks for med changes, 3 months for GLP, 6 months for chronic disease reviews",
      status: "PENDING",
    },
  });

  plan.steps = steps;
  plan.title = `Orders Processing: ${event.payload.patient_name || event.patient_id}`;
  return plan;
}

