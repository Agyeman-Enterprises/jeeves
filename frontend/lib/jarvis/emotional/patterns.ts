import { supabaseServer } from "@/lib/supabase/server";
import type { EnergyPattern, MentalState } from "./types";

export async function updateEnergyPattern(
  userId: string,
  state: MentalState
): Promise<void> {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const hourOfDay = now.getHours();

  // Get existing pattern
  const { data: existing } = await supabaseServer
    .from("jarvis_energy_patterns")
    .select("*")
    .eq("user_id", userId)
    .eq("day_of_week", dayOfWeek)
    .eq("hour_of_day", hourOfDay)
    .single();

  if (existing) {
    // Update existing pattern with weighted average
    const pattern = existing as any;
    const sampleCount = pattern.sample_count || 1;
    const newSampleCount = sampleCount + 1;

    const avgEnergyLevel =
      (pattern.avg_energy_level * sampleCount + state.energy_level) / newSampleCount;
    const avgFocusLevel =
      (pattern.avg_focus_level * sampleCount + state.focus_level) / newSampleCount;
    const avgStressLevel =
      (pattern.avg_stress_level * sampleCount + state.stress_level) / newSampleCount;

    // Determine pattern type
    const patternType = determinePatternType(avgEnergyLevel, avgFocusLevel, avgStressLevel);

    // Calculate confidence (more samples = higher confidence)
    const confidenceScore = Math.min(1.0, newSampleCount / 20); // Max confidence at 20 samples

    await (supabaseServer as any)
      .from("jarvis_energy_patterns")
      .update({
        avg_energy_level: avgEnergyLevel,
        avg_focus_level: avgFocusLevel,
        avg_stress_level: avgStressLevel,
        pattern_type: patternType,
        confidence_score: confidenceScore,
        sample_count: newSampleCount,
        updated_at: new Date().toISOString(),
      } as any)
      .eq("id", pattern.id);
  } else {
    // Create new pattern
    const patternType = determinePatternType(
      state.energy_level,
      state.focus_level,
      state.stress_level
    );

    await supabaseServer
      .from("jarvis_energy_patterns")
      .insert({
        user_id: userId,
        day_of_week: dayOfWeek,
        hour_of_day: hourOfDay,
        avg_energy_level: state.energy_level,
        avg_focus_level: state.focus_level,
        avg_stress_level: state.stress_level,
        pattern_type: patternType,
        confidence_score: 0.1, // Low confidence for first sample
        sample_count: 1,
      } as any);
  }
}

function determinePatternType(
  energyLevel: number,
  focusLevel: number,
  stressLevel: number
): "peak" | "valley" | "steady" | "variable" {
  if (energyLevel > 70 && focusLevel > 70 && stressLevel < 30) {
    return "peak";
  }
  if (energyLevel < 30 || focusLevel < 30 || stressLevel > 70) {
    return "valley";
  }
  if (Math.abs(energyLevel - 50) < 10 && Math.abs(focusLevel - 50) < 10) {
    return "steady";
  }
  return "variable";
}

export async function getEnergyPattern(
  userId: string,
  dayOfWeek: number,
  hourOfDay: number
): Promise<EnergyPattern | null> {
  const { data } = await supabaseServer
    .from("jarvis_energy_patterns")
    .select("*")
    .eq("user_id", userId)
    .eq("day_of_week", dayOfWeek)
    .eq("hour_of_day", hourOfDay)
    .single();

  if (data) {
    return data as EnergyPattern;
  }

  return null;
}

export async function getDailyEnergyProfile(userId: string, dayOfWeek: number): Promise<EnergyPattern[]> {
  const { data } = await supabaseServer
    .from("jarvis_energy_patterns")
    .select("*")
    .eq("user_id", userId)
    .eq("day_of_week", dayOfWeek)
    .order("hour_of_day", { ascending: true });

  return (data || []) as EnergyPattern[];
}

