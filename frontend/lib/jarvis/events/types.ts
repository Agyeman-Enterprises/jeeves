export type ClinicalEventType =
  // Hospitalization Events
  | "PATIENT_HOSPITALIZED"
  | "DISCHARGE_SUMMARY_RECEIVED"
  | "ED_VISIT_REPORTED"
  | "HOSPITAL_DOCS_UPLOADED"
  // Medication Events
  | "MED_REFILL_REQUESTED"
  | "MED_NONCOMPLIANCE_FLAG"
  | "PHARMACY_NOTE_RECEIVED"
  // Labs
  | "CRITICAL_LAB_RESULT"
  | "LAB_RESULT_RECEIVED"
  | "LAB_OVERDUE"
  // Scheduling
  | "FOLLOWUP_DUE"
  | "NEW_APPOINTMENT_BOOKED"
  | "APPOINTMENT_NO_SHOW"
  | "APPOINTMENT_RESCHEDULED"
  // Clinical Messages
  | "PATIENT_MESSAGE"
  | "SYMPTOM_UPDATE"
  | "NEW_FILE_UPLOADED"
  // Patient Journey Events
  | "LEAD_CREATED"
  | "INTAKE_FORM_SUBMITTED"
  | "PREVISIT_DATA_RECEIVED"
  | "MEDLIST_UPLOADED"
  | "SYMPTOMS_ENTERED"
  | "TASK_COMPLETED_BY_MA";

export type FinancialEventType =
  // Transaction-Level
  | "TXN_RECORDED"
  | "INCOME_RECORDED"
  | "EXPENSE_RECORDED"
  | "TRANSFER_RECORDED"
  | "PAYROLL_RUN"
  // Accounting / Entity-Level
  | "PERIOD_CLOSE"
  | "TAX_ESTIMATE_UPDATED"
  | "DEPRECIATION_SCHEDULE_UPDATED"
  | "ENTITY_BALANCE_UPDATED"
  | "CASHFLOW_FORECAST_UPDATED"
  // Alerts / Risks
  | "CASH_LOW_THRESHOLD"
  | "TAX_PAYMENT_DUE"
  | "UNUSUAL_SPEND_PATTERN"
  | "PROFITABILITY_DROP"
  | "HIGH_GL_EXPENSE_CATEGORY";

export type EventType = ClinicalEventType | FinancialEventType;

export type EventSource = "myhealthally" | "solopractice" | "bookadoc" | "medrx" | "taxrx" | "entitytaxpro" | "nexus" | "shopify" | "clinic_billing" | "accessmd" | "marketing" | "system";

export type EventStatus = "NEW" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface ClinicalEvent {
  id?: string;
  source: EventSource;
  type: ClinicalEventType;
  patient_id?: string | null;
  user_id: string;
  payload: Record<string, any>;
  status?: EventStatus;
  created_at?: string;
}

export interface FinancialEvent {
  id?: string;
  source: EventSource;
  type: FinancialEventType;
  entity_id?: string | null;
  user_id: string;
  amount?: number;
  currency?: string;
  category?: string;
  payload: Record<string, any>;
  status?: EventStatus;
  created_at?: string;
}

export type SystemEvent = ClinicalEvent | FinancialEvent;
