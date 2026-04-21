import { supabaseServer } from "@/lib/supabase/server";
import type { TimePattern, PatternType, IdentityDimension } from "./types";

export async function detectTimePattern(
  userId: string,
  patternType: PatternType,
  patternName: string,
  dimension: IdentityDimension,
  effectValue: number,
  timeSpec: Record<string, any>
): Promise<TimePattern> {
  // Get existing pattern
  const { data: existing } = await supabaseServer
    .from("jarvis_time_patterns")
    .select("*")
    .eq("user_id", userId)
    .eq("pattern_type", patternType)
    .eq("pattern_name", patternName)
    .single();

  if (existing) {
    // Update existing pattern
    const pattern = existing as any;
    const sampleCount = pattern.sample_count || 1;
    const newSampleCount = sampleCount + 1;

    // Update effect value (weighted average)
    const currentEffect = pattern.effect_value || effectValue;
    const newEffect = (currentEffect * sampleCount + effectValue) / newSampleCount;

    // Calculate confidence
    const confidenceScore = Math.min(1.0, newSampleCount / 20);

    const updateData: Record<string, any> = {
      effect_value: newEffect,
      confidence_score: confidenceScore,
      sample_count: newSampleCount,
      last_observed_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await (supabaseServer as any)
      .from("jarvis_time_patterns")
      .update(updateData)
      .eq("id", pattern.id);

    return { ...pattern, ...updateData } as TimePattern;
  } else {
    // Create new pattern
    const { data: newPattern } = await supabaseServer
      .from("jarvis_time_patterns")
      .insert({
        user_id: userId,
        pattern_type: patternType,
        pattern_name: patternName,
        time_spec: timeSpec,
        dimension,
        effect_value: effectValue,
        confidence_score: 0.1,
        sample_count: 1,
        first_observed_at: new Date().toISOString(),
        last_observed_at: new Date().toISOString(),
      } as any)
      .select()
      .single();

    return newPattern as TimePattern;
  }
}

export async function detectDailyPatterns(userId: string): Promise<TimePattern[]> {
  const patterns: TimePattern[] = [];

  // Get energy patterns by hour
  const { data: energyPatterns } = await supabaseServer
    .from("jarvis_energy_patterns")
    .select("*")
    .eq("user_id", userId);

  if (energyPatterns) {
    for (const pattern of energyPatterns as any[]) {
      if (pattern.pattern_type === "peak" && pattern.avg_energy_level > 70) {
        await detectTimePattern(
          userId,
          "DAILY",
          `hour_${pattern.hour_of_day}_peak`,
          "energy",
          pattern.avg_energy_level,
          { hour: pattern.hour_of_day, day_of_week: pattern.day_of_week }
        );
      }
      if (pattern.pattern_type === "valley" && pattern.avg_energy_level < 30) {
        await detectTimePattern(
          userId,
          "DAILY",
          `hour_${pattern.hour_of_day}_valley`,
          "energy",
          pattern.avg_energy_level,
          { hour: pattern.hour_of_day, day_of_week: pattern.day_of_week }
        );
      }
    }
  }

  return patterns;
}

export async function detectWeeklyPatterns(userId: string): Promise<TimePattern[]> {
  // Analyze patterns by day of week
  const { data: weeklyData } = await supabaseServer
    .from("jarvis_energy_patterns")
    .select("*")
    .eq("user_id", userId);

  if (!weeklyData) {
    return [];
  }

  // Group by day of week
  const byDay: Record<number, any[]> = {};
  for (const record of weeklyData as any[]) {
    const day = record.day_of_week;
    if (!byDay[day]) {
      byDay[day] = [];
    }
    byDay[day].push(record);
  }

  const patterns: TimePattern[] = [];

  for (const [day, records] of Object.entries(byDay)) {
    const avgEnergy = records.reduce((sum, r) => sum + (r.avg_energy_level || 0), 0) / records.length;
    const avgFocus = records.reduce((sum, r) => sum + (r.avg_focus_level || 0), 0) / records.length;

    const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const dayName = dayNames[parseInt(day)];

    if (avgEnergy > 70 && avgFocus > 70) {
      await detectTimePattern(
        userId,
        "WEEKLY",
        `${dayName.toLowerCase()}_high_power`,
        "energy",
        avgEnergy,
        { day_of_week: parseInt(day) }
      );
    }
  }

  return patterns;
}

export async function getTimePatterns(
  userId: string,
  patternType?: PatternType
): Promise<TimePattern[]> {
  let query = supabaseServer
    .from("jarvis_time_patterns")
    .select("*")
    .eq("user_id", userId);

  if (patternType) {
    query = query.eq("pattern_type", patternType);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get time patterns: ${error.message}`);
  }

  return (data || []) as TimePattern[];
}

