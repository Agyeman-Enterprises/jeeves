"use client";

import Shell from "@/components/layout/Shell";
import Link from "next/link";
import { useEffect, useState } from "react";

interface ApprovalRequest {
  id: string;
  workspaceId: string;
  workspaceName: string;
  decisionId: string;
  decisionType: string;
  entityType: string;
  entityName: string;
  reason: string;
  suggestedAction: Record<string, unknown>;
  spendImpact: number;
  createdAt: string;
}

export default function AdAIApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch from API
    setApprovals([
      {
        id: "apr-1",
        workspaceId: "ws-bookadoc2u",
        workspaceName: "Bookadoc2u",
        decisionId: "dec-123",
        decisionType: "rotate",
        entityType: "ad",
        entityName: "Summer Campaign Ad #3",
        reason: "CTR (0.3%) is below threshold (0.5%) and declining",
        suggestedAction: { action: "rotate_creative", reason: "low_ctr" },
        spendImpact: 15,
        createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: "apr-2",
        workspaceId: "ws-medrx",
        workspaceName: "MedRx",
        decisionId: "dec-124",
        decisionType: "scale",
        entityType: "campaign",
        entityName: "Telehealth Awareness Q1",
        reason:
          "CPA ($12.50) is below target ($20) with sufficient evidence for 3+ days",
        suggestedAction: { action: "increase_budget", percent: 30 },
        spendImpact: 45,
        createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      },
    ]);
    setLoading(false);
  }, []);

  const handleApprove = async (id: string) => {
    // TODO: Call API
    alert(`Approved ${id}`);
    setApprovals((prev) => prev.filter((a) => a.id !== id));
  };

  const handleReject = async (id: string) => {
    // TODO: Call API
    alert(`Rejected ${id}`);
    setApprovals((prev) => prev.filter((a) => a.id !== id));
  };

  const getDecisionTypeColor = (type: string) => {
    switch (type) {
      case "scale":
        return "text-emerald-400 bg-emerald-400/10";
      case "pause":
        return "text-red-400 bg-red-400/10";
      case "rotate":
        return "text-amber-400 bg-amber-400/10";
      default:
        return "text-blue-400 bg-blue-400/10";
    }
  };

  return (
    <Shell>
      <div className="p-6 space-y-6 text-slate-200">
        <header className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Link href="/adai" className="text-slate-400 hover:text-slate-200">
                AdAI
              </Link>
              <span className="text-slate-600">/</span>
              <span>Approvals</span>
            </div>
            <h1 className="text-3xl font-bold mt-2">Pending Approvals</h1>
            <p className="mt-2 text-slate-400">
              Review and approve proposed ad changes
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{approvals.length}</div>
            <div className="text-sm text-slate-400">pending</div>
          </div>
        </header>

        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading...</div>
        ) : approvals.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✓</div>
            <div className="text-xl font-medium">All caught up!</div>
            <p className="text-slate-400 mt-2">
              No pending approvals at this time.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {approvals.map((approval) => (
              <div
                key={approval.id}
                className="rounded-xl border border-slate-700 bg-slate-900/70 p-6"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium uppercase ${getDecisionTypeColor(approval.decisionType)}`}
                      >
                        {approval.decisionType}
                      </span>
                      <span className="text-slate-400">
                        {approval.entityType}
                      </span>
                    </div>
                    <h3 className="text-xl font-medium mt-2">
                      {approval.entityName}
                    </h3>
                    <p className="text-slate-400 mt-1">
                      {approval.workspaceName}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">Est. Impact</div>
                    <div className="text-xl font-medium">
                      ${approval.spendImpact}/day
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-4 bg-slate-800/50 rounded-lg">
                  <div className="text-sm text-slate-400 mb-1">Reason</div>
                  <div>{approval.reason}</div>
                </div>

                <div className="mt-4 p-4 bg-slate-800/50 rounded-lg">
                  <div className="text-sm text-slate-400 mb-1">
                    Suggested Action
                  </div>
                  <code className="text-sm">
                    {JSON.stringify(approval.suggestedAction, null, 2)}
                  </code>
                </div>

                <div className="mt-6 flex items-center justify-between">
                  <div className="text-sm text-slate-400">
                    Proposed {new Date(approval.createdAt).toLocaleString()}
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleReject(approval.id)}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => handleApprove(approval.id)}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium transition-colors"
                    >
                      Approve & Execute
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
