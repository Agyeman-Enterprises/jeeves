import { supabaseServer } from "@/lib/supabase/server";
import type { ForesightMap } from "./types";
import { getNodesByDomain } from "../cuil/graph";
import { simulateClinical } from "../simulation/clinical";
import { simulateOperational } from "../simulation/operational";
import { getCognitiveBudget } from "../cerae/cognitive";

export async function generateTacticalForesight(
  userId: string,
  startDate?: Date
): Promise<ForesightMap> {
  const start = startDate || new Date();
  const end = new Date(start);
  end.setDate(end.getDate() + 10);

  // Analyze various domains for 10-day window
  const [clinicLoad, maWorkload, glpFollowups, patientRisk, fileBacklog, financialFlows, cognitivePatterns] =
    await Promise.all([
      analyzeClinicLoad(userId, start, end),
      analyzeMAWorkload(userId, start, end),
      analyzeGLPFollowups(userId, start, end),
      analyzePatientRisk(userId, start, end),
      analyzeFileBacklog(userId),
      analyzeFinancialFlows(userId, start, end),
      analyzeCognitivePatterns(userId, start, end),
    ]);

  // Identify risks
  const risks = identifyRisks({
    clinicLoad,
    maWorkload,
    glpFollowups,
    patientRisk,
    fileBacklog,
    financialFlows,
    cognitivePatterns,
  });

  // Identify opportunities
  const opportunities = identifyOpportunities({
    clinicLoad,
    maWorkload,
    glpFollowups,
    financialFlows,
    cognitivePatterns,
  });

  // Identify bottlenecks
  const bottlenecks = identifyBottlenecks({
    clinicLoad,
    maWorkload,
    fileBacklog,
    cognitivePatterns,
  });

  // Generate recommended actions
  const recommendedActions = generateRecommendedActions({
    risks,
    opportunities,
    bottlenecks,
    cognitivePatterns,
  });

  // Generate day-by-day map
  const dayByDayMap = generateDayByDayMap({
    clinicLoad,
    maWorkload,
    glpFollowups,
    patientRisk,
    financialFlows,
    cognitivePatterns,
  });

  const foresightMap: ForesightMap = {
    user_id: userId,
    horizon: "TACTICAL_10DAY",
    forecast_start_date: start.toISOString().split("T")[0],
    forecast_end_date: end.toISOString().split("T")[0],
    status: "COMPLETED",
    foresight_data: {
      day_by_day: dayByDayMap,
      clinic_load: clinicLoad,
      ma_workload: maWorkload,
      glp_followups: glpFollowups,
      patient_risk: patientRisk,
      file_backlog: fileBacklog,
      financial_flows: financialFlows,
      cognitive_patterns: cognitivePatterns,
    },
    risks,
    opportunities,
    bottlenecks,
    recommended_actions: recommendedActions,
    confidence_score: 0.75, // Higher confidence for short-term forecasts
    factors_used: {
      historical_data: true,
      current_state: true,
      trend_analysis: true,
    },
  };

  // Store foresight map
  await storeForesightMap(userId, foresightMap);

  return foresightMap;
}

async function analyzeClinicLoad(userId: string, start: Date, end: Date): Promise<Record<string, any>> {
  // Get clinical events in the forecast window
  const { data: events } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .gte("created_at", start.toISOString())
    .lte("created_at", end.toISOString());

  // Simulate clinic load
  const simulation = await simulateClinical(userId, {
    scenario: "CLINIC_LOAD",
    time_horizon: "10DAYS",
  });

  return {
    total_appointments: (events || []).filter((e: any) => e.event_type === "APPOINTMENT_BOOKED").length,
    projected_volume: simulation.predicted_hours_per_week || 0,
    peak_days: [], // Would calculate from historical patterns
  };
}

async function analyzeMAWorkload(userId: string, start: Date, end: Date): Promise<Record<string, any>> {
  const simulation = await simulateOperational(userId, {
    scenario: "MA_WORKLOAD",
    time_horizon: "10DAYS",
  });

  return {
    projected_hours: simulation.predicted_hours_per_week || 0,
    peak_days: [],
    capacity_utilization: simulation.utilization_percentage || 0,
  };
}

async function analyzeGLPFollowups(userId: string, start: Date, end: Date): Promise<Record<string, any>> {
  const { data: patients } = await supabaseServer
    .from("jarvis_patient_state")
    .select("*")
    .eq("user_id", userId)
    .eq("service_line", "glp");

  // Calculate follow-ups due in window
  const followupsDue = (patients || []).filter((p: any) => {
    // Simplified - would check actual follow-up dates
    return true;
  }).length;

  return {
    followups_due: followupsDue,
    projected_surge_days: [],
  };
}

async function analyzePatientRisk(userId: string, start: Date, end: Date): Promise<Record<string, any>> {
  const { data: events } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .in("event_type", ["CRITICAL_LAB_RESULT", "PATIENT_HOSPITALIZED", "MED_NONCOMPLIANCE_FLAG"]);

  return {
    high_risk_patients: (events || []).length,
    risk_trend: "STABLE", // Would calculate from historical data
  };
}

async function analyzeFileBacklog(userId: string): Promise<Record<string, any>> {
  // Simplified - would analyze actual file/document backlog
  return {
    pending_files: 0,
    backlog_trend: "STABLE",
  };
}

async function analyzeFinancialFlows(userId: string, start: Date, end: Date): Promise<Record<string, any>> {
  const { data: transactions } = await supabaseServer
    .from("nexus_financial_transactions")
    .select("*")
    .eq("user_id", userId)
    .gte("occurred_at", start.toISOString())
    .lte("occurred_at", end.toISOString());

  const income = (transactions || []).filter((t: any) => t.direction === "INCOME").reduce((sum: number, t: any) => sum + parseFloat(t.amount || 0), 0);
  const expenses = (transactions || []).filter((t: any) => t.direction === "EXPENSE").reduce((sum: number, t: any) => sum + parseFloat(t.amount || 0), 0);

  return {
    projected_income: income,
    projected_expenses: expenses,
    net_cashflow: income - expenses,
  };
}

async function analyzeCognitivePatterns(userId: string, start: Date, end: Date): Promise<Record<string, any>> {
  const budgets = [];
  for (let i = 0; i < 10; i++) {
    const date = new Date(start);
    date.setDate(date.getDate() + i);
    const budget = await getCognitiveBudget(userId, date.toISOString().split("T")[0]);
    if (budget) {
      budgets.push(budget);
    }
  }

  return {
    energy_trend: calculateEnergyTrend(budgets),
    low_energy_days: budgets.filter((b) => (b.total_energy_percentage || 0) < 50).length,
    high_energy_days: budgets.filter((b) => (b.total_energy_percentage || 0) > 70).length,
  };
}

function calculateEnergyTrend(budgets: any[]): string {
  if (budgets.length < 2) return "STABLE";
  const first = budgets[0]?.total_energy_percentage || 50;
  const last = budgets[budgets.length - 1]?.total_energy_percentage || 50;
  if (last > first + 10) return "RISING";
  if (last < first - 10) return "FALLING";
  return "STABLE";
}

function identifyRisks(analysis: Record<string, any>): Record<string, any> {
  const risks: any[] = [];

  if (analysis.maWorkload.projected_hours > 40) {
    risks.push({
      type: "BOTTLENECK",
      severity: "HIGH",
      description: "MA workload exceeds capacity",
      predicted_date: new Date().toISOString().split("T")[0],
    });
  }

  if (analysis.patientRisk.high_risk_patients > 5) {
    risks.push({
      type: "CLINICAL",
      severity: "HIGH",
      description: "Multiple high-risk patients require attention",
      predicted_date: new Date().toISOString().split("T")[0],
    });
  }

  if (analysis.financialFlows.net_cashflow < 0) {
    risks.push({
      type: "FINANCIAL",
      severity: "MEDIUM",
      description: "Negative cashflow projected",
      predicted_date: new Date().toISOString().split("T")[0],
    });
  }

  return { risks };
}

function identifyOpportunities(analysis: Record<string, any>): Record<string, any> {
  const opportunities: any[] = [];

  if (analysis.cognitivePatterns.high_energy_days > 3) {
    opportunities.push({
      type: "PRODUCTIVITY",
      description: "Multiple high-energy days - good time for deep work",
      predicted_date: new Date().toISOString().split("T")[0],
    });
  }

  return { opportunities };
}

function identifyBottlenecks(analysis: Record<string, any>): Record<string, any> {
  const bottlenecks: any[] = [];

  if (analysis.maWorkload.capacity_utilization > 85) {
    bottlenecks.push({
      type: "OPERATIONAL",
      description: "MA capacity near limit",
      predicted_date: new Date().toISOString().split("T")[0],
    });
  }

  return { bottlenecks };
}

function generateRecommendedActions(context: Record<string, any>): Record<string, any> {
  const actions: any[] = [];

  if (context.risks.risks?.length > 0) {
    context.risks.risks.forEach((risk: any) => {
      if (risk.type === "BOTTLENECK" && risk.severity === "HIGH") {
        actions.push({
          type: "REALLOCATE",
          description: "Pre-allocate MA time for workload surge",
          priority: "HIGH",
          target_date: risk.predicted_date,
        });
      }
    });
  }

  return { actions };
}

function generateDayByDayMap(analysis: Record<string, any>): Record<string, any> {
  const dayMap: Record<string, any> = {};

  // Generate day-by-day predictions
  for (let i = 0; i < 10; i++) {
    const date = new Date();
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split("T")[0];

    dayMap[dateStr] = {
      clinic_load: "NORMAL", // Would calculate from analysis
      ma_workload: "NORMAL",
      glp_followups: 0,
      cognitive_energy: "MEDIUM",
      risks: [],
      opportunities: [],
    };
  }

  return dayMap;
}

async function storeForesightMap(userId: string, map: ForesightMap): Promise<void> {
  await supabaseServer
    .from("jarvis_foresight_maps")
    .upsert({
      ...map,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "user_id,horizon,forecast_start_date",
    });
}

