import { supabaseServer } from "@/lib/supabase/server";
import type { PreferenceLearning, PatternType, UserFeedback } from "./types";

export async function recordPreferenceFeedback(
  userId: string,
  patternType: PatternType,
  patternValue: string,
  feedback: UserFeedback,
  context?: Record<string, any>
): Promise<void> {
  // Find or create preference learning record
  const { data: existing } = await supabaseServer
    .from("jarvis_preference_learning")
    .select("*")
    .eq("user_id", userId)
    .eq("pattern_type", patternType)
    .eq("pattern_value", patternValue)
    .single();

  if (existing) {
    // Update existing record
    const existingData = existing as any;
    const update: any = {
      last_used_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Increment appropriate counter
    if (feedback === "ACCEPTED") {
      update.acceptance_count = (existingData.acceptance_count || 0) + 1;
    } else if (feedback === "EDITED") {
      update.edit_count = (existingData.edit_count || 0) + 1;
    } else if (feedback === "REJECTED" || feedback === "OVERRIDDEN") {
      update.rewrite_count = (existingData.rewrite_count || 0) + 1;
      update.rejection_count = (existingData.rejection_count || 0) + 1;
    }

    // Recalculate confidence score
    update.confidence_score = calculateConfidenceScore(
      update.acceptance_count || existingData.acceptance_count || 0,
      update.edit_count || existingData.edit_count || 0,
      update.rewrite_count || existingData.rewrite_count || 0,
      update.rejection_count || existingData.rejection_count || 0
    );

    await (supabaseServer as any)
      .from("jarvis_preference_learning")
      .update(update)
      .eq("id", existingData.id);
  } else {
    // Create new record
    const newRecord: any = {
      user_id: userId,
      pattern_type: patternType,
      pattern_value: patternValue,
      context,
      acceptance_count: feedback === "ACCEPTED" ? 1 : 0,
      edit_count: feedback === "EDITED" ? 1 : 0,
      rewrite_count: feedback === "REJECTED" || feedback === "OVERRIDDEN" ? 1 : 0,
      rejection_count: feedback === "REJECTED" || feedback === "OVERRIDDEN" ? 1 : 0,
      confidence_score: calculateConfidenceScore(
        feedback === "ACCEPTED" ? 1 : 0,
        feedback === "EDITED" ? 1 : 0,
        feedback === "REJECTED" || feedback === "OVERRIDDEN" ? 1 : 0,
        feedback === "REJECTED" || feedback === "OVERRIDDEN" ? 1 : 0
      ),
      last_used_at: new Date().toISOString(),
    };

    await supabaseServer
      .from("jarvis_preference_learning")
      .insert(newRecord);
  }
}

function calculateConfidenceScore(
  acceptanceCount: number,
  editCount: number,
  rewriteCount: number,
  rejectionCount: number
): number {
  const total = acceptanceCount + editCount + rewriteCount + rejectionCount;
  if (total === 0) return 0.5; // Default neutral

  // Weight: acceptance = +1, edit = +0.5, rewrite = -0.5, rejection = -1
  const weightedScore =
    (acceptanceCount * 1 + editCount * 0.5 - rewriteCount * 0.5 - rejectionCount * 1) / total;

  // Normalize to 0-1 range
  return Math.max(0, Math.min(1, (weightedScore + 1) / 2));
}

export async function getPreferenceConfidence(
  userId: string,
  patternType: PatternType,
  patternValue: string
): Promise<number> {
  const { data } = await supabaseServer
    .from("jarvis_preference_learning")
    .select("confidence_score")
    .eq("user_id", userId)
    .eq("pattern_type", patternType)
    .eq("pattern_value", patternValue)
    .single();

  if (data) {
    return (data as any).confidence_score || 0.5;
  }

  return 0.5; // Default neutral confidence
}

export async function getTopPreferences(
  userId: string,
  patternType: PatternType,
  limit: number = 5
): Promise<PreferenceLearning[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_preference_learning")
    .select("*")
    .eq("user_id", userId)
    .eq("pattern_type", patternType)
    .order("confidence_score", { ascending: false })
    .limit(limit);

  if (error) {
    throw new Error(`Failed to get top preferences: ${error.message}`);
  }

  return (data || []) as PreferenceLearning[];
}

