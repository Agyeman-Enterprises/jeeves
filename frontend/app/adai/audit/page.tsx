"use client";

import Shell from "@/components/layout/Shell";
import Link from "next/link";
import { useEffect, useState } from "react";

interface AuditEntry {
  id: string;
  workspaceName: string;
  action: string;
  entityType: string;
  entityName: string;
  performedBy: string;
  beforeState: Record<string, unknown> | null;
  afterState: Record<string, unknown> | null;
  createdAt: string;
}

export default function AdAIAuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    // TODO: Fetch from API
    setEntries([
      {
        id: "aud-1",
        workspaceName: "MedRx",
        action: "execute_scale",
        entityType: "campaign",
        entityName: "Telehealth Awareness Q1",
        performedBy: "system",
        beforeState: { daily_budget: 4000 },
        afterState: { daily_budget: 4800 },
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: "aud-2",
        workspaceName: "AccessMD",
        action: "execute_pause",
        entityType: "ad",
        entityName: "Provider Network Ad #5",
        performedBy: "system",
        beforeState: { status: "ACTIVE" },
        afterState: { status: "PAUSED" },
        createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: "aud-3",
        workspaceName: "Bookadoc2u",
        action: "approval_rejected",
        entityType: "creative",
        entityName: "Summer Promo Video",
        performedBy: "user:admin",
        beforeState: null,
        afterState: null,
        createdAt: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: "aud-4",
        workspaceName: "InkwellPublishing",
        action: "metrics_synced",
        entityType: "workspace",
        entityName: "InkwellPublishing",
        performedBy: "system",
        beforeState: null,
        afterState: { campaigns_synced: 3, ads_synced: 12 },
        createdAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      },
    ]);
    setLoading(false);
  }, []);

  const getActionColor = (action: string) => {
    if (action.includes("scale")) return "text-emerald-400";
    if (action.includes("pause")) return "text-red-400";
    if (action.includes("rotate")) return "text-amber-400";
    if (action.includes("rejected")) return "text-red-400";
    if (action.includes("approved")) return "text-emerald-400";
    return "text-blue-400";
  };

  const formatAction = (action: string) => {
    return action
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <Shell>
      <div className="p-6 space-y-6 text-slate-200">
        <header>
          <div className="flex items-center gap-2">
            <Link href="/adai" className="text-slate-400 hover:text-slate-200">
              AdAI
            </Link>
            <span className="text-slate-600">/</span>
            <span>Audit Log</span>
          </div>
          <h1 className="text-3xl font-bold mt-2">Audit Log</h1>
          <p className="mt-2 text-slate-400">
            Complete history of all AdAI decisions and actions
          </p>
        </header>

        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading...</div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="rounded-xl border border-slate-700 bg-slate-900/70 overflow-hidden"
              >
                <div
                  className="p-4 cursor-pointer hover:bg-slate-800/30"
                  onClick={() =>
                    setExpandedId(expandedId === entry.id ? null : entry.id)
                  }
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div
                        className={`font-medium ${getActionColor(entry.action)}`}
                      >
                        {formatAction(entry.action)}
                      </div>
                      <div className="text-slate-400">
                        {entry.entityType}: {entry.entityName}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-sm text-slate-400">
                        {entry.workspaceName}
                      </div>
                      <div className="text-sm text-slate-500">
                        {new Date(entry.createdAt).toLocaleString()}
                      </div>
                      <span className="text-slate-500">
                        {expandedId === entry.id ? "▼" : "▶"}
                      </span>
                    </div>
                  </div>
                </div>

                {expandedId === entry.id && (
                  <div className="px-4 pb-4 border-t border-slate-700 pt-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">
                          Before State
                        </div>
                        <pre className="text-sm bg-slate-800/50 p-3 rounded-lg overflow-x-auto">
                          {entry.beforeState
                            ? JSON.stringify(entry.beforeState, null, 2)
                            : "—"}
                        </pre>
                      </div>
                      <div>
                        <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">
                          After State
                        </div>
                        <pre className="text-sm bg-slate-800/50 p-3 rounded-lg overflow-x-auto">
                          {entry.afterState
                            ? JSON.stringify(entry.afterState, null, 2)
                            : "—"}
                        </pre>
                      </div>
                    </div>
                    <div className="mt-4 text-sm text-slate-400">
                      Performed by:{" "}
                      <span className="text-slate-300">{entry.performedBy}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
