import { supabaseServer } from "@/lib/supabase/server";
import type { FutureSelfPrediction, PredictionType, WarningLevel } from "./types";
import { getLongitudinalIdentity } from "./identity";
import { getTimePatterns } from "./patterns";

export async function predictFutureSelf(
  userId: string,
  predictionType: PredictionType,
  timeHorizon: string
): Promise<FutureSelfPrediction> {
  let predictedValue: Record<string, any> = {};
  let warningLevel: WarningLevel = "LOW";
  let recommendations: Record<string, any> = {};

  switch (predictionType) {
    case "burnout_risk":
      const burnoutPrediction = await predictBurnoutRisk(userId, timeHorizon);
      predictedValue = burnoutPrediction.predicted_value;
      warningLevel = burnoutPrediction.warning_level;
      recommendations = burnoutPrediction.recommendations;
      break;

    case "workload_sustainability":
      const workloadPrediction = await predictWorkloadSustainability(userId, timeHorizon);
      predictedValue = workloadPrediction.predicted_value;
      warningLevel = workloadPrediction.warning_level;
      recommendations = workloadPrediction.recommendations;
      break;

    case "energy_decline":
      const energyPrediction = await predictEnergyDecline(userId, timeHorizon);
      predictedValue = energyPrediction.predicted_value;
      warningLevel = energyPrediction.warning_level;
      recommendations = energyPrediction.recommendations;
      break;

    default:
      predictedValue = { message: "Prediction not yet implemented" };
  }

  // Calculate expiration date
  const expiresAt = new Date();
  const days = parseInt(timeHorizon.replace("days", "")) || 30;
  expiresAt.setDate(expiresAt.getDate() + days);

  // Store prediction
  const { data, error } = await supabaseServer
    .from("jarvis_future_self_predictions")
    .insert({
      user_id: userId,
      prediction_type: predictionType,
      time_horizon: timeHorizon,
      predicted_value: predictedValue,
      confidence_score: 0.7,
      warning_level: warningLevel,
      recommendations,
      expires_at: expiresAt.toISOString(),
    } as any)
    .select()
    .single();

  if (error || !data) {
    throw new Error(`Failed to create future self prediction: ${error?.message}`);
  }

  return data as FutureSelfPrediction;
}

async function predictBurnoutRisk(
  userId: string,
  timeHorizon: string
): Promise<{
  predicted_value: Record<string, any>;
  warning_level: WarningLevel;
  recommendations: Record<string, any>;
}> {
  // Get fatigue and stress trends
  const fatigueIdentity = await getLongitudinalIdentity(userId, "fatigue_pattern");
  const stressIdentity = await getLongitudinalIdentity(userId, "stress");

  const fatigueTrend = fatigueIdentity[0]?.trend_30days || 0;
  const stressTrend = stressIdentity[0]?.trend_30days || 0;

  // Calculate burnout risk
  const burnoutRisk = Math.min(100, (fatigueTrend + stressTrend) * 10);

  let warningLevel: WarningLevel = "LOW";
  if (burnoutRisk > 70) {
    warningLevel = "CRITICAL";
  } else if (burnoutRisk > 50) {
    warningLevel = "HIGH";
  } else if (burnoutRisk > 30) {
    warningLevel = "MEDIUM";
  }

  const recommendations: Record<string, any> = {};
  if (burnoutRisk > 50) {
    recommendations.actions = [
      "Delegate high-cognitive-load tasks",
      "Reduce meeting frequency",
      "Schedule recovery time",
      "Consider reducing operational autonomy temporarily",
    ];
    recommendations.message = `At your current pace, you will hit overload by ${timeHorizon}. I recommend delegating tasks, reducing meetings, and scheduling recovery time.`;
  }

  return {
    predicted_value: {
      burnout_risk_score: burnoutRisk,
      fatigue_trend: fatigueTrend,
      stress_trend: stressTrend,
    },
    warning_level: warningLevel,
    recommendations,
  };
}

async function predictWorkloadSustainability(
  userId: string,
  timeHorizon: string
): Promise<{
  predicted_value: Record<string, any>;
  warning_level: WarningLevel;
  recommendations: Record<string, any>;
}> {
  // Get decision load and work intensity trends
  const decisionLoadIdentity = await getLongitudinalIdentity(userId, "decision_load");
  const workIntensityIdentity = await getLongitudinalIdentity(userId, "work_intensity");

  const decisionLoadTrend = decisionLoadIdentity[0]?.trend_30days || 0;
  const workIntensityTrend = workIntensityIdentity[0]?.trend_30days || 0;

  // Calculate sustainability score
  const sustainabilityScore = 100 - Math.abs(decisionLoadTrend + workIntensityTrend) * 5;

  let warningLevel: WarningLevel = "LOW";
  if (sustainabilityScore < 30) {
    warningLevel = "CRITICAL";
  } else if (sustainabilityScore < 50) {
    warningLevel = "HIGH";
  } else if (sustainabilityScore < 70) {
    warningLevel = "MEDIUM";
  }

  const recommendations: Record<string, any> = {};
  if (sustainabilityScore < 50) {
    recommendations.actions = [
      "Reduce decision load",
      "Automate routine decisions",
      "Batch similar tasks",
      "Increase delegation",
    ];
  }

  return {
    predicted_value: {
      sustainability_score: sustainabilityScore,
      decision_load_trend: decisionLoadTrend,
      work_intensity_trend: workIntensityTrend,
    },
    warning_level: warningLevel,
    recommendations,
  };
}

async function predictEnergyDecline(
  userId: string,
  timeHorizon: string
): Promise<{
  predicted_value: Record<string, any>;
  warning_level: WarningLevel;
  recommendations: Record<string, any>;
}> {
  // Get energy trend
  const energyIdentity = await getLongitudinalIdentity(userId, "energy");
  const energyTrend = energyIdentity[0]?.trend_30days || 0;

  // Project energy decline
  const days = parseInt(timeHorizon.replace("days", "")) || 30;
  const projectedEnergy = (energyIdentity[0]?.current_value || 50) + energyTrend * (days / 30);

  let warningLevel: WarningLevel = "LOW";
  if (projectedEnergy < 30) {
    warningLevel = "CRITICAL";
  } else if (projectedEnergy < 40) {
    warningLevel = "HIGH";
  } else if (projectedEnergy < 50) {
    warningLevel = "MEDIUM";
  }

  const recommendations: Record<string, any> = {};
  if (projectedEnergy < 40) {
    recommendations.actions = [
      "Schedule rest periods",
      "Reduce high-energy-demand tasks",
      "Optimize work schedule for energy peaks",
    ];
  }

  return {
    predicted_value: {
      current_energy: energyIdentity[0]?.current_value || 50,
      projected_energy: projectedEnergy,
      energy_trend: energyTrend,
    },
    warning_level: warningLevel,
    recommendations,
  };
}

export async function getFutureSelfPredictions(
  userId: string,
  predictionType?: PredictionType
): Promise<FutureSelfPrediction[]> {
  let query = supabaseServer
    .from("jarvis_future_self_predictions")
    .select("*")
    .eq("user_id", userId)
    .gt("expires_at", new Date().toISOString())
    .order("created_at", { ascending: false });

  if (predictionType) {
    query = query.eq("prediction_type", predictionType);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get future self predictions: ${error.message}`);
  }

  return (data || []) as FutureSelfPrediction[];
}

