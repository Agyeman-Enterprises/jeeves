import type { ClinicalEvent, FinancialEvent, SystemEvent } from "./types";
import { createPlanForHospitalization } from "./plans/hospitalization";
import { createPlanForDischarge } from "./plans/discharge";
import { createPlanForRefill } from "./plans/refill";
import { createPlanForMessage } from "./plans/message";
import { createPlanForCriticalLab } from "./plans/criticalLab";
import { createPlanForExpense } from "./plans/financial/expense";
import { createPlanForTaxUpdate } from "./plans/financial/tax";
import { createPlanForCashflowAlert } from "./plans/financial/cashflow";
import { createPlanForLeadCapture } from "./plans/patient-journey/leadCapture";
import { createPlanForIntake } from "./plans/patient-journey/intake";
import { createPlanForScheduling } from "./plans/patient-journey/scheduling";
import { createPlanForEncounter } from "./plans/patient-journey/encounter";
import { createPlanForOrders } from "./plans/patient-journey/orders";
import { createPlanForOngoingCare } from "./plans/patient-journey/ongoingCare";
import { createPlanForRetention } from "./plans/patient-journey/retention";

export async function handleClinicalEvent(event: ClinicalEvent) {
  switch (event.type) {
    // Patient Journey Events
    case "LEAD_CREATED":
      return createPlanForLeadCapture(event);

    case "INTAKE_FORM_SUBMITTED":
    case "PREVISIT_DATA_RECEIVED":
    case "MEDLIST_UPLOADED":
    case "SYMPTOMS_ENTERED":
      return createPlanForIntake(event);

    case "NEW_APPOINTMENT_BOOKED":
    case "APPOINTMENT_RESCHEDULED":
    case "APPOINTMENT_NO_SHOW":
      return createPlanForScheduling(event);

    // Encounter support (triggered during visit)
    // This would be triggered by a separate event or API call during encounter

    // Orders, Tasks, Refills, Follow-Ups
    case "LAB_RESULT_RECEIVED":
    case "TASK_COMPLETED_BY_MA":
    case "FOLLOWUP_DUE":
      return createPlanForOrders(event);

    // Ongoing Care
    case "PATIENT_HOSPITALIZED":
      return createPlanForHospitalization(event);

    case "DISCHARGE_SUMMARY_RECEIVED":
      // Check if this is part of ongoing care or initial discharge
      if (event.payload.is_ongoing_care) {
        return createPlanForOngoingCare(event);
      }
      return createPlanForDischarge(event);

    case "MED_REFILL_REQUESTED":
      return createPlanForRefill(event);

    case "PATIENT_MESSAGE":
      return createPlanForOngoingCare(event);

    case "CRITICAL_LAB_RESULT":
      return createPlanForCriticalLab(event);

    default:
      return null;
  }
}

export async function handleFinancialEvent(event: FinancialEvent) {
  switch (event.type) {
    case "EXPENSE_RECORDED":
      return createPlanForExpense(event);

    case "TAX_ESTIMATE_UPDATED":
      return createPlanForTaxUpdate(event);

    case "CASH_LOW_THRESHOLD":
    case "PROFITABILITY_DROP":
      return createPlanForCashflowAlert(event);

    default:
      return null;
  }
}

export async function handleSystemEvent(event: SystemEvent) {
  // Route to appropriate handler based on event type
  if ("patient_id" in event) {
    return handleClinicalEvent(event as ClinicalEvent);
  } else if ("entity_id" in event || "amount" in event) {
    return handleFinancialEvent(event as FinancialEvent);
  }
  return null;
}

