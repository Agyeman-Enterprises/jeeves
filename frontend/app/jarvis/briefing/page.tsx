"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const BACKEND = "/api/proxy";

type BriefingSection = {
  title: string;
  items: { label: string; value?: string }[];
};

type Briefing = {
  date: string;
  timezone: string;
  sections: BriefingSection[];
  raw: string;
};

export default function DailyBriefingPage() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchBriefing() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND}/briefing/today`);
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const data = await res.json();
      setBriefing(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load briefing");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBriefing();
  }, []);

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <Shell>
      <div className="mx-auto max-w-4xl space-y-6 py-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-emerald-300">Daily Briefing</h1>
            <p className="mt-1 text-sm text-slate-400">{today}</p>
          </div>
          <button
            onClick={fetchBriefing}
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
          >
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-700 bg-red-900/20 p-4 text-sm text-red-300">
            {error} — Make sure the JARVIS backend is running on port 8000.
          </div>
        )}

        {/* Loading skeleton */}
        {loading && !error && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse rounded-xl border border-slate-700 bg-slate-800/50 p-5">
                <div className="h-4 w-1/3 rounded bg-slate-700 mb-3" />
                <div className="space-y-2">
                  <div className="h-3 w-full rounded bg-slate-700" />
                  <div className="h-3 w-4/5 rounded bg-slate-700" />
                  <div className="h-3 w-3/5 rounded bg-slate-700" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Briefing content */}
        {!loading && briefing && (
          <>
            {/* Sections */}
            {briefing.sections && briefing.sections.length > 0 ? (
              <div className="space-y-4">
                {briefing.sections.map((section, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-slate-700 bg-slate-800/50 p-5"
                  >
                    <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-emerald-400">
                      {section.title}
                    </h2>
                    {section.items.length === 0 ? (
                      <p className="text-xs text-slate-500">Nothing to report.</p>
                    ) : (
                      <ul className="space-y-2">
                        {section.items.map((item, iIdx) => (
                          <li
                            key={iIdx}
                            className="flex items-start justify-between gap-4 text-sm"
                          >
                            <span className="text-slate-200">{item.label}</span>
                            {item.value && (
                              <span className="shrink-0 text-right font-mono text-emerald-300">
                                {item.value}
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              /* Raw fallback */
              <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5">
                <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-emerald-400">
                  Full Briefing
                </h2>
                <pre className="whitespace-pre-wrap text-sm text-slate-300 leading-relaxed">
                  {briefing.raw}
                </pre>
              </div>
            )}

            <p className="text-right text-xs text-slate-600">
              Generated {briefing.date} · {briefing.timezone}
            </p>
          </>
        )}

        {/* Empty state */}
        {!loading && !briefing && !error && (
          <div className="rounded-xl border border-slate-700 bg-slate-800/30 p-10 text-center">
            <p className="text-slate-400">No briefing available. Click Refresh to generate one.</p>
          </div>
        )}
      </div>
    </Shell>
  );
}
