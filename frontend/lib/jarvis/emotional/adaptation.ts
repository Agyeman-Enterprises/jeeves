import { supabaseServer } from "@/lib/supabase/server";
import type { MentalState, StateAdaptation, AdaptationType, EmotionalState } from "./types";
import { setDomainAutonomyMode } from "../autonomy/modes";
import { logAutonomyChange } from "../autonomy/history";
import type { AutonomyMode } from "../autonomy/types";

export async function adaptToMentalState(
  userId: string,
  state: MentalState
): Promise<StateAdaptation[]> {
  const adaptations: StateAdaptation[] = [];

  // Determine adaptation strategy based on state
  if (state.energy_level > 70 && state.stress_level < 40 && state.fatigue_level < 30) {
    // High energy - increase autonomy, be more proactive
    adaptations.push(...(await adaptForHighEnergy(userId, state)));
  } else if (state.fatigue_level > 60 || state.stress_level > 60) {
    // Fatigue or stress - reduce load, be supportive
    adaptations.push(...(await adaptForFatigueOrStress(userId, state)));
  } else if (state.cognitive_bandwidth < 40 || state.emotional_state === "overwhelmed") {
    // Overwhelmed - minimize cognitive load
    adaptations.push(...(await adaptForOverwhelm(userId, state)));
  } else if (state.emotional_state === "frustrated") {
    // Frustrated - slow down, be precise
    adaptations.push(...(await adaptForFrustration(userId, state)));
  } else if (state.focus_level > 70) {
    // High focus - minimize interruptions
    adaptations.push(...(await adaptForHighFocus(userId, state)));
  } else {
    // Normal mode - balanced approach
    adaptations.push(...(await adaptForNormalMode(userId, state)));
  }

  // Store adaptations
  for (const adaptation of adaptations) {
    await storeAdaptation(userId, state.id || "", adaptation);
  }

  return adaptations;
}

async function adaptForHighEnergy(
  userId: string,
  state: MentalState
): Promise<StateAdaptation[]> {
  const adaptations: StateAdaptation[] = [];

  // Increase autonomy for operations domain
  try {
    await setDomainAutonomyMode(userId, "operations", "AUTONOMOUS");
    adaptations.push({
      user_id: userId,
      adaptation_type: "autonomy",
      previous_value: "DELEGATED",
      new_value: "AUTONOMOUS",
      reason: "High energy detected - increasing autonomy for efficiency",
    });
  } catch (error) {
    // Domain may not allow autonomous mode
  }

  adaptations.push({
    user_id: userId,
    adaptation_type: "verbosity",
    previous_value: "medium",
    new_value: "high",
    reason: "High energy - providing more detailed options and strategic planning",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "tone",
    previous_value: "balanced",
    new_value: "confident, fast-paced, visionary",
    reason: "High energy - matching your energetic state",
  });

  return adaptations;
}

async function adaptForFatigueOrStress(
  userId: string,
  state: MentalState
): Promise<StateAdaptation[]> {
  const adaptations: StateAdaptation[] = [];

  // Reduce autonomy
  try {
    await setDomainAutonomyMode(userId, "operations", "COLLABORATIVE");
    adaptations.push({
      user_id: userId,
      adaptation_type: "autonomy",
      previous_value: "DELEGATED",
      new_value: "COLLABORATIVE",
      reason: "Fatigue/stress detected - reducing autonomy to lighten load",
    });
  } catch (error) {
    // May already be collaborative
  }

  adaptations.push({
    user_id: userId,
    adaptation_type: "verbosity",
    previous_value: "medium",
    new_value: "low",
    reason: "Fatigue/stress - keeping communications concise",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "notifications",
    previous_value: "normal",
    new_value: "reduced",
    reason: "Fatigue/stress - reducing notification frequency",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "tone",
    previous_value: "balanced",
    new_value: "gentle, supportive, concise",
    reason: "Fatigue/stress - providing supportive, gentle tone",
  });

  return adaptations;
}

async function adaptForOverwhelm(
  userId: string,
  state: MentalState
): Promise<StateAdaptation[]> {
  const adaptations: StateAdaptation[] = [];

  // Reduce to assistive mode
  try {
    await setDomainAutonomyMode(userId, "operations", "ASSISTIVE");
    adaptations.push({
      user_id: userId,
      adaptation_type: "autonomy",
      previous_value: "COLLABORATIVE",
      new_value: "ASSISTIVE",
      reason: "Overwhelm detected - switching to assistive mode",
    });
  } catch (error) {
    // May not be allowed
  }

  adaptations.push({
    user_id: userId,
    adaptation_type: "verbosity",
    previous_value: "medium",
    new_value: "minimal",
    reason: "Overwhelm - using simple bullet points only",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "notifications",
    previous_value: "normal",
    new_value: "paused",
    reason: "Overwhelm - pausing non-critical notifications",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "tone",
    previous_value: "balanced",
    new_value: "calm, grounding, executive clarity",
    reason: "Overwhelm - providing calm, grounding tone",
  });

  // Check if we should enter support mode
  if (state.cognitive_bandwidth < 30) {
    await activateSupportMode(userId, "overwhelm", state);
  }

  return adaptations;
}

async function adaptForFrustration(
  userId: string,
  state: MentalState
): Promise<StateAdaptation[]> {
  const adaptations: StateAdaptation[] = [];

  adaptations.push({
    user_id: userId,
    adaptation_type: "verbosity",
    previous_value: "medium",
    new_value: "minimal",
    reason: "Frustration detected - keeping instructions extremely precise",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "tone",
    previous_value: "balanced",
    new_value: "precise, clear, no fluff",
    reason: "Frustration - providing extremely precise, clear communication",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "timing",
    previous_value: "normal",
    new_value: "slowed",
    reason: "Frustration - slowing down to ensure clarity",
  });

  return adaptations;
}

async function adaptForHighFocus(
  userId: string,
  state: MentalState
): Promise<StateAdaptation[]> {
  const adaptations: StateAdaptation[] = [];

  adaptations.push({
    user_id: userId,
    adaptation_type: "notifications",
    previous_value: "normal",
    new_value: "minimal",
    reason: "High focus detected - minimizing interruptions",
  });

  adaptations.push({
    user_id: userId,
    adaptation_type: "tone",
    previous_value: "balanced",
    new_value: "high-precision, minimal interruption",
    reason: "High focus - using high-precision, minimal interruption tone",
  });

  return adaptations;
}

async function adaptForNormalMode(
  userId: string,
  state: MentalState
): Promise<StateAdaptation[]> {
  const adaptations: StateAdaptation[] = [];

  adaptations.push({
    user_id: userId,
    adaptation_type: "tone",
    previous_value: "any",
    new_value: "balanced, collaborative, structured",
    reason: "Normal mode - using balanced, collaborative tone",
  });

  return adaptations;
}

async function storeAdaptation(
  userId: string,
  mentalStateId: string,
  adaptation: Partial<StateAdaptation>
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_state_adaptations")
    .insert({
      user_id: userId,
      mental_state_id: mentalStateId,
      adaptation_type: adaptation.adaptation_type,
      previous_value: adaptation.previous_value,
      new_value: adaptation.new_value,
      reason: adaptation.reason,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to store adaptation: ${error?.message}`);
  }

  return (data as any).id;
}

async function activateSupportMode(
  userId: string,
  trigger: "burnout" | "overwhelm" | "cognitive_exhaustion" | "user_request",
  state: MentalState
): Promise<string> {
  // Check if support mode is already active
  const { data: existing } = await supabaseServer
    .from("jarvis_support_mode")
    .select("*")
    .eq("user_id", userId)
    .eq("status", "ACTIVE")
    .single();

  if (existing) {
    return (existing as any).id;
  }

  // Create support mode activation
  const adaptations = {
    reduce_autonomy: true,
    lower_notifications: true,
    pause_non_critical_agents: true,
    route_tasks_to_later: true,
    adjust_schedule: true,
  };

  const { data, error } = await supabaseServer
    .from("jarvis_support_mode")
    .insert({
      user_id: userId,
      triggered_by: trigger,
      state_snapshot: state.state_vector,
      adaptations_applied: adaptations,
      status: "ACTIVE",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to activate support mode: ${error?.message}`);
  }

  return (data as any).id;
}

export async function deactivateSupportMode(userId: string): Promise<void> {
  await (supabaseServer as any)
    .from("jarvis_support_mode")
    .update({
      status: "INACTIVE",
      deactivated_at: new Date().toISOString(),
    } as any)
    .eq("user_id", userId)
    .eq("status", "ACTIVE");
}

