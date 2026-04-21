import { supabaseServer } from "@/lib/supabase/server";
import type { BehaviorVector, PreferenceRule, ContextType } from "./types";

export interface BehaviorInterpretation {
  shouldNotify: boolean;
  shouldAutomate: boolean;
  priority: number;
  tone: string;
  escalationRequired: boolean;
  delegationRecommended: boolean;
}

export async function interpretBehavior(
  userId: string,
  context: {
    type: "CLINICAL" | "FINANCIAL" | "OPERATIONAL" | "COMMUNICATION" | "PERSONAL";
    severity?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    data?: Record<string, any>;
  }
): Promise<BehaviorInterpretation> {
  // Get behavior vectors
  const { data: vectors } = await supabaseServer
    .from("jarvis_behavior_vectors")
    .select("*")
    .eq("user_id", userId)
    .single();

  // Get preference rules
  const { data: rules } = await supabaseServer
    .from("jarvis_preference_rules")
    .select("*")
    .eq("user_id", userId)
    .order("confidence", { ascending: false });

  const behaviorVectors = vectors ? (vectors as any) : null;
  const preferenceRules = rules || [];

  // Start with defaults
  let interpretation: BehaviorInterpretation = {
    shouldNotify: true,
    shouldAutomate: false,
    priority: 50,
    tone: "professional",
    escalationRequired: false,
    delegationRecommended: false,
  };

  // Apply preference rules first (explicit rules override)
  for (const rule of preferenceRules) {
    const r = rule as any;
    if (matchesCondition(r.trigger_condition, context)) {
      if (r.rule_type === "NOTIFICATION") {
        interpretation.shouldNotify = r.action === "NOTIFY";
      } else if (r.rule_type === "AUTOMATION") {
        interpretation.shouldAutomate = r.action === "AUTOMATE";
      } else if (r.rule_type === "PRIORITY") {
        interpretation.priority = parseInt(r.action) || interpretation.priority;
      } else if (r.rule_type === "ESCALATION") {
        interpretation.escalationRequired = r.action === "ESCALATE";
      } else if (r.rule_type === "DELEGATION") {
        interpretation.delegationRecommended = r.action === "DELEGATE";
      }
    }
  }

  // Apply learned behavior patterns
  if (behaviorVectors) {
    if (context.type === "CLINICAL" && behaviorVectors.clinical_vector) {
      const clinical = behaviorVectors.clinical_vector;
      // Check if similar context was typically approved/declined
      const contextKey = (context.data?.context || "").toLowerCase().replace(/\s+/g, "_");
      if (clinical.patterns?.[contextKey]) {
        const pattern = clinical.patterns[contextKey];
        if (pattern.approve > pattern.decline * 2) {
          interpretation.shouldAutomate = true;
          interpretation.shouldNotify = false;
        }
      }
    }

    if (context.type === "OPERATIONAL" && behaviorVectors.operational_vector) {
      const operational = behaviorVectors.operational_vector;
      // Check ignore patterns
      if (operational.priorities?.ignored_count > operational.priorities?.escalated_count * 3) {
        interpretation.shouldNotify = false;
        interpretation.priority = Math.max(0, interpretation.priority - 20);
      }
    }

    if (context.type === "COMMUNICATION" && behaviorVectors.communication_vector) {
      const comm = behaviorVectors.communication_vector;
      // Adjust tone based on learned preferences
      if (comm.preferred_length < 0) {
        interpretation.tone = "concise";
      } else if (comm.avg_sentence_length && comm.avg_sentence_length < 50) {
        interpretation.tone = "brief";
      }
    }
  }

  // Severity-based adjustments
  if (context.severity === "CRITICAL") {
    interpretation.shouldNotify = true;
    interpretation.escalationRequired = true;
    interpretation.priority = 100;
  } else if (context.severity === "LOW") {
    interpretation.shouldNotify = false;
    interpretation.priority = Math.max(0, interpretation.priority - 30);
  }

  return interpretation;
}

function matchesCondition(
  condition: Record<string, any>,
  context: Record<string, any>
): boolean {
  // Simple condition matching
  for (const [key, value] of Object.entries(condition)) {
    if (context[key] !== value) {
      return false;
    }
  }
  return true;
}

export async function predictDecision(
  userId: string,
  context: {
    type: ContextType;
    data: Record<string, any>;
  }
): Promise<{
  predictedAction: "APPROVE" | "DECLINE" | "ESCALATE" | "REVISE";
  confidence: number;
}> {
  const { data: vectors } = await supabaseServer
    .from("jarvis_behavior_vectors")
    .select("*")
    .eq("user_id", userId)
    .single();

  if (!vectors) {
    return { predictedAction: "ESCALATE", confidence: 0.5 };
  }

  const v = vectors as any;

  // Use learned patterns to predict
  if (context.type === "CLINICAL" && v.clinical_vector?.patterns) {
    const contextKey = (context.data?.context || "").toLowerCase().replace(/\s+/g, "_");
    const pattern = v.clinical_vector.patterns[contextKey];
    
    if (pattern) {
      const total = pattern.approve + pattern.decline + pattern.escalate;
      if (total > 0) {
        if (pattern.approve / total > 0.7) {
          return { predictedAction: "APPROVE", confidence: pattern.approve / total };
        } else if (pattern.decline / total > 0.7) {
          return { predictedAction: "DECLINE", confidence: pattern.decline / total };
        } else if (pattern.escalate / total > 0.5) {
          return { predictedAction: "ESCALATE", confidence: pattern.escalate / total };
        }
      }
    }
  }

  // Default to escalate if uncertain
  return { predictedAction: "ESCALATE", confidence: 0.5 };
}

