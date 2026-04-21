import type { ClinicalEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForLeadCapture(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Lead captured: ${event.payload.lead_name || event.payload.email || "new lead"}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "patient-journey" },
    classification: {
      kind: "ACTION",
      confidence: 0.9,
      reason: "Lead capture requires pipeline assignment and intake automation",
      tags: ["patient-journey", "lead", "intake"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "intake_agent",
      input: {
        event,
        action: "identify_clinic_service",
        query: "Identify which clinic/service line: Bookadoc (telehealth), MedRx (GLP), Ohimaa General, Pain, Aesthetics, etc.",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "intake_agent",
      input: {
        event,
        action: "assign_pipeline_stage",
        query: "Assign pipeline stage: NEW → INTAKE_SENT → FORM_COMPLETED → APPOINTMENT_BOOKED",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "intake_agent",
      input: {
        event,
        action: "send_intake_forms",
        query: "Send automated intake forms, collect demographics, meds, history",
      },
      status: "PENDING",
    },
    {
      orderIndex: 3,
      type: "agent",
      agentSlug: "intake_agent",
      input: {
        event,
        action: "sync_to_solopractice",
        query: "Sync lead data into Solopractice",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Lead Capture: ${event.payload.lead_name || event.payload.email || "new lead"}`;
  return plan;
}

