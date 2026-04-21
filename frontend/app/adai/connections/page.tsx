"use client";

import Shell from "@/components/layout/Shell";
import Link from "next/link";
import { useEffect, useState } from "react";

interface Connection {
  id: string;
  workspaceName: string;
  platform: "meta" | "google" | "tiktok";
  accountId: string;
  accountName: string;
  status: "active" | "expired" | "error" | "pending";
  lastHealthCheck: string | null;
  tokenExpiresAt: string | null;
}

export default function AdAIConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch from API
    setConnections([
      {
        id: "conn-1",
        workspaceName: "MedRx",
        platform: "meta",
        accountId: "act_123456789",
        accountName: "MedRx Marketing",
        status: "active",
        lastHealthCheck: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        tokenExpiresAt: new Date(
          Date.now() + 45 * 24 * 60 * 60 * 1000
        ).toISOString(),
      },
      {
        id: "conn-2",
        workspaceName: "Bookadoc2u",
        platform: "meta",
        accountId: "act_234567890",
        accountName: "Bookadoc2u Ads",
        status: "active",
        lastHealthCheck: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        tokenExpiresAt: new Date(
          Date.now() + 30 * 24 * 60 * 60 * 1000
        ).toISOString(),
      },
      {
        id: "conn-3",
        workspaceName: "AccessMD",
        platform: "meta",
        accountId: "act_345678901",
        accountName: "AccessMD Healthcare",
        status: "expired",
        lastHealthCheck: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
        tokenExpiresAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: "conn-4",
        workspaceName: "InkwellPublishing",
        platform: "meta",
        accountId: "act_456789012",
        accountName: "Inkwell Books",
        status: "active",
        lastHealthCheck: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        tokenExpiresAt: new Date(
          Date.now() + 5 * 24 * 60 * 60 * 1000
        ).toISOString(),
      },
      {
        id: "conn-5",
        workspaceName: "MyHealthAlly",
        platform: "meta",
        accountId: "",
        accountName: "",
        status: "pending",
        lastHealthCheck: null,
        tokenExpiresAt: null,
      },
    ]);
    setLoading(false);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return (
          <span className="px-2 py-1 rounded text-xs font-medium text-emerald-400 bg-emerald-400/10">
            Active
          </span>
        );
      case "expired":
        return (
          <span className="px-2 py-1 rounded text-xs font-medium text-red-400 bg-red-400/10">
            Expired
          </span>
        );
      case "error":
        return (
          <span className="px-2 py-1 rounded text-xs font-medium text-red-400 bg-red-400/10">
            Error
          </span>
        );
      case "pending":
        return (
          <span className="px-2 py-1 rounded text-xs font-medium text-slate-400 bg-slate-400/10">
            Not Connected
          </span>
        );
      default:
        return null;
    }
  };

  const getDaysUntilExpiry = (expiresAt: string | null) => {
    if (!expiresAt) return null;
    const days = Math.ceil(
      (new Date(expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    );
    return days;
  };

  const handleConnect = (workspaceName: string) => {
    // TODO: Trigger OAuth flow
    alert(`Connect ${workspaceName} to Meta`);
  };

  const handleRefresh = (id: string) => {
    // TODO: Trigger token refresh
    alert(`Refreshing token for ${id}`);
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
            <span>Connections</span>
          </div>
          <h1 className="text-3xl font-bold mt-2">Platform Connections</h1>
          <p className="mt-2 text-slate-400">
            Manage Meta, Google, and TikTok ad account connections
          </p>
        </header>

        {/* Summary */}
        <section className="grid gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Total Workspaces
            </div>
            <div className="mt-2 text-3xl font-semibold">31</div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Connected
            </div>
            <div className="mt-2 text-3xl font-semibold text-emerald-400">
              {connections.filter((c) => c.status === "active").length}
            </div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Expired
            </div>
            <div className="mt-2 text-3xl font-semibold text-red-400">
              {connections.filter((c) => c.status === "expired").length}
            </div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Pending Setup
            </div>
            <div className="mt-2 text-3xl font-semibold text-slate-400">
              {connections.filter((c) => c.status === "pending").length}
            </div>
          </div>
        </section>

        {/* Connections List */}
        <section className="space-y-4">
          {loading ? (
            <div className="text-center py-12 text-slate-400">Loading...</div>
          ) : (
            connections.map((conn) => {
              const daysUntilExpiry = getDaysUntilExpiry(conn.tokenExpiresAt);
              const isExpiringSoon =
                daysUntilExpiry !== null && daysUntilExpiry <= 7;

              return (
                <div
                  key={conn.id}
                  className="rounded-xl border border-slate-700 bg-slate-900/70 p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-blue-600 flex items-center justify-center text-xl font-bold">
                        {conn.platform === "meta" ? "M" : conn.platform[0].toUpperCase()}
                      </div>
                      <div>
                        <div className="font-medium text-lg">
                          {conn.workspaceName}
                        </div>
                        <div className="text-sm text-slate-400">
                          {conn.accountName || "Not connected"}{" "}
                          {conn.accountId && `• ${conn.accountId}`}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {getStatusBadge(conn.status)}

                      {conn.status === "pending" ? (
                        <button
                          onClick={() => handleConnect(conn.workspaceName)}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors"
                        >
                          Connect Meta
                        </button>
                      ) : conn.status === "expired" ? (
                        <button
                          onClick={() => handleConnect(conn.workspaceName)}
                          className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium transition-colors"
                        >
                          Reconnect
                        </button>
                      ) : (
                        <button
                          onClick={() => handleRefresh(conn.id)}
                          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
                        >
                          Refresh
                        </button>
                      )}
                    </div>
                  </div>

                  {conn.status === "active" && (
                    <div className="mt-4 pt-4 border-t border-slate-700 flex items-center justify-between text-sm">
                      <div className="text-slate-400">
                        Last health check:{" "}
                        {conn.lastHealthCheck
                          ? new Date(conn.lastHealthCheck).toLocaleString()
                          : "Never"}
                      </div>
                      <div
                        className={
                          isExpiringSoon ? "text-amber-400" : "text-slate-400"
                        }
                      >
                        {daysUntilExpiry !== null && (
                          <>
                            Token expires in {daysUntilExpiry} days
                            {isExpiringSoon && " ⚠️"}
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </section>
      </div>
    </Shell>
  );
}
