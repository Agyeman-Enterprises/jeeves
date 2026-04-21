import { supabaseServer } from "@/lib/supabase/server";
import type { SystemEvent } from "../events/types";
import type { Signal, SignalType, SignalSeverity } from "./types";
import type { AggregatedEvents } from "./aggregator";

export async function extractSignals(
  userId: string,
  events: AggregatedEvents
): Promise<Signal[]> {
  const signals: Signal[] = [];

  // Extract clinical signals
  for (const event of events.clinical) {
    const evt = event as any;
    
    if (evt.type === "PATIENT_HOSPITALIZED") {
      signals.push({
        user_id: userId,
        type: "CLINICAL",
        severity: "HIGH",
        domain: "clinical",
        title: "Patient Hospitalized",
        description: `Patient ${evt.payload?.patient_name || evt.patient_id} was hospitalized`,
        payload: evt.payload,
      });
    }

    if (evt.type === "CRITICAL_LAB_RESULT") {
      signals.push({
        user_id: userId,
        type: "CLINICAL",
        severity: "CRITICAL",
        domain: "clinical",
        title: "Critical Lab Result",
        description: `Critical lab result for patient ${evt.payload?.patient_name || evt.patient_id}`,
        payload: evt.payload,
      });
    }

    if (evt.type === "MED_REFILL_REQUESTED") {
      signals.push({
        user_id: userId,
        type: "CLINICAL",
        severity: "MEDIUM",
        domain: "clinical",
        title: "Medication Refill Requested",
        description: `Refill requested for ${evt.payload?.medication_name || "medication"}`,
        payload: evt.payload,
      });
    }

    if (evt.type === "APPOINTMENT_NO_SHOW") {
      signals.push({
        user_id: userId,
        type: "OPERATIONAL",
        severity: "LOW",
        domain: "ops",
        title: "Appointment No-Show",
        description: `Patient ${evt.payload?.patient_name || evt.patient_id} did not show`,
        payload: evt.payload,
      });
    }
  }

  // Extract financial signals
  for (const event of events.financial) {
    const evt = event as any;
    
    if (evt.type === "CASH_LOW_THRESHOLD") {
      signals.push({
        user_id: userId,
        type: "FINANCIAL",
        severity: "HIGH",
        domain: "finance",
        title: "Cash Flow Alert",
        description: `Cash below threshold for ${evt.payload?.entity_name || "entity"}`,
        payload: evt.payload,
      });
    }

    if (evt.type === "TAX_PAYMENT_DUE") {
      signals.push({
        user_id: userId,
        type: "FINANCIAL",
        severity: "HIGH",
        domain: "finance",
        title: "Tax Payment Due",
        description: `Tax payment due: $${evt.payload?.amount || 0}`,
        payload: evt.payload,
      });
    }

    if (evt.type === "PROFITABILITY_DROP") {
      signals.push({
        user_id: userId,
        type: "FINANCIAL",
        severity: "MEDIUM",
        domain: "finance",
        title: "Profitability Drop",
        description: `Profitability dropped for ${evt.payload?.entity_name || "entity"}`,
        payload: evt.payload,
      });
    }
  }

  // Extract system signals
  for (const event of events.system) {
    const evt = event as any;
    
    // Agent degradation signals would come from agent_runs
    // This is a placeholder for system health signals
  }

  // Store signals in database
  if (signals.length > 0) {
    await supabaseServer
      .from("jarvis_signals")
      .insert(signals.map(s => ({
        user_id: s.user_id,
        type: s.type,
        severity: s.severity,
        domain: s.domain,
        title: s.title,
        description: s.description,
        payload: s.payload,
      })) as any);
  }

  return signals;
}

