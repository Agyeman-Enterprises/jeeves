import { supabaseServer } from "@/lib/supabase/server";
import type { OperationalPrediction, TimeHorizon, RiskLevel } from "./types";

export async function simulateOperational(
  userId: string,
  parameters: Record<string, any>
): Promise<Record<string, any>> {
  const scenario = parameters.scenario || "default";
  const timeHorizon = (parameters.time_horizon || "3MONTHS") as TimeHorizon;

  // Get operational data
  const { data: appointments } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .eq("event_type", "APPOINTMENT_BOOKED")
    .order("created_at", { ascending: false })
    .limit(500);

  const { data: tasks } = await supabaseServer
    .from("jarvis_agent_runs")
    .select("*")
    .eq("user_id", userId)
    .eq("agent_slug", "scheduler_agent")
    .order("created_at", { ascending: false })
    .limit(500);

  if (scenario === "SCHEDULING_BOTTLENECK") {
    return simulateSchedulingBottleneck(userId, parameters, appointments || [], timeHorizon);
  }

  if (scenario === "MA_WORKLOAD") {
    return simulateMAWorkload(userId, parameters, appointments || [], tasks || [], timeHorizon);
  }

  if (scenario === "CHARTING_BACKLOG") {
    return simulateChartingBacklog(userId, parameters, appointments || [], timeHorizon);
  }

  // Default
  return {
    scenario: "OPERATIONAL",
    time_horizon: timeHorizon,
    predicted_bottlenecks: [],
    risk_level: "LOW" as RiskLevel,
    confidence_score: 0.5,
  };
}

async function simulateSchedulingBottleneck(
  userId: string,
  parameters: Record<string, any>,
  appointments: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const weeks = getWeeksFromHorizon(timeHorizon);
  const avgAppointmentsPerWeek = appointments.length / Math.max(weeks, 1);
  const capacity = parameters.weekly_capacity || 40; // Default 40 appointments per week

  const predictedAppointments = avgAppointmentsPerWeek * weeks;
  const utilization = (predictedAppointments / (capacity * weeks)) * 100;

  let riskLevel: RiskLevel = "LOW";
  if (utilization > 90) {
    riskLevel = "CRITICAL";
  } else if (utilization > 75) {
    riskLevel = "HIGH";
  } else if (utilization > 60) {
    riskLevel = "MEDIUM";
  }

  const recommendations: string[] = [];
  if (utilization > 90) {
    recommendations.push("Consider adding more appointment slots");
    recommendations.push("Consider hiring additional provider");
  } else if (utilization > 75) {
    recommendations.push("Monitor capacity closely");
    recommendations.push("Consider extending hours");
  }

  return {
    scenario: "SCHEDULING_BOTTLENECK",
    time_horizon: timeHorizon,
    predicted_appointments: predictedAppointments,
    weekly_capacity: capacity,
    utilization_percentage: utilization,
    risk_level: riskLevel,
    recommendations,
    confidence_score: 0.7,
  };
}

async function simulateMAWorkload(
  userId: string,
  parameters: Record<string, any>,
  appointments: any[],
  tasks: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const weeks = getWeeksFromHorizon(timeHorizon);
  const avgAppointmentsPerWeek = appointments.length / Math.max(weeks, 1);
  const avgTasksPerWeek = tasks.length / Math.max(weeks, 1);

  // Estimate MA hours needed
  const appointmentPrepHours = avgAppointmentsPerWeek * 0.25; // 15 min per appointment
  const taskHours = avgTasksPerWeek * 0.5; // 30 min per task
  const totalHoursPerWeek = appointmentPrepHours + taskHours;

  const maxSustainableHours = parameters.max_hours_per_week || 40;
  const utilization = (totalHoursPerWeek / maxSustainableHours) * 100;

  let riskLevel: RiskLevel = "LOW";
  if (utilization > 100) {
    riskLevel = "CRITICAL";
  } else if (utilization > 85) {
    riskLevel = "HIGH";
  } else if (utilization > 70) {
    riskLevel = "MEDIUM";
  }

  const recommendations: string[] = [];
  if (utilization > 100) {
    recommendations.push(`MA workload exceeds capacity by ${(utilization - 100).toFixed(1)}%`);
    recommendations.push("Consider hiring additional MA");
    recommendations.push("Consider reducing appointment prep time");
  } else if (utilization > 85) {
    recommendations.push("MA workload approaching capacity");
    recommendations.push("Monitor for burnout risk");
  }

  return {
    scenario: "MA_WORKLOAD",
    time_horizon: timeHorizon,
    predicted_hours_per_week: totalHoursPerWeek,
    max_sustainable_hours: maxSustainableHours,
    utilization_percentage: utilization,
    risk_level: riskLevel,
    recommendations,
    confidence_score: 0.65,
  };
}

async function simulateChartingBacklog(
  userId: string,
  parameters: Record<string, any>,
  appointments: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const weeks = getWeeksFromHorizon(timeHorizon);
  const avgAppointmentsPerWeek = appointments.length / Math.max(weeks, 1);

  // Estimate charting time per appointment
  const chartingTimePerAppointment = parameters.charting_time_minutes || 10;
  const totalChartingHours = (avgAppointmentsPerWeek * chartingTimePerAppointment) / 60;

  const currentBacklog = parameters.current_backlog_hours || 0;
  const predictedBacklog = currentBacklog + (totalChartingHours * weeks);

  let riskLevel: RiskLevel = "LOW";
  if (predictedBacklog > 20) {
    riskLevel = "CRITICAL";
  } else if (predictedBacklog > 10) {
    riskLevel = "HIGH";
  } else if (predictedBacklog > 5) {
    riskLevel = "MEDIUM";
  }

  const recommendations: string[] = [];
  if (predictedBacklog > 20) {
    recommendations.push("Charting backlog will exceed safe levels");
    recommendations.push("Consider hiring additional MA for charting");
    recommendations.push("Consider reducing charting time per appointment");
  }

  return {
    scenario: "CHARTING_BACKLOG",
    time_horizon: timeHorizon,
    current_backlog_hours: currentBacklog,
    predicted_backlog_hours: predictedBacklog,
    risk_level: riskLevel,
    recommendations,
    confidence_score: 0.6,
  };
}

function getWeeksFromHorizon(horizon: TimeHorizon): number {
  switch (horizon) {
    case "1WEEK":
      return 1;
    case "1MONTH":
      return 4;
    case "3MONTHS":
      return 12;
    case "6MONTHS":
      return 26;
    case "1YEAR":
      return 52;
    default:
      return 12;
  }
}

