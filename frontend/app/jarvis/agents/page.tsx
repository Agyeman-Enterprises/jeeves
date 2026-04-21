"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const JARVIS_URL = "/api/proxy";

type Agent = {
  name: string;
  role: string;
  status: "idle" | "active" | "error" | "processing";
  lastRun: string | null;
  lastTask: string | null;
};

type Stats = {
  active: number;
  idle: number;
  total: number;
};

const STATUS_CONFIG = {
  active:     { dot: "bg-emerald-400 animate-pulse", text: "text-emerald-400", label: "ACTIVE" },
  idle:       { dot: "bg-slate-500",                  text: "text-slate-500",   label: "IDLE" },
  processing: { dot: "bg-amber-400 animate-pulse",    text: "text-amber-400",   label: "PROCESSING" },
  error:      { dot: "bg-red-500",                    text: "text-red-400",     label: "ERROR" },
};

// Map agent names to domain tags
function getDomain(name: string): string {
  if (name.includes("Health") || name.includes("Medical") || name.includes("Wellness") || name.includes("WhoZon")) return "Healthcare";
  if (name.includes("Finance") || name.includes("Sales") || name.includes("Business")) return "Finance";
  if (name.includes("Marketing") || name.includes("Social") || name.includes("SEO") || name.includes("AdAI") || name.includes("Copywriter")) return "Marketing";
  if (name.includes("Email") || name.includes("Calendar") || name.includes("Task") || name.includes("Communications")) return "Comms";
  if (name.includes("Vision") || name.includes("Browser") || name.includes("System") || name.includes("File")) return "System";
  if (name.includes("Content") || name.includes("Personal") || name.includes("Coach")) return "Creative";
  if (name.includes("Nexus") || name.includes("Supervisor") || name.includes("Proactive") || name.includes("Data")) return "Intelligence";
  return "General";
}

const DOMAIN_COLORS: Record<string, string> = {
  Healthcare:   "bg-teal-500/10 text-teal-400 border-teal-500/20",
  Finance:      "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  Marketing:    "bg-purple-500/10 text-purple-400 border-purple-500/20",
  Comms:        "bg-blue-500/10 text-blue-400 border-blue-500/20",
  System:       "bg-slate-500/10 text-slate-400 border-slate-500/20",
  Creative:     "bg-pink-500/10 text-pink-400 border-pink-500/20",
  Intelligence: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  General:      "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [filter, setFilter] = useState<string>("All");
  const [loading, setLoading] = useState(true);

  const fetchAgents = async () => {
    try {
      const r = await fetch(`${JARVIS_URL}/agents/status`);
      if (r.ok) setAgents(await r.json());
    } catch {
      // backend offline — show empty state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 10_000);
    return () => clearInterval(interval);
  }, []);

  const domains = ["All", ...Array.from(new Set(agents.map((a) => getDomain(a.name))))].sort();
  const filtered = filter === "All" ? agents : agents.filter((a) => getDomain(a.name) === filter);

  const stats: Stats = {
    active: agents.filter((a) => a.status === "active" || a.status === "processing").length,
    idle:   agents.filter((a) => a.status === "idle").length,
    total:  agents.length,
  };

  return (
    <Shell>
      <div className="flex h-full gap-6">
        {/* Main panel */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-white">Agents</h1>
              <p className="text-sm text-slate-400 mt-0.5">
                {stats.total} agents · {stats.active} active · {stats.idle} idle
              </p>
            </div>
            <button
              onClick={fetchAgents}
              className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:border-emerald-500/40 hover:text-emerald-400 transition-colors"
            >
              Refresh
            </button>
          </div>

          {/* Domain filter */}
          <div className="mb-5 flex flex-wrap gap-2">
            {domains.map((d) => (
              <button
                key={d}
                onClick={() => setFilter(d)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  filter === d
                    ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400"
                    : "border-slate-700 text-slate-500 hover:border-slate-600 hover:text-slate-300"
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          {/* Agent grid */}
          {loading ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 9 }).map((_, i) => (
                <div key={i} className="h-32 animate-pulse rounded-lg bg-slate-800/50" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-sm text-slate-500">
              No agents found
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((agent) => {
                const cfg = STATUS_CONFIG[agent.status] ?? STATUS_CONFIG.idle;
                const domain = getDomain(agent.name);
                const domainCls = DOMAIN_COLORS[domain] ?? DOMAIN_COLORS.General;
                return (
                  <div
                    key={agent.name}
                    className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-white leading-tight">
                        {agent.name.replace("Agent", "").trim()}
                      </span>
                      <span className={`inline-flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider ${cfg.text}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
                        {cfg.label}
                      </span>
                    </div>
                    <span className={`mb-3 inline-block rounded border px-1.5 py-0.5 text-[10px] font-medium ${domainCls}`}>
                      {domain}
                    </span>
                    <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                      {agent.role}
                    </p>
                    {agent.lastTask && (
                      <p className="mt-2 text-[10px] text-slate-600 truncate">
                        Last: {agent.lastTask}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right context panel */}
        <div className="w-64 shrink-0 flex flex-col gap-4">
          {/* System metrics */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              System Health
            </h3>
            <div className="space-y-3">
              <Metric label="Total Agents"  value={String(stats.total)} />
              <Metric label="Active"        value={String(stats.active)} accent="emerald" />
              <Metric label="Idle"          value={String(stats.idle)} />
            </div>
          </div>

          {/* Domain breakdown */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Domains
            </h3>
            <div className="space-y-1.5">
              {Array.from(new Set(agents.map((a) => getDomain(a.name))))
                .sort()
                .map((d) => {
                  const count = agents.filter((a) => getDomain(a.name) === d).length;
                  return (
                    <button
                      key={d}
                      onClick={() => setFilter(d)}
                      className="flex w-full items-center justify-between rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-800 transition-colors"
                    >
                      <span>{d}</span>
                      <span className="text-slate-600">{count}</span>
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Architecture note */}
          <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-600">
              Flow
            </h3>
            <div className="space-y-1 text-[11px] text-slate-600">
              {["Akua", "JARVIS", "NEXUS", "Agents", "GHEXIT"].map((n, i, arr) => (
                <div key={n}>
                  <span className={i === 2 ? "text-emerald-600" : ""}>{n}</span>
                  {i < arr.length - 1 && <div className="ml-2 text-slate-700">↓</div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}

function Metric({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-500">{label}</span>
      <span className={`text-sm font-semibold ${accent === "emerald" ? "text-emerald-400" : "text-white"}`}>
        {value}
      </span>
    </div>
  );
}
