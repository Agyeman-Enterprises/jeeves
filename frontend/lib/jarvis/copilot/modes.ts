import { supabaseServer } from "@/lib/supabase/server";
import type { AutonomyMode, ModeTransition, ModeTransitionTrigger, CoPilotState } from "./types";
import { getCurrentMentalState } from "../emotional/state";
import { getCognitiveBudget } from "../cerae/cognitive";
import { checkKillSwitch } from "../governance/killswitch";

export async function determineOptimalMode(
  userId: string,
  domain?: string
): Promise<AutonomyMode> {
  // Get current state
  const mentalState = await getCurrentMentalState(userId);
  const cognitiveBudget = await getCognitiveBudget(userId);
  const killSwitch = await checkKillSwitch(userId, domain as any, undefined);

  // If kill switch is active, force OBSERVE mode
  if (killSwitch.blocked) {
    return "OBSERVE";
  }

  // Get current co-pilot state
  const currentState = await getCoPilotState(userId);
  const currentMode = currentState?.current_mode || "OBSERVE";

  // Determine optimal mode based on multiple factors
  const cognitiveBandwidth = mentalState?.cognitive_bandwidth || 100;
  const fatigueLevel = mentalState?.fatigue_level || 0;
  const emotionalState = mentalState?.emotional_state || "neutral";
  const totalEnergy = cognitiveBudget?.total_energy_percentage || 50;

  // High cognitive load or fatigue → increase autonomy
  if (cognitiveBandwidth < 40 || fatigueLevel > 60 || totalEnergy < 40) {
    if (currentMode === "OBSERVE" || currentMode === "SUGGEST") {
      return "ASSIST"; // Step up to assist mode
    }
    if (currentMode === "ASSIST") {
      return "EXECUTE"; // Step up to execute mode
    }
    if (currentMode === "EXECUTE") {
      return "CO_PILOT"; // Full co-pilot mode
    }
  }

  // Low cognitive load and high energy → can handle more suggestions
  if (cognitiveBandwidth > 70 && fatigueLevel < 30 && totalEnergy > 70) {
    if (currentMode === "CO_PILOT" || currentMode === "EXECUTE") {
      return "ASSIST"; // Step down to assist mode
    }
  }

  // Emotional state considerations
  if (emotionalState === "stressed" || emotionalState === "overwhelmed") {
    // Increase autonomy to reduce burden
    if (currentMode === "OBSERVE" || currentMode === "SUGGEST") {
      return "ASSIST";
    }
    if (currentMode === "ASSIST") {
      return "EXECUTE";
    }
  }

  // Default: maintain current mode or step up gradually
  return currentMode;
}

export async function transitionMode(
  userId: string,
  toMode: AutonomyMode,
  reason: string,
  triggeredBy: ModeTransitionTrigger = "COGNITIVE_STATE",
  context?: Record<string, any>
): Promise<void> {
  // Get current state
  const currentState = await getCoPilotState(userId);
  const fromMode = currentState?.current_mode || "OBSERVE";

  // Log transition
  await logModeTransition(userId, fromMode, toMode, reason, triggeredBy, context);

  // Update co-pilot state
  await updateCoPilotState(userId, {
    current_mode: toMode,
    mode_context: context,
    last_mode_change: new Date().toISOString(),
  });
}

async function getCoPilotState(userId: string): Promise<CoPilotState | null> {
  const { data } = await supabaseServer
    .from("jarvis_copilot_state")
    .select("*")
    .eq("user_id", userId)
    .single();

  if (data) {
    return data as CoPilotState;
  }

  // Create initial state if doesn't exist
  const initialState: CoPilotState = {
    user_id: userId,
    current_mode: "OBSERVE",
    active_domains: [],
  };
  await createCoPilotState(userId, initialState);

  return initialState;
}

async function createCoPilotState(userId: string, state: CoPilotState): Promise<void> {
  await supabaseServer
    .from("jarvis_copilot_state")
    .insert({
      ...state,
    } as any);
}

async function updateCoPilotState(
  userId: string,
  updates: Partial<CoPilotState>
): Promise<void> {
  await (supabaseServer as any)
    .from("jarvis_copilot_state")
    .update({
      ...updates,
      updated_at: new Date().toISOString(),
    } as any)
    .eq("user_id", userId);
}

async function logModeTransition(
  userId: string,
  fromMode: AutonomyMode | undefined,
  toMode: AutonomyMode,
  reason: string,
  triggeredBy: ModeTransitionTrigger,
  context?: Record<string, any>
): Promise<void> {
  await supabaseServer
    .from("jarvis_mode_transitions")
    .insert({
      user_id: userId,
      from_mode: fromMode,
      to_mode: toMode,
      transition_reason: reason,
      triggered_by: triggeredBy,
      context,
    } as any);
}

export async function getCurrentMode(userId: string): Promise<AutonomyMode> {
  const state = await getCoPilotState(userId);
  return state?.current_mode || "OBSERVE";
}

