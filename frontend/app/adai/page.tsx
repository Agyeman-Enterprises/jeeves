"use client";

import Shell from "@/components/layout/Shell";
import Link from "next/link";
import { useEffect, useState } from "react";

interface DashboardStats {
  totalWorkspaces: number;
  activeConnections: number;
  activeCampaigns: number;
  pendingApprovals: number;
  todaySpend: number;
  monthlySpend: number;
  totalConversions: number;
  avgRoas: number;
  lastRunStatus: string;
  lastRunTime: string | null;
  alerts: Alert[];
}

interface Alert {
  type: string;
  level: string;
  message: string;
}

interface Campaign {
  id: string;
  name: string;
  workspace_id: string;
  status: string;
  metrics?: {
    spend: number;
    conversions: number;
    kpis: {
      roas: number;
      cpa: number;
    };
  };
}

const PRIORITY_COMPANIES = [
  "MedRx",
  "Bookadoc2u",
  "MyHealthAlly",
  "InkwellPublishing",
  "AccessMD",
];

const API_BASE = "/api/proxy";

export default function AdAIDashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch status and campaigns in parallel
        const [statusRes, campaignsRes] = await Promise.all([
          fetch(`${API_BASE}/api/adai/status`),
          fetch(`${API_BASE}/api/adai/campaigns`),
        ]);

        if (!statusRes.ok || !campaignsRes.ok) {
          throw new Error("Failed to fetch AdAI data");
        }

        const statusData = await statusRes.json();
        const campaignsData = await campaignsRes.json();

        const summary = statusData.summary || {};
        const alerts = statusData.alerts || [];

        // Calculate today's spend (mock for now, would need separate endpoint)
        const totalSpend = summary.total_spend || 0;
        const todaySpend = totalSpend * 0.033; // Approximate daily from monthly

        setStats({
          totalWorkspaces: summary.total_workspaces || 31,
          activeConnections: summary.active_campaigns || 0,
          activeCampaigns: summary.active_campaigns || 0,
          pendingApprovals: 2, // Would come from approvals endpoint
          todaySpend: todaySpend,
          monthlySpend: totalSpend,
          totalConversions: summary.total_conversions || 0,
          avgRoas: summary.avg_roas || 0,
          lastRunStatus: "completed",
          lastRunTime: statusData.generated_at || new Date().toISOString(),
          alerts: alerts,
        });

        setCampaigns(campaignsData.campaigns || []);
      } catch (err) {
        console.error("Error fetching AdAI data:", err);
        setError(err instanceof Error ? err.message : "Unknown error");

        // Fallback to mock data
        setStats({
          totalWorkspaces: 31,
          activeConnections: 5,
          activeCampaigns: 3,
          pendingApprovals: 2,
          todaySpend: 42.5,
          monthlySpend: 127.8,
          totalConversions: 36,
          avgRoas: 6.11,
          lastRunStatus: "completed",
          lastRunTime: new Date().toISOString(),
          alerts: [],
        });
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const spendPercentage = stats
    ? Math.min(100, (stats.monthlySpend / 150) * 100)
    : 0;
  const spendColor =
    spendPercentage >= 100
      ? "text-red-400"
      : spendPercentage >= 80
        ? "text-amber-400"
        : "text-emerald-400";

  const handleTriggerRun = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/adai/analytics/report`, {
        method: "GET",
      });
      if (response.ok) {
        alert("Report generation triggered successfully!");
      } else {
        alert("Failed to trigger report generation");
      }
    } catch (err) {
      alert("Error: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  return (
    <Shell>
      <div className="p-6 space-y-6 text-slate-200">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">AdAI Dashboard</h1>
            <p className="mt-2 text-slate-400">
              Advertising automation across {stats?.totalWorkspaces || 31} companies
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/adai/approvals"
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg text-sm font-medium transition-colors"
            >
              Pending Approvals ({stats?.pendingApprovals || 0})
            </Link>
            <button
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors"
              onClick={handleTriggerRun}
            >
              Generate Report
            </button>
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="rounded-xl border border-amber-700 bg-amber-900/30 p-4 text-amber-200">
            <strong>Note:</strong> Using cached data. API error: {error}
          </div>
        )}

        {/* Alerts Banner */}
        {stats?.alerts && stats.alerts.length > 0 && (
          <div className="rounded-xl border border-red-700 bg-red-900/30 p-4">
            {stats.alerts.map((alert, idx) => (
              <div key={idx} className="text-red-200">
                <strong className="uppercase">{alert.level}:</strong> {alert.message}
              </div>
            ))}
          </div>
        )}

        {/* Stats Grid */}
        <section className="grid gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Today&apos;s Spend
            </div>
            <div className="mt-2 text-3xl font-semibold">
              ${stats?.todaySpend.toFixed(2) || "—"}
            </div>
            <p className="mt-1 text-xs text-slate-400">Across all workspaces</p>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Monthly Spend
            </div>
            <div className={`mt-2 text-3xl font-semibold ${spendColor}`}>
              ${stats?.monthlySpend.toFixed(2) || "—"}
            </div>
            <div className="mt-2 w-full bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${spendPercentage >= 100 ? "bg-red-500" : spendPercentage >= 80 ? "bg-amber-500" : "bg-emerald-500"}`}
                style={{ width: `${spendPercentage}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-slate-400">
              {spendPercentage.toFixed(0)}% of $150 threshold
            </p>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Active Campaigns
            </div>
            <div className="mt-2 text-3xl font-semibold">
              {stats?.activeCampaigns || 0}
            </div>
            <p className="mt-1 text-xs text-slate-400">
              {stats?.totalConversions || 0} total conversions
            </p>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Avg ROAS
            </div>
            <div
              className={`mt-2 text-3xl font-semibold ${(stats?.avgRoas || 0) >= 4 ? "text-emerald-400" : (stats?.avgRoas || 0) >= 2 ? "text-amber-400" : "text-red-400"}`}
            >
              {stats?.avgRoas?.toFixed(2) || "—"}x
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Return on ad spend
            </p>
          </div>
        </section>

        {/* Priority Companies */}
        <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-400 mb-4">
            Priority Companies (60% budget allocation)
          </div>
          <div className="grid gap-3 md:grid-cols-5">
            {PRIORITY_COMPANIES.map((company) => {
              const companyCampaigns = campaigns.filter(
                (c) => c.workspace_id?.toLowerCase() === company.toLowerCase()
              );
              const companySpend = companyCampaigns.reduce(
                (sum, c) => sum + (c.metrics?.spend || 0),
                0
              );
              return (
                <Link
                  key={company}
                  href={`/adai/workspaces/${company.toLowerCase()}`}
                  className="p-3 rounded-lg border border-slate-600 hover:border-blue-500 hover:bg-slate-800/50 transition-colors"
                >
                  <div className="font-medium">{company}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    ${companySpend.toFixed(2)} spend
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {companyCampaigns.length} campaigns
                  </div>
                </Link>
              );
            })}
          </div>
        </section>

        {/* Quick Links */}
        <section className="grid gap-4 md:grid-cols-3">
          <Link
            href="/adai/campaigns"
            className="rounded-xl border border-slate-700 bg-slate-900/70 p-4 hover:border-blue-500 transition-colors"
          >
            <div className="text-lg font-medium">Campaigns</div>
            <p className="mt-1 text-sm text-slate-400">
              View and manage all campaigns ({campaigns.length})
            </p>
          </Link>

          <Link
            href="/adai/creatives"
            className="rounded-xl border border-slate-700 bg-slate-900/70 p-4 hover:border-blue-500 transition-colors"
          >
            <div className="text-lg font-medium">Creatives</div>
            <p className="mt-1 text-sm text-slate-400">
              Creative library and rotation
            </p>
          </Link>

          <Link
            href="/adai/experiments"
            className="rounded-xl border border-slate-700 bg-slate-900/70 p-4 hover:border-blue-500 transition-colors"
          >
            <div className="text-lg font-medium">Experiments</div>
            <p className="mt-1 text-sm text-slate-400">A/B tests and results</p>
          </Link>

          <Link
            href="/adai/audit"
            className="rounded-xl border border-slate-700 bg-slate-900/70 p-4 hover:border-blue-500 transition-colors"
          >
            <div className="text-lg font-medium">Audit Log</div>
            <p className="mt-1 text-sm text-slate-400">
              All decisions and changes
            </p>
          </Link>

          <Link
            href="/adai/connections"
            className="rounded-xl border border-slate-700 bg-slate-900/70 p-4 hover:border-blue-500 transition-colors"
          >
            <div className="text-lg font-medium">Connections</div>
            <p className="mt-1 text-sm text-slate-400">
              Meta/Google/TikTok tokens
            </p>
          </Link>

          <Link
            href="/adai/settings"
            className="rounded-xl border border-slate-700 bg-slate-900/70 p-4 hover:border-blue-500 transition-colors"
          >
            <div className="text-lg font-medium">Settings</div>
            <p className="mt-1 text-sm text-slate-400">Policies and defaults</p>
          </Link>
        </section>

        {/* Recent Campaigns */}
        <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-400 mb-4">
            Recent Campaigns
          </div>
          <div className="space-y-3 text-sm">
            {campaigns.length === 0 ? (
              <div className="py-4 text-center text-slate-400">
                {loading ? "Loading campaigns..." : "No campaigns found"}
              </div>
            ) : (
              campaigns.slice(0, 5).map((campaign) => (
                <div
                  key={campaign.id}
                  className="flex items-center justify-between py-2 border-b border-slate-700"
                >
                  <div>
                    <span
                      className={
                        campaign.status === "ACTIVE"
                          ? "text-emerald-400"
                          : campaign.status === "PAUSED"
                            ? "text-amber-400"
                            : "text-slate-400"
                      }
                    >
                      {campaign.status}
                    </span>{" "}
                    {campaign.name}
                  </div>
                  <div className="text-slate-400">
                    ${campaign.metrics?.spend?.toFixed(2) || "0.00"} spend |{" "}
                    {campaign.metrics?.conversions || 0} conv
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Last Run Status */}
        <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wide text-slate-400">
                Last Sync
              </div>
              <div
                className={`mt-1 text-lg font-medium ${stats?.lastRunStatus === "completed" ? "text-emerald-400" : "text-red-400"}`}
              >
                {stats?.lastRunStatus === "completed" ? "✓ Success" : "✗ Failed"}
              </div>
            </div>
            <div className="text-right text-slate-400 text-sm">
              {stats?.lastRunTime
                ? new Date(stats.lastRunTime).toLocaleString()
                : "Never"}
            </div>
          </div>
        </section>
      </div>
    </Shell>
  );
}
