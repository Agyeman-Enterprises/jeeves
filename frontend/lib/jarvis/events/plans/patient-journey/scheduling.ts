import type { ClinicalEvent } from "../../types";
import type { Plan } from "../../../planner/types";
import { createPlan } from "../../../planner/planner";
import type { JarvisTaskClassification } from "../../../types";

export async function createPlanForScheduling(
  event: ClinicalEvent
): Promise<Plan | null> {
  const plan = await createPlan({
    user: { userId: event.user_id, workspaceId: null },
    query: `Appointment ${event.type === "APPOINTMENT_RESCHEDULED" ? "rescheduled" : "booked"}: ${event.payload.patient_name || event.patient_id}`,
    messages: [],
    workspaceContext: { app: "jarvis", location: "patient-journey" },
    classification: {
      kind: "SCHEDULE",
      confidence: 0.9,
      reason: "Appointment booking requires validation, reminders, and chart prep",
      tags: ["patient-journey", "scheduling", "appointment"],
    } as JarvisTaskClassification,
  });

  plan.steps = [
    {
      orderIndex: 0,
      type: "agent",
      agentSlug: "scheduler_agent",
      input: {
        event,
        action: "validate_appointment",
        query: "Ensure no conflicts, correct visit type, right location (CA/HI/GU), insurance coverage",
      },
      status: "PENDING",
    },
    {
      orderIndex: 1,
      type: "agent",
      agentSlug: "scheduler_agent",
      input: {
        event,
        action: "setup_reminders",
        query: "Setup 24h reminder, 2h reminder, automatic Zoom/Ghexit link, pre-visit questionnaire",
      },
      status: "PENDING",
    },
    {
      orderIndex: 2,
      type: "agent",
      agentSlug: "chartprep_agent",
      input: {
        event,
        action: "flag_high_risk",
        query: "If patient appears high-risk: flag chart for more prep, extend appointment time, suggest labs ahead of visit",
      },
      status: "PENDING",
    },
  ];

  plan.title = `Appointment ${event.type === "APPOINTMENT_RESCHEDULED" ? "Rescheduling" : "Booking"}: ${event.payload.patient_name || event.patient_id}`;
  return plan;
}

