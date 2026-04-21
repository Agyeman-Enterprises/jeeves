"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const JARVIS_URL = "/api/proxy";

type KnowledgeStats = {
  total_documents?: number;
  total_chunks?: number;
  last_indexed?: string;
  collections?: Record<string, { count: number }>;
};

type SearchResult = {
  id: string;
  content: string;
  source?: string;
  score?: number;
  metadata?: Record<string, unknown>;
};

export default function KnowledgePage() {
  const [stats, setStats]     = useState<KnowledgeStats | null>(null);
  const [query, setQuery]     = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${JARVIS_URL}/api/knowledge/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const r = await fetch(`${JARVIS_URL}/api/knowledge/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 10 }),
      });
      if (r.ok) {
        const data = await r.json();
        setResults(Array.isArray(data) ? data : data.results ?? []);
      }
    } catch {
      // offline
    } finally {
      setSearching(false);
    }
  };

  return (
    <Shell>
      <div className="flex h-full gap-6">
        <div className="flex-1 min-w-0">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-white">Knowledge Library</h1>
            <p className="text-sm text-slate-400 mt-0.5">RAG document store · vector search · Pinecone index</p>
          </div>

          {/* Search */}
          <div className="mb-6 flex gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && search()}
              placeholder="Search the knowledge base…"
              className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-emerald-500/50 focus:outline-none"
            />
            <button
              onClick={search}
              disabled={searching || !query.trim()}
              className="rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-40 transition-colors"
            >
              {searching ? "…" : "Search"}
            </button>
          </div>

          {/* Results */}
          {results.length > 0 && (
            <div className="mb-6">
              <h2 className="mb-3 text-sm font-semibold text-white">
                Results <span className="text-slate-500 font-normal">({results.length})</span>
              </h2>
              <div className="space-y-3">
                {results.map((r) => (
                  <div key={r.id} className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                    <div className="flex items-center justify-between mb-2">
                      {r.source && (
                        <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                          {r.source}
                        </span>
                      )}
                      {r.score !== undefined && (
                        <span className="text-[10px] text-emerald-400">
                          {(r.score * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed line-clamp-4">
                      {r.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Stats */}
          {!loading && stats && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <StatCard label="Documents"    value={String(stats.total_documents ?? "—")} />
              <StatCard label="Chunks"       value={String(stats.total_chunks ?? "—")} />
              <StatCard label="Last indexed" value={stats.last_indexed ? new Date(stats.last_indexed).toLocaleDateString() : "—"} />
            </div>
          )}

          {!loading && !stats && results.length === 0 && (
            <div className="flex h-40 items-center justify-center text-sm text-slate-500">
              Knowledge base offline or empty — index documents via JARVIS backend
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="w-64 shrink-0 space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Index Stats
            </h3>
            <div className="space-y-2">
              <StatRow label="Documents"  value={String(stats?.total_documents ?? "—")} />
              <StatRow label="Chunks"     value={String(stats?.total_chunks ?? "—")} />
            </div>
          </div>

          {stats?.collections && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
                Collections
              </h3>
              <div className="space-y-1.5">
                {Object.entries(stats.collections).map(([name, col]) => (
                  <div key={name} className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 truncate">{name}</span>
                    <span className="text-slate-600">{col.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Vector Store
            </h3>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Pinecone index · semantic search · used by all 26 agents for RAG context retrieval.
            </p>
          </div>
        </div>
      </div>
    </Shell>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-xl font-bold text-white">{value}</p>
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
