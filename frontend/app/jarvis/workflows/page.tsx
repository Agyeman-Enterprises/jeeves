"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const JARVIS_URL = "/api/proxy";

type Job = {
  id: string;
  title?: string;
  description?: string;
  status: "pending" | "running" | "completed" | "failed";
  agent?: string;
  created_at?: string;
  updated_at?: string;
  progress?: number;
};

const STATUS_CFG = {
  pending:   { dot: "bg-slate-500",                  text: "text-slate-400",   label: "PENDING" },
  running:   { dot: "bg-amber-400 animate-pulse",    text: "text-amber-400",   label: "RUNNING" },
  completed: { dot: "bg-emerald-400",                text: "text-emerald-400", label: "DONE" },
  failed:    { dot: "bg-red-500",                    text: "text-red-400",     label: "FAILED" },
};

const PIPELINE_NODES = [
  { label: "Akua",    sub: "Initiates request",   color: "border-slate-600 text-slate-300" },
  { label: "JARVIS",  sub: "Plans & routes",       color: "border-emerald-600 text-emerald-300" },
  { label: "NEXUS",   sub: "Orchestrates agents",  color: "border-blue-600 text-blue-300" },
  { label: "Agents",  sub: "Domain specialists",   color: "border-purple-600 text-purple-300" },
  { label: "GHEXIT",  sub: "Delivers output",      color: "border-teal-600 text-teal-300" },
];

export default function WorkflowsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`${JARVIS_URL}/api/jobs`);
        if (r.ok) {
          const data = await r.json();
          setJobs(Array.isArray(data) ? data : data.jobs ?? []);
        }
      } catch {
        // offline
      } finally {
        setLoading(false);
      }
    };
    load();
    const t = setInterval(load, 8_000);
    return () => clearInterval(t);
  }, []);

  const running   = jobs.filter((j) => j.status === "running");
  const pending   = jobs.filter((j) => j.status === "pending");
  const completed = jobs.filter((j) => j.status === "completed").slice(0, 5);

  return (
    <Shell>
      <div className="flex h-full gap-6">
        <div className="flex-1 min-w-0">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-white">Workflows</h1>
            <p className="text-sm text-slate-400 mt-0.5">
              {running.length} running · {pending.length} pending · {completed.length} recently completed
            </p>
          </div>

          {/* Pipeline visualization */}
          <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900/50 p-5">
            <h2 className="mb-4 text-sm font-semibold text-white">Execution Pipeline</h2>
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {PIPELINE_NODES.map((node, i) => (
                <div key={node.label} className="flex items-center gap-2 shrink-0">
                  <div className={`rounded-lg border px-4 py-3 text-center min-w-[90px] ${node.color}`}>
                    <p className="text-sm font-semibold">{node.label}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{node.sub}</p>
                  </div>
                  {i < PIPELINE_NODES.length - 1 && (
                    <span className="text-slate-600 text-lg shrink-0">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Active jobs */}
          {running.length > 0 && (
            <div className="mb-5">
              <h2 className="mb-3 text-sm font-semibold text-amber-400">Running</h2>
              <div className="space-y-2">
                {running.map((job) => <JobCard key={job.id} job={job} />)}
              </div>
            </div>
          )}

          {/* Pending */}
          {pending.length > 0 && (
            <div className="mb-5">
              <h2 className="mb-3 text-sm font-semibold text-slate-400">Pending</h2>
              <div className="space-y-2">
                {pending.map((job) => <JobCard key={job.id} job={job} />)}
              </div>
            </div>
          )}

          {/* Completed */}
          {completed.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold text-emerald-400">Recently Completed</h2>
              <div className="space-y-2">
                {completed.map((job) => <JobCard key={job.id} job={job} />)}
              </div>
            </div>
          )}

          {!loading && jobs.length === 0 && (
            <div className="flex h-40 items-center justify-center text-sm text-slate-500">
              No active workflows — submit a task from the Console to get started
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="w-64 shrink-0 space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">Summary</h3>
            <div className="space-y-2">
              <StatRow label="Running"   value={String(running.length)}   accent="amber" />
              <StatRow label="Pending"   value={String(pending.length)} />
              <StatRow label="Completed" value={String(completed.length)} accent="emerald" />
              <StatRow label="Total"     value={String(jobs.length)} />
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Architecture Rule
            </h3>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Agents never bypass NEXUS. Every workflow routes through the orchestration layer before reaching domain specialists.
            </p>
          </div>
        </div>
      </div>
    </Shell>
  );
}

function JobCard({ job }: { job: Job }) {
  const cfg = STATUS_CFG[job.status] ?? STATUS_CFG.pending;
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
      <div className="flex items-start justify-between mb-1">
        <p className="text-sm font-medium text-white">
          {job.title ?? job.description ?? `Job ${job.id.slice(0, 8)}`}
        </p>
        <span className={`flex items-center gap-1.5 text-[10px] font-semibold uppercase ${cfg.text}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
          {cfg.label}
        </span>
      </div>
      {job.agent && (
        <p className="text-[11px] text-slate-500">Agent: {job.agent}</p>
      )}
      {job.progress !== undefined && job.progress > 0 && (
        <div className="mt-2 h-1 rounded-full bg-slate-800">
          <div
            className="h-1 rounded-full bg-amber-400 transition-all"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      )}
    </div>
  );
}

function StatRow({ label, value, accent }: { label: string; value: string; accent?: "emerald" | "amber" }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-500">{label}</span>
      <span className={`text-xs font-medium ${
        accent === "emerald" ? "text-emerald-400"
        : accent === "amber" ? "text-amber-400"
        : "text-white"
      }`}>{value}</span>
    </div>
  );
}
