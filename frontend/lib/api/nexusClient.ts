// Nexus API client — routes through Next.js proxy to avoid CORS
const BACKEND = "/api/proxy";

export interface PortfolioTotals {
  total_businesses: number;
  active_businesses: number;
  total_companies: number;
  revenue_trends: {
    total_revenue: number;
    total_expenses: number;
    growth_rate: number;
  };
}

export interface PortfolioBusiness {
  id: string;
  name: string;
  slug: string;
  status: string;
  metrics: {
    revenue_mtd: number;
    expenses_mtd: number;
    profit_margin: number;
    cash_balance: number;
  };
}

export interface PortfolioOverview {
  total_businesses: number;
  active_businesses: number;
  total_companies: number;
  businesses: PortfolioBusiness[];
  top_performers: Array<{ id: string; name: string; revenue_mtd: number; performance_score: number }>;
  high_risk_businesses: Array<{ id: string; name: string; reason: string }>;
  revenue_trends: { total_revenue: number; total_expenses: number; growth_rate: number };
  summary: string;
  as_of: string;
}

export interface RiskHeatmap {
  entities: Array<{ id: string; name: string; risk_score: number; status: string }>;
  summary: { low_risk: number; medium_risk: number; high_risk: number };
}

export async function getPortfolioOverview(): Promise<PortfolioOverview | null> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/portfolio/overview`);
    if (!res.ok) throw new Error(`Portfolio API error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("[nexusClient] getPortfolioOverview failed:", err);
    return null;
  }
}

export async function getRiskHeatmap(): Promise<RiskHeatmap | null> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/portfolio/risk-heatmap`);
    if (!res.ok) throw new Error(`Risk heatmap API error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("[nexusClient] getRiskHeatmap failed:", err);
    return null;
  }
}

export async function getAlerts(): Promise<any[]> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/portfolio/alerts`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : data.alerts ?? [];
  } catch {
    return [];
  }
}
