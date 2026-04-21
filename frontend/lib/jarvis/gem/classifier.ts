import type { EventCategory, EventMeshEvent } from "./types";

export async function classifyEvent(
  eventType: string,
  payload: Record<string, any>,
  source: string
): Promise<{
  category: EventCategory;
  classification: Record<string, any>;
}> {
  // Rule-based classification first (fast)
  const ruleBasedCategory = classifyByRules(eventType, payload, source);
  
  if (ruleBasedCategory) {
    return {
      category: ruleBasedCategory,
      classification: {
        method: "rule_based",
        confidence: 0.9,
        rules_matched: [eventType],
      },
    };
  }

  // LLM-based classification for ambiguous events
  // In production, this would use the LLM router
  const llmCategory = await classifyWithLLM(eventType, payload, source);

  return {
    category: llmCategory,
    classification: {
      method: "llm_based",
      confidence: 0.7,
    },
  };
}

function classifyByRules(
  eventType: string,
  payload: Record<string, any>,
  source: string
): EventCategory | null {
  // Clinical events
  const clinicalPatterns = [
    "PATIENT_MESSAGE",
    "LAB_RESULT",
    "HOSPITALIZATION",
    "MEDICATION",
    "GLP",
    "DISCHARGE",
    "NO_SHOW",
    "VITALS",
    "CLINICAL",
  ];

  if (clinicalPatterns.some((p) => eventType.includes(p))) {
    return "CLINICAL";
  }

  if (source === "myhealthally" || source === "solopractice" || source === "bookadoc") {
    return "CLINICAL";
  }

  // Financial events
  const financialPatterns = [
    "TRANSACTION",
    "INVOICE",
    "SUBSCRIPTION",
    "EXPENSE",
    "TAX",
    "REVENUE",
    "FINANCIAL",
  ];

  if (financialPatterns.some((p) => eventType.includes(p))) {
    return "FINANCIAL";
  }

  if (source === "taxrx" || source === "entitytaxpro" || source === "nexus") {
    return "FINANCIAL";
  }

  // Operational events
  const operationalPatterns = [
    "APPOINTMENT",
    "SCHEDULE",
    "WORKLOAD",
    "AUTOMATION",
    "CHART",
    "STAFF",
    "OPERATIONAL",
  ];

  if (operationalPatterns.some((p) => eventType.includes(p))) {
    return "OPERATIONAL";
  }

  // Business/Project events
  const businessPatterns = [
    "PROJECT",
    "DEADLINE",
    "RESOURCE",
    "BUSINESS",
    "TASK",
  ];

  if (businessPatterns.some((p) => eventType.includes(p))) {
    return "BUSINESS_PROJECT";
  }

  // Personal state events
  const personalPatterns = [
    "FATIGUE",
    "COGNITIVE",
    "EMOTIONAL",
    "FOCUS",
    "FRUSTRATION",
    "PERSONAL",
  ];

  if (personalPatterns.some((p) => eventType.includes(p))) {
    return "PERSONAL_STATE";
  }

  // System events
  const systemPatterns = [
    "AGENT",
    "RETRY",
    "LOAD",
    "MEMORY",
    "KILL_SWITCH",
    "POLICY",
    "SYSTEM",
  ];

  if (systemPatterns.some((p) => eventType.includes(p))) {
    return "SYSTEM";
  }

  return null;
}

async function classifyWithLLM(
  eventType: string,
  payload: Record<string, any>,
  source: string
): Promise<EventCategory> {
  // Simplified LLM classification
  // In production, this would call the LLM router
  // For now, default to OPERATIONAL for unknown events
  return "OPERATIONAL";
}

