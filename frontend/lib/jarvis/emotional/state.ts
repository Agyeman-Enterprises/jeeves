import { supabaseServer } from "@/lib/supabase/server";
import type { MentalState, BehavioralSignal, EmotionalState, SignalType } from "./types";

export async function detectMentalState(userId: string): Promise<MentalState> {
  // Get recent behavioral signals
  const { data: recentSignals } = await supabaseServer
    .from("jarvis_behavioral_signals")
    .select("*")
    .eq("user_id", userId)
    .order("detected_at", { ascending: false })
    .limit(50);

  // Get energy patterns for current time
  const now = new Date();
  const dayOfWeek = now.getDay();
  const hourOfDay = now.getHours();

  const { data: energyPattern } = await supabaseServer
    .from("jarvis_energy_patterns")
    .select("*")
    .eq("user_id", userId)
    .eq("day_of_week", dayOfWeek)
    .eq("hour_of_day", hourOfDay)
    .single();

  // Analyze signals to determine state
  const state = analyzeSignals(recentSignals || [], energyPattern as any);

  // Store mental state snapshot
  const { data: stateData } = await supabaseServer
    .from("jarvis_mental_state")
    .insert({
      user_id: userId,
      stress_level: state.stress_level,
      fatigue_level: state.fatigue_level,
      focus_level: state.focus_level,
      decision_load: state.decision_load,
      emotional_state: state.emotional_state,
      cognitive_bandwidth: state.cognitive_bandwidth,
      energy_level: state.energy_level,
      state_vector: state,
    } as any)
    .select()
    .single();

  return stateData as MentalState;
}

function analyzeSignals(signals: any[], energyPattern: any): MentalState {
  // Initialize state with defaults
  let stressLevel = 0;
  let fatigueLevel = 0;
  let focusLevel = 50;
  let decisionLoad = 0;
  let emotionalState: EmotionalState = "neutral";
  let cognitiveBandwidth = 100;
  let energyLevel = 50;

  // Apply energy pattern baseline if available
  if (energyPattern) {
    energyLevel = energyPattern.avg_energy_level || 50;
    focusLevel = energyPattern.avg_focus_level || 50;
    stressLevel = energyPattern.avg_stress_level || 0;
  }

  // Analyze typing patterns
  const typingSignals = signals.filter((s) => s.signal_type === "typing_pattern");
  for (const signal of typingSignals) {
    const data = signal.signal_data;
    if (data.slow_typing) {
      fatigueLevel += 10;
      energyLevel -= 5;
    }
    if (data.short_replies) {
      stressLevel += 5;
      cognitiveBandwidth -= 10;
    }
    if (data.long_pauses) {
      fatigueLevel += 5;
      focusLevel -= 5;
    }
  }

  // Analyze timing patterns
  const timingSignals = signals.filter((s) => s.signal_type === "timing");
  for (const signal of timingSignals) {
    const data = signal.signal_data;
    if (data.late_night_work) {
      fatigueLevel += 15;
      energyLevel -= 10;
    }
    if (data.rapid_fire_commands) {
      stressLevel += 10;
      decisionLoad += 15;
    }
    if (data.long_silence) {
      stressLevel += 5;
      cognitiveBandwidth -= 15;
    }
  }

  // Analyze behavioral changes
  const behavioralSignals = signals.filter((s) => s.signal_type === "behavioral_change");
  for (const signal of behavioralSignals) {
    const data = signal.signal_data;
    if (data.rejecting_more) {
      stressLevel += 10;
      cognitiveBandwidth -= 10;
    }
    if (data.asking_simpler_explanations) {
      fatigueLevel += 10;
      cognitiveBandwidth -= 15;
    }
    if (data.asking_to_slow_down) {
      stressLevel += 15;
      cognitiveBandwidth -= 20;
    }
  }

  // Analyze emotional cues
  const emotionalSignals = signals.filter((s) => s.signal_type === "emotional_cue");
  for (const signal of emotionalSignals) {
    const data = signal.signal_data;
    if (data.frustration_cues) {
      stressLevel += 15;
      emotionalState = "frustrated";
    }
    if (data.overwhelm_cues) {
      stressLevel += 20;
      cognitiveBandwidth -= 25;
      emotionalState = "overwhelmed";
    }
    if (data.fatigue_cues) {
      fatigueLevel += 20;
      energyLevel -= 15;
      emotionalState = "tired";
    }
    if (data.energy_cues) {
      energyLevel += 15;
      emotionalState = "energized";
    }
  }

  // Analyze calendar context
  const calendarSignals = signals.filter((s) => s.signal_type === "calendar_context");
  for (const signal of calendarSignals) {
    const data = signal.signal_data;
    if (data.too_many_meetings) {
      decisionLoad += 20;
      cognitiveBandwidth -= 15;
    }
    if (data.back_to_back_schedule) {
      stressLevel += 10;
      fatigueLevel += 10;
    }
  }

  // Analyze system stress
  const systemSignals = signals.filter((s) => s.signal_type === "system_stress");
  for (const signal of systemSignals) {
    const data = signal.signal_data;
    if (data.too_many_notifications) {
      stressLevel += 10;
      cognitiveBandwidth -= 10;
    }
    if (data.too_many_agents) {
      stressLevel += 5;
    }
  }

  // Normalize values (0-100)
  stressLevel = Math.min(100, Math.max(0, stressLevel));
  fatigueLevel = Math.min(100, Math.max(0, fatigueLevel));
  focusLevel = Math.min(100, Math.max(0, focusLevel));
  decisionLoad = Math.min(100, Math.max(0, decisionLoad));
  cognitiveBandwidth = Math.min(100, Math.max(0, cognitiveBandwidth));
  energyLevel = Math.min(100, Math.max(0, energyLevel));

  // Determine emotional state if not already set
  if (emotionalState === "neutral") {
    if (stressLevel > 70 || cognitiveBandwidth < 30) {
      emotionalState = "overwhelmed";
    } else if (stressLevel > 50) {
      emotionalState = "stressed";
    } else if (fatigueLevel > 70) {
      emotionalState = "tired";
    } else if (focusLevel > 70 && energyLevel > 60) {
      emotionalState = "focused";
    } else if (energyLevel > 70) {
      emotionalState = "energized";
    }
  }

  return {
    user_id: "",
    stress_level: stressLevel,
    fatigue_level: fatigueLevel,
    focus_level: focusLevel,
    decision_load: decisionLoad,
    emotional_state: emotionalState,
    cognitive_bandwidth: cognitiveBandwidth,
    energy_level: energyLevel,
    state_vector: {
      stress_level: stressLevel,
      fatigue_level: fatigueLevel,
      focus_level: focusLevel,
      decision_load: decisionLoad,
      emotional_state: emotionalState,
      cognitive_bandwidth: cognitiveBandwidth,
      energy_level: energyLevel,
    },
  };
}

export async function getCurrentMentalState(userId: string): Promise<MentalState | null> {
  const { data } = await supabaseServer
    .from("jarvis_mental_state")
    .select("*")
    .eq("user_id", userId)
    .order("detected_at", { ascending: false })
    .limit(1)
    .single();

  if (data) {
    return data as MentalState;
  }

  return null;
}

export async function recordBehavioralSignal(
  userId: string,
  signalType: SignalType,
  signalData: Record<string, any>
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_behavioral_signals")
    .insert({
      user_id: userId,
      signal_type: signalType,
      signal_data: signalData,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to record behavioral signal: ${error?.message}`);
  }

  return (data as any).id;
}

