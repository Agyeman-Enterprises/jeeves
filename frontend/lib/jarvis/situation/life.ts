import { supabaseServer } from "@/lib/supabase/server";
import type { SituationRoomSnapshot, SituationRoomAlert, SituationRoomRecommendation } from "./types";
import { getCurrentMentalState } from "../emotional/state";
import { getLongitudinalIdentity } from "../longitudinal/identity";
import { getFutureSelfPredictions } from "../longitudinal/predictions";

export async function generateLifeSituationRoom(
  userId: string
): Promise<SituationRoomSnapshot> {
  // A. Cognitive Load Telemetry
  const currentState = await getCurrentMentalState(userId);

  // B. Longitudinal Trends
  const energyIdentity = await getLongitudinalIdentity(userId, "energy");
  const stressIdentity = await getLongitudinalIdentity(userId, "stress");
  const fatigueIdentity = await getLongitudinalIdentity(userId, "fatigue_pattern");

  // C. Overcommitment Detection
  const { data: activePlans } = await supabaseServer
    .from("jarvis_plans")
    .select("*")
    .eq("user_id", userId)
    .in("status", ["PENDING", "RUNNING"]);

  const { data: appointments } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .eq("event_type", "APPOINTMENT_BOOKED")
    .gte("created_at", new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());

  // D. Future Self Predictions
  const burnoutPrediction = await getFutureSelfPredictions(userId, "burnout_risk");
  const workloadPrediction = await getFutureSelfPredictions(userId, "workload_sustainability");

  // Generate alerts
  const alerts: SituationRoomAlert[] = [];

  if (currentState && currentState.cognitive_bandwidth < 30) {
    alerts.push({
      user_id: userId,
      room_type: "LIFE",
      alert_type: "OVERLOAD",
      severity: "HIGH",
      title: "Cognitive Overload Detected",
      description: "Your cognitive bandwidth is critically low. Consider reducing load.",
      recommended_actions: {
        actions: ["Reduce non-critical notifications", "Defer non-urgent tasks", "Take a break"],
      },
    });
  }

  if (burnoutPrediction.length > 0 && burnoutPrediction[0].warning_level === "CRITICAL") {
    alerts.push({
      user_id: userId,
      room_type: "LIFE",
      alert_type: "CRISIS",
      severity: "CRITICAL",
      title: "Burnout Risk Critical",
      description: burnoutPrediction[0].predicted_value.message || "High risk of burnout detected",
      recommended_actions: burnoutPrediction[0].recommendations,
    });
  }

  // Generate recommendations
  const recommendations: SituationRoomRecommendation[] = [];

  if (currentState && currentState.fatigue_level > 60) {
    recommendations.push({
      user_id: userId,
      room_type: "LIFE",
      recommendation_type: "PREVENTION",
      title: "Fatigue Management",
      description: "You've been experiencing elevated fatigue. Consider adjusting your schedule for better energy management.",
      priority: 1,
    });
  }

  if ((activePlans || []).length > 10) {
    recommendations.push({
      user_id: userId,
      room_type: "LIFE",
      recommendation_type: "OPTIMIZATION",
      title: "Project Overload",
      description: `You have ${(activePlans || []).length} active projects. Consider prioritizing or deferring some.`,
      priority: 2,
    });
  }

  // Create snapshot
  const snapshot: SituationRoomSnapshot = {
    user_id: userId,
    room_type: "LIFE",
    snapshot_data: {
      cognitive_load: {
        current_cognitive_demand: currentState?.cognitive_bandwidth || 100,
        mental_fatigue: currentState?.fatigue_level || 0,
        emotional_bandwidth: currentState?.cognitive_bandwidth || 100,
        decision_fatigue: currentState?.decision_load || 0,
        risk_of_overwhelm: currentState?.cognitive_bandwidth < 40 ? "HIGH" : "LOW",
        recommended_decision_volume: Math.max(0, (currentState?.cognitive_bandwidth || 100) / 10),
      },
      longitudinal_trends: {
        energy_baseline: energyIdentity[0]?.baseline_value || 50,
        energy_current: energyIdentity[0]?.current_value || 50,
        energy_trend: energyIdentity[0]?.trend_30days || 0,
        stress_baseline: stressIdentity[0]?.baseline_value || 0,
        stress_current: stressIdentity[0]?.current_value || 0,
        stress_trend: stressIdentity[0]?.trend_30days || 0,
        fatigue_trend: fatigueIdentity[0]?.trend_30days || 0,
      },
      overcommitment: {
        active_projects: (activePlans || []).length,
        upcoming_deadlines: 0, // Would calculate from plans
        microtasks: 0,
        appointments_this_week: (appointments || []).length,
        total_commitments: (activePlans || []).length + (appointments || []).length,
      },
      ai_behavioral_adjustments: {
        current_tone: currentState?.emotional_state === "tired" ? "gentle, supportive" : "balanced",
        current_verbosity: currentState?.cognitive_bandwidth < 40 ? "minimal" : "medium",
        current_autonomy: "COLLABORATIVE", // Would get from autonomy settings
        notification_density: currentState?.cognitive_bandwidth < 40 ? "reduced" : "normal",
      },
      future_predictions: {
        burnout_risk: burnoutPrediction[0]?.predicted_value || {},
        workload_sustainability: workloadPrediction[0]?.predicted_value || {},
      },
    },
    alerts: alerts.map((a) => ({
      id: a.id,
      type: a.alert_type,
      severity: a.severity,
      title: a.title,
      description: a.description,
    })),
    recommendations: recommendations.map((r) => ({
      id: r.id,
      type: r.recommendation_type,
      title: r.title,
      description: r.description,
      priority: r.priority,
    })),
  };

  return snapshot;
}

