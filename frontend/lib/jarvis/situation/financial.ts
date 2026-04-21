import { supabaseServer } from "@/lib/supabase/server";
import type { SituationRoomSnapshot, SituationRoomAlert, SituationRoomRecommendation } from "./types";
import { simulateFinancial } from "../simulation/financial";

export async function generateFinancialSituationRoom(
  userId: string
): Promise<SituationRoomSnapshot> {
  // A. Live Entity Status
  const { data: entities } = await supabaseServer
    .from("nexus_financial_entities")
    .select("*")
    .eq("owner_user_id", userId);

  const { data: transactions } = await supabaseServer
    .from("nexus_financial_transactions")
    .select("*")
    .eq("user_id", userId)
    .gte("occurred_at", new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())
    .order("occurred_at", { ascending: false });

  // Calculate revenue today/this week
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const revenueToday = (transactions || [])
    .filter((t) => t.direction === "INCOME" && new Date(t.occurred_at) >= today)
    .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);

  const revenueThisWeek = (transactions || [])
    .filter((t) => t.direction === "INCOME" && new Date(t.occurred_at) >= weekAgo)
    .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);

  // B. Trend Analysis
  const financialSim = await simulateFinancial(userId, {
    scenario: "AGGREGATE_FINANCIALS",
    time_horizon: "3MONTHS",
  });

  // C. Tax Risk Panel
  const { data: taxPositions } = await supabaseServer
    .from("nexus_tax_positions")
    .select("*")
    .eq("user_id", userId)
    .order("tax_year", { ascending: false })
    .limit(5);

  // D. Anomaly Detection
  const anomalies: any[] = [];
  const avgTransactionAmount = (transactions || []).reduce((sum, t) => sum + Math.abs(parseFloat(t.amount || 0)), 0) / Math.max((transactions || []).length, 1);
  const largeTransactions = (transactions || []).filter(
    (t) => Math.abs(parseFloat(t.amount || 0)) > avgTransactionAmount * 3
  );

  if (largeTransactions.length > 0) {
    anomalies.push({
      type: "UNUSUAL_TRANSACTION",
      count: largeTransactions.length,
      description: "Unusually large transactions detected",
    });
  }

  // Generate alerts
  const alerts: SituationRoomAlert[] = [];

  // Check cashflow risk
  const totalIncome = (transactions || []).filter((t) => t.direction === "INCOME").reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
  const totalExpenses = (transactions || []).filter((t) => t.direction === "EXPENSE").reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
  const netCashflow = totalIncome - totalExpenses;

  if (netCashflow < 0) {
    alerts.push({
      user_id: userId,
      room_type: "FINANCIAL",
      alert_type: "RISK",
      severity: "HIGH",
      title: "Negative Cashflow Detected",
      description: `Expenses exceed income by $${Math.abs(netCashflow).toFixed(2)} this month`,
      recommended_actions: {
        actions: ["Review expenses", "Increase revenue", "Consider financing"],
      },
    });
  }

  // Generate recommendations
  const recommendations: SituationRoomRecommendation[] = [];

  if (financialSim.total_projected_profit && financialSim.total_projected_profit > 0) {
    recommendations.push({
      user_id: userId,
      room_type: "FINANCIAL",
      recommendation_type: "OPPORTUNITY",
      title: "Revenue Trending Above Forecast",
      description: `Projected profit is $${financialSim.total_projected_profit.toFixed(2)} over next 3 months`,
      priority: 2,
    });
  }

  // Create snapshot
  const snapshot: SituationRoomSnapshot = {
    user_id: userId,
    room_type: "FINANCIAL",
    snapshot_data: {
      live_entity_status: {
        entity_count: (entities || []).length,
        revenue_today: revenueToday,
        revenue_this_week: revenueThisWeek,
        projected_revenue_3months: financialSim.total_projected_income || 0,
        cashflow: netCashflow,
        tax_exposure: (taxPositions || []).reduce((sum, t) => sum + (parseFloat(t.estimated_tax || 0) - parseFloat(t.paid_tax || 0)), 0),
      },
      trend_analysis: {
        burn_rate: financialSim.total_projected_expenses || 0,
        revenue_trend: "STABLE", // Simplified
        profit_centers: [],
        loss_centers: [],
      },
      tax_risk: {
        underpayment_probability: 0.3, // Simplified
        estimated_quarterly_payments: (taxPositions || []).reduce((sum, t) => sum + parseFloat(t.estimated_tax || 0), 0),
        multi_entity_recommendations: [],
      },
      anomalies,
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

