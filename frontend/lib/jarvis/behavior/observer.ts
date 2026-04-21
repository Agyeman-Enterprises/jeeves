import { supabaseServer } from "@/lib/supabase/server";
import type { DecisionLog, ModelType } from "./types";

export async function logDecision(log: DecisionLog): Promise<void> {
  // Store decision log
  await supabaseServer
    .from("jarvis_decision_logs")
    .insert({
      user_id: log.user_id,
      decision_type: log.decision_type,
      context_type: log.context_type,
      context_id: log.context_id,
      original_input: log.original_input,
      user_action: log.user_action,
      user_feedback: log.user_feedback,
      model_affected: log.model_affected || [],
    } as any);

  // Update behavior vectors based on decision
  if (log.model_affected && log.model_affected.length > 0) {
    await updateBehaviorVectors(log.user_id, log);
  }
}

async function updateBehaviorVectors(userId: string, log: DecisionLog): Promise<void> {
  // Get current vectors
  const { data: vectors } = await supabaseServer
    .from("jarvis_behavior_vectors")
    .select("*")
    .eq("user_id", userId)
    .single();

  const currentVectors = vectors ? (vectors as any) : {
    user_id: userId,
    communication_vector: {},
    clinical_vector: {},
    operational_vector: {},
    financial_vector: {},
    personal_vector: {},
  };

  // Update relevant vectors based on decision
  for (const model of log.model_affected || []) {
    switch (model) {
      case "CSM":
        // Update communication style based on revisions
        if (log.decision_type === "REVISE" && log.original_input?.text && log.user_action?.text) {
          currentVectors.communication_vector = updateCommunicationVector(
            currentVectors.communication_vector || {},
            log.original_input.text,
            log.user_action.text
          );
        }
        break;

      case "CDM":
        // Update clinical decision patterns
        if (log.context_type === "CLINICAL") {
          currentVectors.clinical_vector = updateClinicalVector(
            currentVectors.clinical_vector || {},
            log
          );
        }
        break;

      case "OPM":
        // Update operational priorities
        if (log.context_type === "OPERATIONAL") {
          currentVectors.operational_vector = updateOperationalVector(
            currentVectors.operational_vector || {},
            log
          );
        }
        break;

      case "FBM":
        // Update financial behavior
        if (log.context_type === "FINANCIAL") {
          currentVectors.financial_vector = updateFinancialVector(
            currentVectors.financial_vector || {},
            log
          );
        }
        break;

      case "PPM":
        // Update personal preferences
        currentVectors.personal_vector = updatePersonalVector(
          currentVectors.personal_vector || {},
          log
        );
        break;
    }
  }

  // Save updated vectors
  await supabaseServer
    .from("jarvis_behavior_vectors")
    .upsert({
      user_id: userId,
      communication_vector: currentVectors.communication_vector,
      clinical_vector: currentVectors.clinical_vector,
      operational_vector: currentVectors.operational_vector,
      financial_vector: currentVectors.financial_vector,
      personal_vector: currentVectors.personal_vector,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "user_id",
    });
}

function updateCommunicationVector(
  current: Record<string, any>,
  original: string,
  revised: string
): Record<string, any> {
  // Simple pattern: track differences in length, tone, structure
  const lengthDiff = revised.length - original.length;
  const avgSentenceLength = revised.split(/[.!?]+/).filter(Boolean).reduce((sum, s) => sum + s.length, 0) / revised.split(/[.!?]+/).filter(Boolean).length;

  return {
    ...current,
    preferred_length: current.preferred_length ? (current.preferred_length + lengthDiff) / 2 : lengthDiff,
    avg_sentence_length: current.avg_sentence_length ? (current.avg_sentence_length + avgSentenceLength) / 2 : avgSentenceLength,
    revision_count: (current.revision_count || 0) + 1,
  };
}

function updateClinicalVector(
  current: Record<string, any>,
  log: DecisionLog
): Record<string, any> {
  const decision = log.decision_type;
  const context = log.original_input?.context || "";

  // Track approval/decline patterns by context
  const patterns = current.patterns || {};
  const key = context.toLowerCase().replace(/\s+/g, "_");

  if (!patterns[key]) {
    patterns[key] = { approve: 0, decline: 0, escalate: 0 };
  }

  if (decision === "APPROVE") patterns[key].approve++;
  if (decision === "DECLINE") patterns[key].decline++;
  if (decision === "ESCALATE") patterns[key].escalate++;

  return {
    ...current,
    patterns,
    total_decisions: (current.total_decisions || 0) + 1,
  };
}

function updateOperationalVector(
  current: Record<string, any>,
  log: DecisionLog
): Record<string, any> {
  const decision = log.decision_type;

  // Track what gets ignored vs escalated
  const priorities = current.priorities || {};
  
  if (decision === "IGNORE") {
    priorities.ignored_count = (priorities.ignored_count || 0) + 1;
  } else if (decision === "ESCALATE") {
    priorities.escalated_count = (priorities.escalated_count || 0) + 1;
  }

  return {
    ...current,
    priorities,
    total_actions: (current.total_actions || 0) + 1,
  };
}

function updateFinancialVector(
  current: Record<string, any>,
  log: DecisionLog
): Record<string, any> {
  const decision = log.decision_type;
  const category = log.original_input?.category || "unknown";

  // Track categorization patterns
  const categories = current.categories || {};
  if (!categories[category]) {
    categories[category] = { approve: 0, revise: 0 };
  }

  if (decision === "APPROVE") categories[category].approve++;
  if (decision === "REVISE") categories[category].revise++;

  return {
    ...current,
    categories,
    total_decisions: (current.total_decisions || 0) + 1,
  };
}

function updatePersonalVector(
  current: Record<string, any>,
  log: DecisionLog
): Record<string, any> {
  // Track general preferences
  const preferences = current.preferences || {};

  if (log.decision_type === "IGNORE") {
    preferences.ignore_patterns = preferences.ignore_patterns || [];
    preferences.ignore_patterns.push(log.context_type);
  }

  return {
    ...current,
    preferences,
    total_interactions: (current.total_interactions || 0) + 1,
  };
}

