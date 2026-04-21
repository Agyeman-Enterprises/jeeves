import { supabaseServer } from "@/lib/supabase/server";
import type { FinancialPrediction, TimeHorizon } from "./types";

export async function simulateFinancial(
  userId: string,
  parameters: Record<string, any>
): Promise<Record<string, any>> {
  const scenario = parameters.scenario || "default";
  const timeHorizon = (parameters.time_horizon || "3MONTHS") as TimeHorizon;
  const entityId = parameters.entity_id;

  // Get historical financial data
  const { data: transactions } = await supabaseServer
    .from("nexus_financial_transactions")
    .select("*")
    .eq("user_id", userId)
    .order("occurred_at", { ascending: false })
    .limit(1000);

  if (entityId) {
    // Filter by entity
    const entityTransactions = (transactions as any[] || []).filter((t: any) => t.entity_id === entityId);
    return simulateEntityFinancials(userId, entityId, parameters, entityTransactions, timeHorizon);
  }

  // Aggregate across all entities
  return simulateAggregateFinancials(userId, parameters, transactions as any[] || [], timeHorizon);
}

async function simulateEntityFinancials(
  userId: string,
  entityId: string,
  parameters: Record<string, any>,
  transactions: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const months = getMonthsFromHorizon(timeHorizon);

  // Calculate historical averages
  const income = transactions.filter((t) => t.direction === "INCOME");
  const expenses = transactions.filter((t) => t.direction === "EXPENSE");

  const avgMonthlyIncome = income.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0) / Math.max(months, 1);
  const avgMonthlyExpenses = expenses.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0) / Math.max(months, 1);

  // Project forward
  const projectedIncome = avgMonthlyIncome * months;
  const projectedExpenses = avgMonthlyExpenses * months;
  const projectedProfit = projectedIncome - projectedExpenses;

  // Calculate cashflow
  const cashflow = projectedIncome - projectedExpenses;

  // Tax liability estimate (simplified)
  const taxRate = 0.25; // 25% effective rate (simplified)
  const projectedTax = projectedProfit * taxRate;

  return {
    scenario: "ENTITY_FINANCIALS",
    entity_id: entityId,
    time_horizon: timeHorizon,
    projected_income: projectedIncome,
    projected_expenses: projectedExpenses,
    projected_profit: projectedProfit,
    projected_cashflow: cashflow,
    projected_tax_liability: projectedTax,
    confidence_score: 0.7,
    assumptions: {
      avg_monthly_income: avgMonthlyIncome,
      avg_monthly_expenses: avgMonthlyExpenses,
      tax_rate: taxRate,
    },
  };
}

async function simulateAggregateFinancials(
  userId: string,
  parameters: Record<string, any>,
  transactions: any[],
  timeHorizon: TimeHorizon
): Promise<Record<string, any>> {
  const months = getMonthsFromHorizon(timeHorizon);

  // Get all entities
  const { data: entities } = await supabaseServer
    .from("nexus_financial_entities")
    .select("*")
    .eq("owner_user_id", userId);

  // Aggregate across entities
  let totalIncome = 0;
  let totalExpenses = 0;

  for (const entity of (entities as any[] || []) as any[]) {
    const entityTransactions = transactions.filter((t) => t.entity_id === entity.id);
    const income = entityTransactions.filter((t) => t.direction === "INCOME");
    const expenses = entityTransactions.filter((t) => t.direction === "EXPENSE");

    const avgMonthlyIncome = income.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0) / Math.max(months, 1);
    const avgMonthlyExpenses = expenses.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0) / Math.max(months, 1);

    totalIncome += avgMonthlyIncome * months;
    totalExpenses += avgMonthlyExpenses * months;
  }

  const totalProfit = totalIncome - totalExpenses;
  const totalTax = totalProfit * 0.25; // Simplified tax rate

  return {
    scenario: "AGGREGATE_FINANCIALS",
    time_horizon: timeHorizon,
    total_projected_income: totalIncome,
    total_projected_expenses: totalExpenses,
    total_projected_profit: totalProfit,
    total_projected_tax_liability: totalTax,
    entity_count: (entities || []).length,
    confidence_score: 0.65,
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

