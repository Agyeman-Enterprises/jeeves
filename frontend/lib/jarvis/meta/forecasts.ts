import { supabaseServer } from "@/lib/supabase/server";
import type { ForecastAccuracy, ForecastType } from "./types";

export async function recordForecastAccuracy(
  userId: string,
  forecastType: ForecastType,
  forecastId: string,
  forecastValue: Record<string, any>,
  actualValue: Record<string, any>,
  forecastHorizon?: string
): Promise<string> {
  // Calculate error metrics
  const errorMargin = calculateErrorMargin(forecastValue, actualValue);
  const errorPercentage = calculateErrorPercentage(forecastValue, actualValue);
  const accuracyScore = 1 - Math.min(1, Math.abs(errorPercentage) / 100); // 0 to 1

  // Generate learned adjustments
  const learnedAdjustments = generateAdjustments(forecastType, forecastValue, actualValue, errorPercentage);

  const { data, error } = await supabaseServer
    .from("jarvis_forecast_accuracy")
    .insert({
      user_id: userId,
      forecast_type: forecastType,
      forecast_id: forecastId,
      forecast_value: forecastValue,
      actual_value: actualValue,
      forecast_horizon: forecastHorizon,
      error_margin: errorMargin,
      error_percentage: errorPercentage,
      accuracy_score: accuracyScore,
      learned_adjustments: learnedAdjustments,
      actual_recorded_at: new Date().toISOString(),
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to record forecast accuracy: ${error?.message}`);
  }

  return (data as any).id;
}

function calculateErrorMargin(forecast: Record<string, any>, actual: Record<string, any>): number {
  // Simple numeric comparison - in production, this would handle different value types
  const forecastNum = typeof forecast.value === "number" ? forecast.value : parseFloat(forecast.value || 0);
  const actualNum = typeof actual.value === "number" ? actual.value : parseFloat(actual.value || 0);
  return Math.abs(forecastNum - actualNum);
}

function calculateErrorPercentage(forecast: Record<string, any>, actual: Record<string, any>): number {
  const forecastNum = typeof forecast.value === "number" ? forecast.value : parseFloat(forecast.value || 0);
  const actualNum = typeof actual.value === "number" ? actual.value : parseFloat(actual.value || 0);
  if (forecastNum === 0) return actualNum === 0 ? 0 : 100;
  return ((actualNum - forecastNum) / Math.abs(forecastNum)) * 100;
}

function generateAdjustments(
  forecastType: ForecastType,
  forecast: Record<string, any>,
  actual: Record<string, any>,
  errorPercentage: number
): Record<string, any> {
  const adjustments: Record<string, any> = {};

  if (Math.abs(errorPercentage) > 20) {
    // Significant error - suggest adjustments
    if (errorPercentage > 0) {
      adjustments.direction = "UNDERESTIMATED";
      adjustments.suggestion = `Forecast was ${errorPercentage.toFixed(1)}% below actual. Consider increasing forecast values.`;
    } else {
      adjustments.direction = "OVERESTIMATED";
      adjustments.suggestion = `Forecast was ${Math.abs(errorPercentage).toFixed(1)}% above actual. Consider decreasing forecast values.`;
    }
  } else {
    adjustments.direction = "ACCURATE";
    adjustments.suggestion = "Forecast was within acceptable range. Continue using current model.";
  }

  return adjustments;
}

export async function getForecastAccuracy(
  userId: string,
  forecastType: ForecastType,
  limit: number = 20
): Promise<ForecastAccuracy[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_forecast_accuracy")
    .select("*")
    .eq("user_id", userId)
    .eq("forecast_type", forecastType)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    throw new Error(`Failed to get forecast accuracy: ${error.message}`);
  }

  return (data || []) as ForecastAccuracy[];
}

export async function getAverageForecastAccuracy(
  userId: string,
  forecastType: ForecastType,
  days: number = 30
): Promise<number> {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  const { data, error } = await supabaseServer
    .from("jarvis_forecast_accuracy")
    .select("accuracy_score")
    .eq("user_id", userId)
    .eq("forecast_type", forecastType)
    .gte("created_at", cutoffDate.toISOString())
    .not("accuracy_score", "is", null);

  if (error) {
    throw new Error(`Failed to get average forecast accuracy: ${error.message}`);
  }

  const scores = (data || []).map((d: any) => d.accuracy_score as number);
  if (scores.length === 0) return 0.5; // Default neutral

  return scores.reduce((a, b) => a + b, 0) / scores.length;
}

