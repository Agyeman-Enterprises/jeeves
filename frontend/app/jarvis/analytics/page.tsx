"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const JARVIS_URL = "/api/proxy";

type AgentStatus = {
  name: string;
  status: string;
  lastRun: string | null;
};

type SystemStatus = {
  services: Record<string, { name: string; port: number; healthy: boolean }>;
};

type KnowledgeStats = {
  total_documents?: number;
  total_chunks?: number;
};

export default function AnalyticsPage() {
  const [agents, setAgents]     = useState<AgentStatus[]>([]);
  const [system, setSystem]     = useState<SystemStatus | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [agR, sysR, kbR] = await Promise.allSettled([
          fetch(`${JARVIS_URL}/agents/status`).then((r) => r.json()),
          fetch(`${JARVIS_URL}/api/empire/status`).then((r) => r.json()),
          fetch(`${JARVIS_URL}/api/knowledge/stats`).then((r) => r.json()),
        ]);
        if (agR.status === "fulfilled") setAgents(agR.value);
        if (sysR.status === "fulfilled") setSystem(sysR.value);
        if (kbR.status === "fulfilled") setKnowledge(kbR.value);
      } finally {
        setLoading(false);
      }
    };
    load();
    const t = setInterval(load, 30_000);
    return () => clearInterval(t);
  }, []);

  const active  = agents.filter((a) => a.status === "active").length;
  const idle    = agents.filter((a) => a.status === "idle").length;
  const total   = agents.length;
  const healthyServices = system
    ? Object.values(system.services).filter((s) => s.healthy).length
    : 0;
  const totalServices = system ? Object.values(system.services).length : 0;

  return (
    <Shell>
      <div className="flex h-full gap-6">
        <div className="flex-1 min-w-0">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-white">Analytics</h1>
            <p className="text-sm text-slate-400 mt-0.5">System health and performance metrics</p>
          </div>

          {/* KPI row */}
          <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <KPICard label="Total Agents"    value={loading ? "—" : String(total)}       />
            <KPICard label="Active Now"      value={loading ? "—" : String(active)}      accent="emerald" />
            <KPICard label="Services OK"     value={loading ? "—" : `${healthyServices}/${totalServices}`} accent={healthyServices === totalServices ? "emerald" : "amber"} />
            <KPICard label="Docs Indexed"    value={loading ? "—" : String(knowledge?.total_documents ?? "—")} />
          </div>

          {/* Agent status breakdown */}
          <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900/50 p-5">
            <h2 className="mb-4 text-sm font-semibold text-white">Agent Utilization</h2>
            <div className="space-y-2">
              <BarRow label="Active"     count={active} total={total} color="bg-emerald-500" />
              <BarRow label="Idle"       count={idle}   total={total} color="bg-slate-600" />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {agents.slice(0, 12).map((a) => (
                <div key={a.name} className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                    a.status === "active" ? "bg-emerald-400 animate-pulse" : "bg-slate-600"
                  }`} />
                  <span className="truncate text-[11px] text-slate-400">
                    {a.name.replace("Agent", "").trim()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Service health */}
          {system && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-5">
              <h2 className="mb-4 text-sm font-semibold text-white">Service Health</h2>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {Object.values(system.services).map((svc) => (
                  <div
                    key={svc.name}
                    className={`flex items-center justify-between rounded-md border p-3 ${
                      svc.healthy
                        ? "border-emerald-500/20 bg-emerald-500/5"
                        : "border-red-500/20 bg-red-500/5"
                    }`}
                  >
                    <div>
                      <p className="text-xs font-medium text-white">{svc.name}</p>
                      <p className="text-[10px] text-slate-500">:{svc.port}</p>
                    </div>
                    <span className={`text-[10px] font-semibold uppercase ${
                      svc.healthy ? "text-emerald-400" : "text-red-400"
                    }`}>
                      {svc.healthy ? "UP" : "DOWN"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="w-64 shrink-0 space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Quick Stats
            </h3>
            <div className="space-y-2.5">
              <StatRow label="Agent count"     value={String(total)} />
              <StatRow label="Active"          value={String(active)} />
              <StatRow label="Idle"            value={String(idle)} />
              <StatRow label="Docs indexed"    value={String(knowledge?.total_documents ?? "—")} />
              <StatRow label="Knowledge chunks" value={String(knowledge?.total_chunks ?? "—")} />
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Legend
            </h3>
            <div className="space-y-1.5 text-[11px] text-slate-500">
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Active / healthy</div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-amber-400" /> Warning</div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-red-500" /> Error / down</div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-slate-600" /> Idle / standby</div>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}

function KPICard({ label, value, accent }: { label: string; value: string; accent?: "emerald" | "amber" }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${
        accent === "emerald" ? "text-emerald-400"
        : accent === "amber" ? "text-amber-400"
        : "text-white"
      }`}>
        {value}
      </p>
    </div>
  );
}

function BarRow({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-16 text-xs text-slate-500 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-slate-800">
        <div className={`h-1.5 rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-xs text-slate-500">{count}</span>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs font-medium text-white">{value}</span>
    </div>
  );
}
