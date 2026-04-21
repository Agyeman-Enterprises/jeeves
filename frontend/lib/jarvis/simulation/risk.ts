import { supabaseServer } from "@/lib/supabase/server";
import type { RiskPrediction, RiskType, RiskLevel, TimeHorizon } from "./types";

export async function simulateRisk(
  userId: string,
  parameters: Record<string, any>
): Promise<Record<string, any>> {
  const riskType = (parameters.risk_type || "OPERATIONAL") as RiskType;
  const timeHorizon = (parameters.time_horizon || "3MONTHS") as TimeHorizon;

  // Get relevant data for risk assessment
  const { data: clinicalEvents } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(500);

  const { data: financialTransactions } = await supabaseServer
    .from("nexus_financial_transactions")
    .select("*")
    .eq("user_id", userId)
    .order("occurred_at", { ascending: false })
    .limit(500);

  switch (riskType) {
    case "CLINICAL":
      return assessClinicalRisk(userId, parameters, clinicalEvents || [], timeHorizon);
    case "FINANCIAL":
      return assessFinancialRisk(userId, parameters, financialTransactions || [], timeHorizon);
    case "OPERATIONAL":
      return assessOperationalRisk(userId, parameters, clinicalEvents || [], timeHorizon);
    case "COMPLIANCE":
      return assessComplianceRisk(userId, parameters, timeHorizon);
    default:
      return {
        risk_type: riskType,
        risks: [],
        overall_severity: "LOW" as RiskLevel,
        confidence_score: 0.5,
      };
  }
}

async function assessClinicalRisk(
  userId: string,
  parameters: Record<string, any>,
  events: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const risks: any[] = [];

  // Check for hospitalization events
  const hospitalizations = events.filter((e) => e.event_type === "PATIENT_HOSPITALIZED");
  if (hospitalizations.length > 0) {
    risks.push({
      risk_category: "Hospitalization Risk",
      severity: "MEDIUM" as RiskLevel,
      probability: 0.3,
      impact: { description: "Recent hospitalizations indicate elevated risk" },
      mitigation_strategies: ["Increase follow-up frequency", "Monitor high-risk patients closely"],
    });
  }

  // Check for critical lab results
  const criticalLabs = events.filter((e) => e.event_type === "CRITICAL_LAB_RESULT");
  if (criticalLabs.length > 0) {
    risks.push({
      risk_category: "Critical Lab Results",
      severity: "HIGH" as RiskLevel,
      probability: 0.4,
      impact: { description: "Unaddressed critical lab results pose patient safety risk" },
      mitigation_strategies: ["Immediate review of all critical labs", "Establish rapid response protocol"],
    });
  }

  const overallSeverity = risks.length > 0 ? (risks[0].severity as RiskLevel) : ("LOW" as RiskLevel);

  return {
    risk_type: "CLINICAL",
    time_horizon: timeHorizon,
    risks,
    overall_severity: overallSeverity,
    confidence_score: 0.7,
  };
}

async function assessFinancialRisk(
  userId: string,
  parameters: Record<string, any>,
  transactions: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const risks: any[] = [];

  // Calculate cashflow
  const income = transactions.filter((t) => t.direction === "INCOME");
  const expenses = transactions.filter((t) => t.direction === "EXPENSE");

  const totalIncome = income.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
  const totalExpenses = expenses.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
  const netCashflow = totalIncome - totalExpenses;

  // Check for negative cashflow
  if (netCashflow < 0) {
    risks.push({
      risk_category: "Negative Cashflow",
      severity: "HIGH" as RiskLevel,
      probability: 0.8,
      impact: { amount: Math.abs(netCashflow), description: "Expenses exceed income" },
      mitigation_strategies: ["Reduce expenses", "Increase revenue", "Secure financing"],
    });
  }

  // Check for tax underpayment risk
  const months = getMonthsFromHorizon(timeHorizon);
  const estimatedTax = (totalIncome - totalExpenses) * 0.25; // Simplified
  if (estimatedTax > 10000 && months >= 3) {
    risks.push({
      risk_category: "Tax Underpayment Risk",
      severity: "MEDIUM" as RiskLevel,
      probability: 0.5,
      impact: { estimated_tax: estimatedTax, description: "Potential underpayment penalties" },
      mitigation_strategies: ["Make quarterly estimated tax payments", "Review tax strategy"],
    });
  }

  const overallSeverity = risks.length > 0 ? (risks[0].severity as RiskLevel) : ("LOW" as RiskLevel);

  return {
    risk_type: "FINANCIAL",
    time_horizon: timeHorizon,
    risks,
    overall_severity: overallSeverity,
    confidence_score: 0.65,
  };
}

async function assessOperationalRisk(
  userId: string,
  parameters: Record<string, any>,
  events: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const risks: any[] = [];

  // Check for no-show rate
  const appointments = events.filter((e) => e.event_type === "APPOINTMENT_BOOKED");
  const noShows = events.filter((e) => e.event_type === "NO_SHOW");
  const noShowRate = appointments.length > 0 ? noShows.length / appointments.length : 0;

  if (noShowRate > 0.2) {
    const revenueLoss = appointments.length * 0.2 * (parameters.avg_appointment_value || 200);
    risks.push({
      risk_category: "High No-Show Rate",
      severity: "MEDIUM" as RiskLevel,
      probability: noShowRate,
      impact: { no_show_rate: noShowRate, estimated_revenue_loss: revenueLoss },
      mitigation_strategies: ["Implement reminder system", "Charge no-show fees", "Overbook strategically"],
    });
  }

  const overallSeverity = risks.length > 0 ? (risks[0].severity as RiskLevel) : ("LOW" as RiskLevel);

  return {
    risk_type: "OPERATIONAL",
    time_horizon: timeHorizon,
    risks,
    overall_severity: overallSeverity,
    confidence_score: 0.6,
  };
}

async function assessComplianceRisk(
  userId: string,
  parameters: Record<string, any>,
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  // Simplified compliance risk assessment
  return {
    risk_type: "COMPLIANCE",
    time_horizon: timeHorizon,
    risks: [],
    overall_severity: "LOW" as RiskLevel,
    confidence_score: 0.5,
  };
}

function getMonthsFromHorizon(horizon: TimeHorizon): number {
  switch (horizon) {
    case "1WEEK":
      return 0.25;
    case "1MONTH":
      return 1;
    case "3MONTHS":
      return 3;
    case "6MONTHS":
      return 6;
    case "1YEAR":
      return 12;
    default:
      return 3;
  }
}

