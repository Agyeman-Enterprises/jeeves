import { supabaseServer } from "@/lib/supabase/server";
import type { StrategicScenario, StrategyType } from "./types";
import { simulateClinical } from "./clinical";
import { simulateFinancial } from "./financial";
import { simulateOperational } from "./operational";
import { simulateRisk } from "./risk";

export async function simulateStrategic(
  userId: string,
  parameters: Record<string, any>
): Promise<Record<string, any>> {
  const goal = parameters.goal || "";
  const strategyType = (parameters.strategy_type || "BALANCED") as StrategyType;

  // Parse goal to determine what to simulate
  if (goal.toLowerCase().includes("glp") || goal.toLowerCase().includes("500")) {
    return simulateGLPExpansion(userId, parameters, strategyType);
  }

  if (goal.toLowerCase().includes("marketing") || goal.toLowerCase().includes("bookadoc")) {
    return simulateMarketingExpansion(userId, parameters, strategyType);
  }

  // Default strategic simulation
  return {
    goal,
    strategy_type: strategyType,
    timeline: { months: 6 },
    required_resources: {},
    projected_outcomes: {},
    risk_map: {},
    confidence_score: 0.5,
  };
}

async function simulateGLPExpansion(
  userId: string,
  parameters: Record<string, any>,
  strategyType: StrategyType
): Promise<Record<string, any>> {
  const targetPatients = parameters.target_patients || 500;
  const currentPatients = parameters.current_patients || 100;

  // Determine strategy parameters based on strategy type
  let growthRate: number;
  let marketingSpend: number;
  let timelineMonths: number;

  switch (strategyType) {
    case "CONSERVATIVE":
      growthRate = 0.05; // 5% monthly growth
      marketingSpend = 1000;
      timelineMonths = Math.ceil(Math.log(targetPatients / currentPatients) / Math.log(1 + growthRate));
      break;
    case "BALANCED":
      growthRate = 0.10; // 10% monthly growth
      marketingSpend = 2500;
      timelineMonths = Math.ceil(Math.log(targetPatients / currentPatients) / Math.log(1 + growthRate));
      break;
    case "AGGRESSIVE":
      growthRate = 0.15; // 15% monthly growth
      marketingSpend = 5000;
      timelineMonths = Math.ceil(Math.log(targetPatients / currentPatients) / Math.log(1 + growthRate));
      break;
    case "EXPANSION":
      growthRate = 0.20; // 20% monthly growth
      marketingSpend = 7500;
      timelineMonths = Math.ceil(Math.log(targetPatients / currentPatients) / Math.log(1 + growthRate));
      break;
    default:
      growthRate = 0.10;
      marketingSpend = 2500;
      timelineMonths = 18;
  }

  // Run clinical simulation for GLP growth
  const clinicalSim = await simulateClinical(userId, {
    scenario: "GLP_GROWTH",
    marketing_spend: marketingSpend,
    months: timelineMonths,
  });

  // Run financial simulation
  const financialSim = await simulateFinancial(userId, {
    scenario: "REVENUE_PROJECTION",
    time_horizon: "1YEAR",
  });

  // Run operational simulation
  const operationalSim = await simulateOperational(userId, {
    scenario: "MA_WORKLOAD",
    time_horizon: "6MONTHS",
  });

  // Run risk simulation
  const riskSim = await simulateRisk(userId, {
    risk_type: "OPERATIONAL",
    time_horizon: "6MONTHS",
  });

  // Calculate required resources
  const requiredResources = {
    marketing_budget: marketingSpend * timelineMonths,
    ma_staffing: operationalSim.predicted_hours_per_week > 40 ? 2 : 1,
    follow_up_capacity: clinicalSim.predicted_follow_ups_per_month || 0,
  };

  // Projected outcomes
  const projectedOutcomes = {
    patient_count: targetPatients,
    revenue: clinicalSim.predicted_revenue || 0,
    ma_workload: operationalSim.predicted_hours_per_week || 0,
    risk_level: riskSim.overall_severity || "LOW",
  };

  return {
    goal: `Grow GLP to ${targetPatients} patients`,
    strategy_type: strategyType,
    timeline: {
      months: timelineMonths,
      start_date: new Date().toISOString(),
      target_date: new Date(Date.now() + timelineMonths * 30 * 24 * 60 * 60 * 1000).toISOString(),
    },
    required_resources: requiredResources,
    projected_outcomes: projectedOutcomes,
    risk_map: {
      operational_risk: riskSim.overall_severity,
      clinical_risk: "LOW",
      financial_risk: "LOW",
    },
    financial_sensitivity: {
      marketing_spend_impact: marketingSpend / 1000, // Simplified
      patient_acquisition_cost: marketingSpend / (growthRate * currentPatients),
    },
    operational_constraints: {
      ma_capacity: operationalSim.predicted_hours_per_week || 0,
      scheduling_capacity: 40, // Default
    },
    recommended_path: {
      phase_1: "Increase marketing spend gradually",
      phase_2: "Monitor MA workload closely",
      phase_3: "Scale infrastructure as patient count grows",
    },
    confidence_score: 0.7,
  };
}

async function simulateMarketingExpansion(
  userId: string,
  parameters: Record<string, any>,
  strategyType: StrategyType
): Promise<Record<string, any>> {
  // Simplified marketing expansion simulation
  return {
    goal: "Expand marketing",
    strategy_type: strategyType,
    timeline: { months: 3 },
    required_resources: { marketing_budget: 10000 },
    projected_outcomes: { new_patients: 50 },
    risk_map: {},
    confidence_score: 0.6,
  };
}

