import type { ClinicalEvent } from "./types";

export interface SafetyCheckResult {
  isUrgent: boolean;
  requiresMDApproval: boolean;
  requiresNotification: boolean;
  riskLevel: "low" | "medium" | "high" | "critical";
  reasons: string[];
}

const URGENT_KEYWORDS = [
  "chest pain",
  "syncope",
  "suicidal ideation",
  "suicide",
  "stroke",
  "chest pressure",
  "shortness of breath",
  "difficulty breathing",
];

const HIGH_RISK_LABS = [
  "troponin",
  "ck-mb",
  "bnp",
  "d-dimer",
  "glucose",
  "potassium",
  "creatinine",
];

const CONTROLLED_SUBSTANCES = [
  "oxycodone",
  "hydrocodone",
  "morphine",
  "fentanyl",
  "adderall",
  "ritalin",
  "xanax",
  "valium",
  "ativan",
];

export function checkClinicalSafety(event: ClinicalEvent): SafetyCheckResult {
  const result: SafetyCheckResult = {
    isUrgent: false,
    requiresMDApproval: false,
    requiresNotification: false,
    riskLevel: "low",
    reasons: [],
  };

  const payloadStr = JSON.stringify(event.payload).toLowerCase();
  const eventType = event.type;

  // Check for urgent keywords
  for (const keyword of URGENT_KEYWORDS) {
    if (payloadStr.includes(keyword)) {
      result.isUrgent = true;
      result.requiresNotification = true;
      result.riskLevel = "critical";
      result.reasons.push(`Urgent keyword detected: ${keyword}`);
      break;
    }
  }

  // Check for critical lab results
  if (eventType === "CRITICAL_LAB_RESULT") {
    result.isUrgent = true;
    result.requiresNotification = true;
    result.riskLevel = "critical";
    result.reasons.push("Critical lab result detected");

    // Check for specific high-risk labs
    for (const lab of HIGH_RISK_LABS) {
      if (payloadStr.includes(lab)) {
        result.riskLevel = "critical";
        result.reasons.push(`High-risk lab: ${lab}`);
        break;
      }
    }
  }

  // Check for controlled substances in refill requests
  if (eventType === "MED_REFILL_REQUESTED") {
    const medName = (event.payload.medication_name || "").toLowerCase();
    for (const substance of CONTROLLED_SUBSTANCES) {
      if (medName.includes(substance)) {
        result.requiresMDApproval = true;
        result.requiresNotification = true;
        result.riskLevel = result.riskLevel === "low" ? "high" : result.riskLevel;
        result.reasons.push(`Controlled substance refill: ${substance}`);
        break;
      }
    }
  }

  // Check for dangerous med interactions (placeholder - would need actual interaction checking)
  if (event.payload.dangerous_interaction) {
    result.requiresMDApproval = true;
    result.requiresNotification = true;
    result.riskLevel = "high";
    result.reasons.push("Dangerous medication interaction detected");
  }

  // Check for new GLP starts without labs
  if (
    eventType === "MED_REFILL_REQUESTED" &&
    payloadStr.includes("glp") &&
    !event.payload.has_recent_labs
  ) {
    result.requiresMDApproval = true;
    result.requiresNotification = true;
    result.riskLevel = "high";
    result.reasons.push("New GLP start without recent labs");
  }

  return result;
}

