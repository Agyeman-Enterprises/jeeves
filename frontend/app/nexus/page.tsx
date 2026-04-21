"use client";

import React, { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";
import { getPortfolioOverview, getRiskHeatmap, type PortfolioOverview, type RiskHeatmap } from "@/lib/api/nexusClient";

const NEXUS_URL = process.env.NEXT_PUBLIC_NEXUS_URL ?? "http://localhost:3001";

function StatCard({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

function fmt(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

function healthColor(score: number) {
  if (score >= 70) return "text-emerald-400";
  if (score >= 40) return "text-amber-400";
  return "text-red-400";
}

export default function NexusPage() {
  const [portfolio, setPortfolio] = useState<PortfolioOverview | null>(null);
  const [risk, setRisk] = useState<RiskHeatmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getPortfolioOverview(), getRiskHeatmap()])
      .then(([p, r]) => {
        setPortfolio(p);
        setRisk(r);
        if (!p) setError("Could not reach JARVIS backend. Make sure it is running on port 8001.");
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  function refresh() {
    setLoading(true);
    setError(null);
    Promise.all([getPortfolioOverview(), getRiskHeatmap()])
      .then(([p, r]) => { setPortfolio(p); setRisk(r); })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }

  return (
    <Shell>
      <div className="p-6 space-y-6 text-slate-200">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">NEXUS — Portfolio Intelligence</h1>
            <p className="mt-1 text-slate-400 text-sm">
              Live data from JARVIS backend &middot; {portfolio?.as_of ? new Date(portfolio.as_of).toLocaleString() : "—"}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={refresh}
              disabled={loading}
              className="rounded-md bg-slate-700 px-3 py-1.5 text-xs font-medium hover:bg-slate-600 disabled:opacity-40 transition-colors"
            >
              {loading ? "Loading…" : "Refresh"}
            </button>
            <a
              href={NEXUS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-medium hover:bg-emerald-600 transition-colors"
            >
              Open NEXUS ↗
            </a>
          </div>
        </header>

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="grid gap-4 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl border border-slate-700 bg-slate-800/50" />
            ))}
          </div>
        )}

        {/* Stats */}
        {!loading && portfolio && (
          <>
            <section className="grid gap-4 md:grid-cols-4">
              <StatCard
                label="Total Entities"
                value={portfolio.total_businesses}
                sub={`${portfolio.active_businesses} active`}
              />
              <StatCard
                label="Revenue MTD"
                value={fmt(portfolio.revenue_trends?.total_revenue ?? 0)}
                sub={portfolio.revenue_trends?.growth_rate != null
                  ? `${portfolio.revenue_trends.growth_rate >= 0 ? "+" : ""}${portfolio.revenue_trends.growth_rate.toFixed(1)}% MoM`
                  : undefined}
              />
              <StatCard
                label="Alert Level"
                value={
                  <span className={
                    (risk?.summary.high_risk ?? 0) > 0 ? "text-red-400"
                    : (risk?.summary.medium_risk ?? 0) > 0 ? "text-amber-400"
                    : "text-emerald-400"
                  }>
                    {(risk?.summary.high_risk ?? 0) > 0 ? "Critical"
                      : (risk?.summary.medium_risk ?? 0) > 0 ? "Attention"
                      : "Healthy"}
                  </span>
                }
                sub={risk ? `${risk.summary.low_risk} healthy · ${risk.summary.medium_risk} attention · ${risk.summary.high_risk} critical` : undefined}
              />
              <StatCard
                label="High-Risk Entities"
                value={
                  <span className={(portfolio.high_risk_businesses?.length ?? 0) > 0 ? "text-red-400" : "text-emerald-400"}>
                    {portfolio.high_risk_businesses?.length ?? 0}
                  </span>
                }
                sub="Negative margin or low cash"
              />
            </section>

            {/* Top Performers */}
            {portfolio.top_performers && portfolio.top_performers.length > 0 && (
              <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
                <div className="text-xs uppercase tracking-wide text-slate-400 mb-3">Top Performers</div>
                <div className="space-y-2">
                  {portfolio.top_performers.map((b) => (
                    <div key={b.id} className="flex items-center justify-between text-sm">
                      <span className="text-slate-200">{b.name}</span>
                      <span className="text-emerald-400 font-mono">{fmt(b.revenue_mtd)} MTD</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Entity Grid */}
            {portfolio.businesses && portfolio.businesses.length > 0 && (
              <section>
                <div className="text-xs uppercase tracking-wide text-slate-400 mb-3">All Entities</div>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {portfolio.businesses.map((b) => {
                    const margin = b.metrics?.profit_margin ?? 0;
                    return (
                      <div key={b.id} className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm truncate">{b.name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            b.status === "active" ? "bg-emerald-900/50 text-emerald-300" : "bg-slate-800 text-slate-400"
                          }`}>{b.status}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <div className="text-slate-500">Revenue MTD</div>
                            <div className="font-mono text-slate-200">{fmt(b.metrics?.revenue_mtd ?? 0)}</div>
                          </div>
                          <div>
                            <div className="text-slate-500">Cash</div>
                            <div className="font-mono text-slate-200">{fmt(b.metrics?.cash_balance ?? 0)}</div>
                          </div>
                          <div>
                            <div className="text-slate-500">Margin</div>
                            <div className={`font-mono ${margin < 0 ? "text-red-400" : margin < 10 ? "text-amber-400" : "text-emerald-400"}`}>
                              {margin.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* High-risk alert */}
            {portfolio.high_risk_businesses && portfolio.high_risk_businesses.length > 0 && (
              <section className="rounded-xl border border-red-800/50 bg-red-950/30 p-4">
                <div className="text-xs uppercase tracking-wide text-red-400 mb-3">Needs Attention</div>
                <div className="space-y-1">
                  {portfolio.high_risk_businesses.map((b) => (
                    <div key={b.id} className="flex items-center gap-2 text-sm">
                      <span className="text-red-400">⚠</span>
                      <span className="text-slate-200">{b.name}</span>
                      <span className="text-slate-500 text-xs">{b.reason.replace(/_/g, " ")}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Empty state */}
            {portfolio.businesses?.length === 0 && (
              <div className="rounded-xl border border-slate-700 bg-slate-900/40 p-8 text-center text-slate-400">
                No entities found in JarvisCore database.{" "}
                <a href={`${NEXUS_URL}/database/seed`} className="text-emerald-400 underline" target="_blank" rel="noopener noreferrer">
                  Seed NEXUS data ↗
                </a>
              </div>
            )}
          </>
        )}
      </div>
    </Shell>
  );
}
