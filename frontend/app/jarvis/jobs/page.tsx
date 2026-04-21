"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const BACKEND = "/api/proxy";

type Job = {
  id: string;
  title: string;
  description?: string;
  priority: "low" | "medium" | "high" | "urgent";
  status: "pending" | "in_progress" | "done" | "blocked" | "cancelled";
  assigned_to?: string;
  due_date?: string;
  created_at: string;
  completed_at?: string;
  result?: string;
  notes?: string;
  tags?: string[];
};

const AGENTS = [
  "Supervisor (Chief of Staff)",
  "Calendar Agent",
  "Email Agent",
  "Task Agent",
  "Finance Agent",
  "Healthcare Agent",
  "Business Agent",
  "Content Agent",
  "Social Media Manager",
  "Copywriter",
  "Data Analyst",
  "Sales Manager",
  "SEO Specialist",
  "Personal Coach",
  "Proactive Agent",
];

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-slate-700 text-slate-300",
  medium: "bg-blue-900/50 text-blue-300",
  high: "bg-orange-900/50 text-orange-300",
  urgent: "bg-red-900/50 text-red-300",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-slate-700 text-slate-300",
  in_progress: "bg-yellow-900/50 text-yellow-300",
  done: "bg-emerald-900/50 text-emerald-300",
  blocked: "bg-red-900/50 text-red-300",
  cancelled: "bg-slate-800 text-slate-500",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  in_progress: "In Progress",
  done: "Done",
  blocked: "Blocked",
  cancelled: "Cancelled",
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [showForm, setShowForm] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [executing, setExecuting] = useState<string | null>(null);

  // Form state
  const [form, setForm] = useState({
    title: "",
    description: "",
    priority: "medium",
    assigned_to: "",
    due_date: "",
    notes: "",
    auto_execute: false,
  });
  const [submitting, setSubmitting] = useState(false);

  async function loadJobs() {
    setLoading(true);
    setError(null);
    try {
      const url =
        filter === "all"
          ? `${BACKEND}/api/jobs`
          : `${BACKEND}/api/jobs?status=${filter}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const data: Job[] = await res.json();
      setJobs(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJobs();
  }, [filter]);

  async function createJob(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(`${BACKEND}/api/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: form.title,
          description: form.description || undefined,
          priority: form.priority,
          assigned_to: form.assigned_to || undefined,
          due_date: form.due_date || undefined,
          notes: form.notes || undefined,
          auto_execute: form.auto_execute,
        }),
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      setForm({ title: "", description: "", priority: "medium", assigned_to: "", due_date: "", notes: "", auto_execute: false });
      setShowForm(false);
      await loadJobs();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to create job");
    } finally {
      setSubmitting(false);
    }
  }

  async function executeJob(jobId: string) {
    setExecuting(jobId);
    try {
      const res = await fetch(`${BACKEND}/api/jobs/${jobId}/execute`, { method: "POST" });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const updated: Job = await res.json();
      setJobs((prev) => prev.map((j) => (j.id === jobId ? updated : j)));
      if (selectedJob?.id === jobId) setSelectedJob(updated);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Execution failed");
    } finally {
      setExecuting(null);
    }
  }

  async function updateStatus(jobId: string, status: string) {
    try {
      const res = await fetch(`${BACKEND}/api/jobs/${jobId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const updated: Job = await res.json();
      setJobs((prev) => prev.map((j) => (j.id === jobId ? updated : j)));
      if (selectedJob?.id === jobId) setSelectedJob(updated);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Update failed");
    }
  }

  async function deleteJob(jobId: string) {
    if (!confirm("Delete this job?")) return;
    try {
      await fetch(`${BACKEND}/api/jobs/${jobId}`, { method: "DELETE" });
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      if (selectedJob?.id === jobId) setSelectedJob(null);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  const filters = ["all", "pending", "in_progress", "done", "blocked"];

  return (
    <Shell>
      <div className="mx-auto max-w-6xl space-y-5 py-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-emerald-300">Jobs</h1>
            <p className="mt-0.5 text-sm text-slate-400">
              Assign tasks to JARVIS agents and track execution
            </p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            data-testid="create-job-btn"
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors"
          >
            + New Job
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-700 bg-red-900/20 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Filter bar */}
        <div className="flex gap-2">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors ${
                filter === f
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {f === "in_progress" ? "In Progress" : f}
            </button>
          ))}
        </div>

        {/* Main layout */}
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Job list */}
          <div className="space-y-2">
            {loading && (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse rounded-xl border border-slate-700 bg-slate-800/50 h-20" />
                ))}
              </div>
            )}
            {!loading && jobs.length === 0 && (
              <div className="rounded-xl border border-slate-700 bg-slate-800/30 p-8 text-center">
                <p className="text-slate-400">No jobs yet. Create one to get started.</p>
              </div>
            )}
            {!loading &&
              jobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job)}
                  data-testid="job-item"
                  className={`w-full rounded-xl border text-left p-4 transition-colors ${
                    selectedJob?.id === job.id
                      ? "border-emerald-600 bg-emerald-900/10"
                      : "border-slate-700 bg-slate-800/50 hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-medium text-slate-100 text-sm leading-tight">
                      {job.title}
                    </span>
                    <div className="flex shrink-0 gap-1">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${PRIORITY_COLORS[job.priority]}`}>
                        {job.priority}
                      </span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_COLORS[job.status]}`}>
                        {STATUS_LABELS[job.status]}
                      </span>
                    </div>
                  </div>
                  {job.assigned_to && (
                    <p className="mt-1 text-xs text-slate-500">→ {job.assigned_to}</p>
                  )}
                  <p className="mt-1 text-xs text-slate-600">
                    {new Date(job.created_at).toLocaleDateString()}
                    {job.due_date && ` · Due ${new Date(job.due_date).toLocaleDateString()}`}
                  </p>
                </button>
              ))}
          </div>

          {/* Detail panel */}
          <div>
            {selectedJob ? (
              <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-4">
                <div className="flex items-start justify-between">
                  <h2 className="font-semibold text-slate-100">{selectedJob.title}</h2>
                  <button
                    onClick={() => deleteJob(selectedJob.id)}
                    className="text-xs text-red-400 hover:text-red-300"
                    data-testid="delete-job-btn"
                  >
                    Delete
                  </button>
                </div>

                <div className="flex gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_COLORS[selectedJob.priority]}`}>
                    {selectedJob.priority}
                  </span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[selectedJob.status]}`}>
                    {STATUS_LABELS[selectedJob.status]}
                  </span>
                </div>

                {selectedJob.description && (
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {selectedJob.description}
                  </p>
                )}

                {selectedJob.assigned_to && (
                  <div>
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Assigned to</span>
                    <p className="text-sm text-slate-200 mt-0.5">{selectedJob.assigned_to}</p>
                  </div>
                )}

                {selectedJob.due_date && (
                  <div>
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Due</span>
                    <p className="text-sm text-slate-200 mt-0.5">
                      {new Date(selectedJob.due_date).toLocaleDateString("en-US", {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </p>
                  </div>
                )}

                {selectedJob.notes && (
                  <div>
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Notes</span>
                    <p className="text-sm text-slate-300 mt-0.5 leading-relaxed">{selectedJob.notes}</p>
                  </div>
                )}

                {selectedJob.result && (
                  <div>
                    <span className="text-xs text-emerald-500 uppercase tracking-wide">JARVIS Result</span>
                    <div className="mt-1 rounded-lg bg-slate-900 p-3 text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto">
                      {selectedJob.result}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap gap-2 pt-2">
                  {selectedJob.status === "pending" && (
                    <button
                      onClick={() => executeJob(selectedJob.id)}
                      disabled={executing === selectedJob.id}
                      data-testid="execute-job-btn"
                      className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
                    >
                      {executing === selectedJob.id ? "Running…" : "Execute with JARVIS"}
                    </button>
                  )}
                  {selectedJob.status === "pending" && (
                    <button
                      onClick={() => updateStatus(selectedJob.id, "in_progress")}
                      className="rounded-lg bg-yellow-800 px-3 py-1.5 text-xs font-semibold text-yellow-200 hover:bg-yellow-700 transition-colors"
                    >
                      Mark In Progress
                    </button>
                  )}
                  {selectedJob.status === "in_progress" && (
                    <>
                      <button
                        onClick={() => executeJob(selectedJob.id)}
                        disabled={executing === selectedJob.id}
                        className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
                      >
                        {executing === selectedJob.id ? "Running…" : "Execute with JARVIS"}
                      </button>
                      <button
                        onClick={() => updateStatus(selectedJob.id, "done")}
                        className="rounded-lg bg-emerald-900 px-3 py-1.5 text-xs font-semibold text-emerald-200 hover:bg-emerald-800 transition-colors"
                      >
                        Mark Done
                      </button>
                      <button
                        onClick={() => updateStatus(selectedJob.id, "blocked")}
                        className="rounded-lg bg-red-900 px-3 py-1.5 text-xs font-semibold text-red-200 hover:bg-red-800 transition-colors"
                      >
                        Mark Blocked
                      </button>
                    </>
                  )}
                  {(selectedJob.status === "blocked" || selectedJob.status === "done") && (
                    <button
                      onClick={() => updateStatus(selectedJob.id, "pending")}
                      className="rounded-lg bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-600 transition-colors"
                    >
                      Reopen
                    </button>
                  )}
                </div>

                <p className="text-xs text-slate-600">
                  Created {new Date(selectedJob.created_at).toLocaleString()}
                  {selectedJob.completed_at &&
                    ` · Completed ${new Date(selectedJob.completed_at).toLocaleString()}`}
                </p>
              </div>
            ) : (
              <div className="rounded-xl border border-slate-700 bg-slate-800/20 p-10 text-center">
                <p className="text-slate-500 text-sm">Select a job to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Job Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
            <h2 className="mb-4 text-lg font-bold text-emerald-300">New Job</h2>
            <form onSubmit={createJob} className="space-y-4" data-testid="create-job-form">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-400">
                  Title *
                </label>
                <input
                  required
                  value={form.title}
                  onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                  placeholder="e.g. Summarize this week's emails"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-slate-400">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  placeholder="What should JARVIS do, and what context does it need?"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:outline-none resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-400">
                    Priority
                  </label>
                  <select
                    value={form.priority}
                    onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:outline-none"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-400">
                    Due Date
                  </label>
                  <input
                    type="date"
                    value={form.due_date}
                    onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-slate-400">
                  Assign to Agent
                </label>
                <select
                  value={form.assigned_to}
                  onChange={(e) => setForm((f) => ({ ...f, assigned_to: e.target.value }))}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:outline-none"
                >
                  <option value="">JARVIS decides</option>
                  {AGENTS.map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-slate-400">
                  Notes
                </label>
                <textarea
                  rows={2}
                  value={form.notes}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                  placeholder="Any extra context or instructions…"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:outline-none resize-none"
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.auto_execute}
                  onChange={(e) => setForm((f) => ({ ...f, auto_execute: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-800 accent-emerald-500"
                />
                <span className="text-sm text-slate-300">
                  Execute immediately with JARVIS
                </span>
              </label>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
                >
                  {submitting ? "Creating…" : "Create Job"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Shell>
  );
}
