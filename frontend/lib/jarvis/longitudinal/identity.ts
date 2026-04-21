import { supabaseServer } from "@/lib/supabase/server";
import type { LongitudinalIdentity, IdentityDimension } from "./types";

export async function updateLongitudinalIdentity(
  userId: string,
  dimension: IdentityDimension,
  currentValue: number
): Promise<LongitudinalIdentity> {
  // Get existing identity
  const { data: existing } = await supabaseServer
    .from("jarvis_longitudinal_identity")
    .select("*")
    .eq("user_id", userId)
    .eq("dimension", dimension)
    .single();

  if (existing) {
    // Update existing
    const identity = existing as any;
    const sampleCount = identity.sample_count || 1;
    const newSampleCount = sampleCount + 1;

    // Calculate new baseline (weighted average)
    const baselineValue = identity.baseline_value || currentValue;
    const newBaseline = (baselineValue * sampleCount + currentValue) / newSampleCount;

    // Calculate trends
    const trend7Days = await calculateTrend(userId, dimension, 7);
    const trend30Days = await calculateTrend(userId, dimension, 30);
    const trend90Days = await calculateTrend(userId, dimension, 90);

    // Calculate variance
    const variance = await calculateVariance(userId, dimension, newBaseline);

    // Determine pattern type
    const patternType = determinePatternType(trend7Days, trend30Days, variance);

    // Calculate confidence (more samples = higher confidence)
    const confidenceScore = Math.min(1.0, newSampleCount / 50);

    const updateData: Record<string, any> = {
      baseline_value: newBaseline,
      current_value: currentValue,
      trend_7days: trend7Days,
      trend_30days: trend30Days,
      trend_90days: trend90Days,
      variance,
      pattern_type: patternType,
      confidence_score: confidenceScore,
      sample_count: newSampleCount,
      last_observed_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await (supabaseServer as any)
      .from("jarvis_longitudinal_identity")
      .update(updateData)
      .eq("id", identity.id);

    return { ...identity, ...updateData } as LongitudinalIdentity;
  } else {
    // Create new identity
    const { data: newIdentity } = await supabaseServer
      .from("jarvis_longitudinal_identity")
      .insert({
        user_id: userId,
        dimension,
        baseline_value: currentValue,
        current_value: currentValue,
        trend_7days: 0,
        trend_30days: 0,
        trend_90days: 0,
        variance: 0,
        pattern_type: "stable",
        confidence_score: 0.1,
        sample_count: 1,
        first_observed_at: new Date().toISOString(),
        last_observed_at: new Date().toISOString(),
      } as any)
      .select()
      .single();

    return newIdentity as LongitudinalIdentity;
  }
}

async function calculateTrend(
  userId: string,
  dimension: IdentityDimension,
  days: number
): Promise<number> {
  // Get historical mental state data
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  const { data: recentStates } = await supabaseServer
    .from("jarvis_mental_state")
    .select("*")
    .eq("user_id", userId)
    .gte("detected_at", cutoffDate.toISOString())
    .order("detected_at", { ascending: true });

  if (!recentStates || recentStates.length < 2) {
    return 0;
  }

  // Map dimension to mental state field
  const fieldMap: Record<IdentityDimension, string> = {
    energy: "energy_level",
    focus: "focus_level",
    stress: "stress_level",
    decision_load: "decision_load",
    autonomy_preference: "energy_level", // Approximate
    work_intensity: "energy_level",
    command_frequency: "energy_level",
    decision_speed: "focus_level",
    correction_rate: "stress_level",
    frustration_threshold: "stress_level",
    fatigue_pattern: "fatigue_level",
    communication_tone: "energy_level",
    escalation_sensitivity: "stress_level",
    burnout_indicators: "fatigue_level",
    productivity_rhythm: "focus_level",
    clinical_risk_tolerance: "stress_level",
    financial_risk_tolerance: "stress_level",
    operational_autonomy: "energy_level",
  };

  const field = fieldMap[dimension] || "energy_level";
  const values = (recentStates as any[]).map((s) => s[field] || 0);

  // Calculate linear trend
  const n = values.length;
  const sumX = (n * (n - 1)) / 2;
  const sumY = values.reduce((a, b) => a + b, 0);
  const sumXY = values.reduce((sum, val, idx) => sum + val * idx, 0);
  const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);

  return slope;
}

async function calculateVariance(
  userId: string,
  dimension: IdentityDimension,
  baseline: number
): Promise<number> {
  // Get recent values
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 30);

  const { data: recentStates } = await supabaseServer
    .from("jarvis_mental_state")
    .select("*")
    .eq("user_id", userId)
    .gte("detected_at", cutoffDate.toISOString());

  if (!recentStates || recentStates.length === 0) {
    return 0;
  }

  const fieldMap: Record<IdentityDimension, string> = {
    energy: "energy_level",
    focus: "focus_level",
    stress: "stress_level",
    decision_load: "decision_load",
    autonomy_preference: "energy_level",
    work_intensity: "energy_level",
    command_frequency: "energy_level",
    decision_speed: "focus_level",
    correction_rate: "stress_level",
    frustration_threshold: "stress_level",
    fatigue_pattern: "fatigue_level",
    communication_tone: "energy_level",
    escalation_sensitivity: "stress_level",
    burnout_indicators: "fatigue_level",
    productivity_rhythm: "focus_level",
    clinical_risk_tolerance: "stress_level",
    financial_risk_tolerance: "stress_level",
    operational_autonomy: "energy_level",
  };

  const field = fieldMap[dimension] || "energy_level";
  const values = (recentStates as any[]).map((s) => s[field] || 0);

  // Calculate variance
  const squaredDiffs = values.map((val) => Math.pow(val - baseline, 2));
  const variance = squaredDiffs.reduce((a, b) => a + b, 0) / values.length;

  return variance;
}

function determinePatternType(
  trend7Days: number,
  trend30Days: number,
  variance: number
): "stable" | "increasing" | "decreasing" | "cyclical" | "volatile" {
  if (variance > 100) {
    return "volatile";
  }
  if (Math.abs(trend7Days) < 1 && Math.abs(trend30Days) < 1) {
    return "stable";
  }
  if (trend7Days > 0 && trend30Days > 0) {
    return "increasing";
  }
  if (trend7Days < 0 && trend30Days < 0) {
    return "decreasing";
  }
  if (Math.abs(trend7Days) > Math.abs(trend30Days)) {
    return "cyclical";
  }
  return "stable";
}

export async function getLongitudinalIdentity(
  userId: string,
  dimension?: IdentityDimension
): Promise<LongitudinalIdentity[]> {
  let query = supabaseServer
    .from("jarvis_longitudinal_identity")
    .select("*")
    .eq("user_id", userId);

  if (dimension) {
    query = query.eq("dimension", dimension);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get longitudinal identity: ${error.message}`);
  }

  return (data || []) as LongitudinalIdentity[];
}

