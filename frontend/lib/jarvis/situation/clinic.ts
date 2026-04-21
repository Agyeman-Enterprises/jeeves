import { supabaseServer } from "@/lib/supabase/server";
import type { SituationRoomSnapshot, SituationRoomAlert, SituationRoomRecommendation } from "./types";
import { simulateClinical } from "../simulation/clinical";
import { simulateOperational } from "../simulation/operational";

export async function generateClinicSituationRoom(
  userId: string
): Promise<SituationRoomSnapshot> {
  // A. Live Clinical Pipeline
  const { data: clinicalEvents } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .gte("created_at", new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
    .order("created_at", { ascending: false });

  const { data: patientStates } = await supabaseServer
    .from("jarvis_patient_state")
    .select("*")
    .eq("user_id", userId);

  // Calculate metrics
  const clinicVolumeToday = (clinicalEvents || []).filter(
    (e) => e.event_type === "APPOINTMENT_BOOKED"
  ).length;

  const overdueLabs = (clinicalEvents || []).filter(
    (e) => e.event_type === "LAB_RESULT_RECEIVED" && e.status === "NEW"
  ).length;

  const gLPPatients = (patientStates || []).filter((p) => p.service_line === "glp").length;

  // B. Patient Conditions Requiring Action
  const urgentFlags = (clinicalEvents || []).filter(
    (e) => e.event_type === "CRITICAL_LAB_RESULT" || e.event_type === "PATIENT_HOSPITALIZED"
  ).length;

  // C. MA Workload Forecast
  const maWorkloadSim = await simulateOperational(userId, {
    scenario: "MA_WORKLOAD",
    time_horizon: "1WEEK",
  });

  // D. Scheduler Load Projection
  const schedulerSim = await simulateOperational(userId, {
    scenario: "SCHEDULING_BOTTLENECK",
    time_horizon: "1WEEK",
  });

  // E. Clinical Risk Panel
  const { data: riskPredictions } = await supabaseServer
    .from("jarvis_risk_predictions")
    .select("*")
    .eq("user_id", userId)
    .eq("risk_type", "CLINICAL")
    .order("created_at", { ascending: false })
    .limit(10);

  // Generate alerts
  const alerts: SituationRoomAlert[] = [];
  if (overdueLabs > 5) {
    alerts.push({
      user_id: userId,
      room_type: "CLINIC",
      alert_type: "BOTTLENECK",
      severity: "MEDIUM",
      title: "Overdue Labs Requiring Review",
      description: `${overdueLabs} lab results are pending review`,
      recommended_actions: {
        actions: ["Review and process lab results", "Message patients if needed"],
      },
    });
  }

  if (urgentFlags > 0) {
    alerts.push({
      user_id: userId,
      room_type: "CLINIC",
      alert_type: "RISK",
      severity: "HIGH",
      title: "Urgent Patient Flags",
      description: `${urgentFlags} patients require immediate attention`,
      recommended_actions: {
        actions: ["Review urgent flags immediately", "Prioritize patient care"],
      },
    });
  }

  // Generate recommendations
  const recommendations: SituationRoomRecommendation[] = [];

  if (maWorkloadSim.predicted_hours_per_week > 40) {
    recommendations.push({
      user_id: userId,
      room_type: "CLINIC",
      recommendation_type: "OPTIMIZATION",
      title: "MA Workload Optimization",
      description: `MA workload projected at ${maWorkloadSim.predicted_hours_per_week.toFixed(1)} hours/week. Consider redistributing tasks or adding capacity.`,
      priority: 2,
      impact_estimate: {
        impact: "Prevents burnout and maintains quality",
      },
    });
  }

  if (schedulerSim.utilization_percentage > 85) {
    recommendations.push({
      user_id: userId,
      room_type: "CLINIC",
      recommendation_type: "PREVENTION",
      title: "Scheduling Capacity Alert",
      description: `Scheduling utilization at ${schedulerSim.utilization_percentage.toFixed(1)}%. Consider adding appointment slots or extending hours.`,
      priority: 1,
      impact_estimate: {
        impact: "Prevents scheduling bottlenecks",
      },
    });
  }

  // Create snapshot
  const snapshot: SituationRoomSnapshot = {
    user_id: userId,
    room_type: "CLINIC",
    snapshot_data: {
      live_pipeline: {
        clinic_volume_today: clinicVolumeToday,
        no_show_risk: "LOW", // Simplified
        overdue_labs: overdueLabs,
        follow_up_load: gLPPatients * 0.25, // ~25% need follow-up per month
        glp_patient_count: gLPPatients,
        urgent_flags: urgentFlags,
      },
      patient_conditions: {
        unstable_diabetics: 0, // Would calculate from patient data
        abnormal_labs: overdueLabs,
        med_change_candidates: 0,
        high_risk_vitals: urgentFlags,
      },
      ma_workload: {
        chart_prep_load: maWorkloadSim.predicted_hours_per_week || 0,
        refill_backlog: 0,
        patient_messages: 0,
        care_coordination_tasks: 0,
      },
      scheduler_load: {
        utilization: schedulerSim.utilization_percentage || 0,
        bottlenecks: schedulerSim.risk_level || "LOW",
        upcoming_spikes: [],
      },
      clinical_risk: {
        medication_safety_alerts: 0,
        missing_documentation: 0,
        delayed_followups: 0,
        patient_deterioration_risk: (riskPredictions || []).length,
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
    agent_status: {
      active_agents: ["hospitalization_agent", "glp_monitor_agent", "scheduler_agent", "triage_agent"],
      agent_load: {},
    },
  };

  return snapshot;
}

