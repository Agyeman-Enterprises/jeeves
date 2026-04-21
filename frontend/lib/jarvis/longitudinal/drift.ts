import { supabaseServer } from "@/lib/supabase/server";
import type { IdentityDrift, IdentityDimension, DriftDirection } from "./types";
import { getLongitudinalIdentity } from "./identity";

export async function detectIdentityDrift(
  userId: string,
  dimension: IdentityDimension
): Promise<IdentityDrift | null> {
  const identities = await getLongitudinalIdentity(userId, dimension);
  const identity = identities[0];

  if (!identity || !identity.baseline_value || !identity.current_value) {
    return null;
  }

  // Calculate drift magnitude
  const driftMagnitude = Math.abs(identity.current_value - identity.baseline_value);
  const driftThreshold = (identity.baseline_value || 0) * 0.15; // 15% change threshold

  if (driftMagnitude < driftThreshold) {
    return null; // No significant drift
  }

  // Determine drift direction
  let driftDirection: DriftDirection = "SHIFTING";
  if (identity.current_value > identity.baseline_value) {
    driftDirection = "INCREASING";
  } else if (identity.current_value < identity.baseline_value) {
    driftDirection = "DECREASING";
  }

  // Get evidence
  const evidence = {
    baseline_value: identity.baseline_value,
    current_value: identity.current_value,
    trend_7days: identity.trend_7days,
    trend_30days: identity.trend_30days,
    sample_count: identity.sample_count,
  };

  // Create drift record
  const { data, error } = await supabaseServer
    .from("jarvis_identity_drift")
    .insert({
      user_id: userId,
      dimension,
      previous_baseline: identity.baseline_value,
      new_baseline: identity.current_value,
      drift_magnitude: driftMagnitude,
      drift_direction: driftDirection,
      evidence,
    } as any)
    .select()
    .single();

  if (error || !data) {
    throw new Error(`Failed to detect identity drift: ${error?.message}`);
  }

  return data as IdentityDrift;
}

export async function getRecentDrifts(
  userId: string,
  limit: number = 10
): Promise<IdentityDrift[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_identity_drift")
    .select("*")
    .eq("user_id", userId)
    .order("detected_at", { ascending: false })
    .limit(limit);

  if (error) {
    throw new Error(`Failed to get identity drifts: ${error.message}`);
  }

  return (data || []) as IdentityDrift[];
}

export async function generateDriftAdaptation(
  userId: string,
  drift: IdentityDrift
): Promise<string> {
  // Generate adaptation message based on drift
  let message = "";

  switch (drift.dimension) {
    case "autonomy_preference":
      if (drift.drift_direction === "INCREASING") {
        message = `I've noticed you're approving more autonomous scheduling — would you like me to increase your autonomy in operations?`;
      }
      break;

    case "fatigue_pattern":
      if (drift.drift_direction === "INCREASING") {
        message = `You've been more fatigued in the past two weeks. Should I move more tasks into low-bandwidth flow?`;
      }
      break;

    case "focus":
      if (drift.drift_direction === "SHIFTING") {
        message = `Your focus periods have shifted later in the day. Want me to reschedule deep work blocks?`;
      }
      break;

    default:
      message = `I've detected a change in your ${drift.dimension} pattern. Would you like me to adjust my approach?`;
  }

  return message;
}

