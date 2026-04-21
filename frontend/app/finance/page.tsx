"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";
import JarvisConsole from "@/components/jarvis/JarvisConsole";

type PortfolioApp = {
  name: string;
  status: string;
  mrr?: number;
  arr?: number;
  users?: number;
};

type PortfolioData = {
  total_apps?: number;
  total_mrr?: number;
  total_arr?: number;
  apps?: PortfolioApp[];
  portfolio_health?: number;
};

export default function FinancePage() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/proxy/api/empire/portfolio")
      .then((r) => r.json())
      .then((d) => setPortfolio(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const apps = portfolio?.apps ?? [];
  const totalMrr = portfolio?.total_mrr ?? 0;
  const health = portfolio?.portfolio_health ?? 0;

  return (
    <Shell>
      <div className="flex h-full gap-4 p-4 min-h-0">
        {/* Left: data panel */}
        <div className="w-80 shrink-0 flex flex-col gap-3 overflow-y-auto">
          <div>
            <h2 className="text-sm font-semibold text-white mb-0.5">Money & Metrics</h2>
            <p className="text-xs text-slate-400">Financial view across all entities</p>
          </div>

          {/* KPIs */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
              <p className="text-xs text-slate-400">MRR</p>
              <p className="text-lg font-bold text-emerald-400">
                {loading ? "—" : `$${totalMrr.toLocaleString()}`}
              </p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
              <p className="text-xs text-slate-400">Portfolio Health</p>
              <p className={`text-lg font-bold ${health >= 70 ? "text-emerald-400" : health >= 40 ? "text-amber-400" : "text-red-400"}`}>
                {loading ? "—" : `${Math.round(health)}%`}
              </p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
              <p className="text-xs text-slate-400">ARR</p>
              <p className="text-lg font-bold text-blue-400">
                {loading ? "—" : `$${((portfolio?.total_arr ?? totalMrr * 12)).toLocaleString()}`}
              </p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
              <p className="text-xs text-slate-400">Apps</p>
              <p className="text-lg font-bold text-slate-200">
                {loading ? "—" : portfolio?.total_apps ?? apps.length}
              </p>
            </div>
          </div>

          {/* App list */}
          <div className="rounded-lg border border-slate-800 bg-slate-900 overflow-hidden">
            <div className="px-3 py-2 border-b border-slate-800">
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-widest">Apps</p>
            </div>
            {loading ? (
              <div className="p-3 text-xs text-slate-500">Loading portfolio…</div>
            ) : apps.length === 0 ? (
              <div className="p-3 text-xs text-slate-500">No portfolio data yet — ask JARVIS to pull it.</div>
            ) : (
              <div className="divide-y divide-slate-800">
                {apps.map((app, i) => (
                  <div key={i} className="flex items-center justify-between px-3 py-2">
                    <div>
                      <p className="text-xs font-medium text-slate-200">{app.name}</p>
                      <p className={`text-xs ${app.status === "live" || app.status === "LIVE" ? "text-emerald-400" : "text-slate-500"}`}>
                        {app.status}
                      </p>
                    </div>
                    {app.mrr !== undefined && (
                      <p className="text-xs text-emerald-400 font-mono">${app.mrr.toLocaleString()}/mo</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick prompts */}
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p className="text-xs font-semibold text-slate-400 mb-2">Quick questions</p>
            <div className="space-y-1 text-xs text-slate-400">
              <p>→ "Which apps are making money?"</p>
              <p>→ "What's my burn rate?"</p>
              <p>→ "Which apps need attention?"</p>
              <p>→ "Pull the latest Stripe data"</p>
            </div>
          </div>
        </div>

        {/* Right: JARVIS chat */}
        <div className="flex-1 min-w-0 flex flex-col">
          <JarvisConsole
            label="Money & Metrics Console"
            initialMessage="Financial command center active. I have your portfolio data loaded. Ask me anything about revenue, burn, or which apps need attention."
          />
        </div>
      </div>
    </Shell>
  );
}
