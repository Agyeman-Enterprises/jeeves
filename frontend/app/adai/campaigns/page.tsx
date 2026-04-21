"use client";

import Shell from "@/components/layout/Shell";
import Link from "next/link";
import { useEffect, useState } from "react";

interface Campaign {
  id: string;
  workspace_id: string;
  name: string;
  platform: string;
  status: string;
  daily_budget: number;
  metrics?: {
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
    revenue: number;
    kpis: {
      ctr: number;
      cpc: number;
      cpa: number;
      roas: number;
      cvr: number;
    };
  };
}

const API_BASE = "/api/proxy";

export default function AdAICampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [platformFilter, setPlatformFilter] = useState<string>("all");

  useEffect(() => {
    async function fetchCampaigns() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();
        if (filter !== "all") params.append("status", filter.toUpperCase());
        if (platformFilter !== "all") params.append("platform", platformFilter);

        const response = await fetch(
          `${API_BASE}/api/adai/campaigns?${params.toString()}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch campaigns");
        }

        const data = await response.json();
        setCampaigns(data.campaigns || []);
      } catch (err) {
        console.error("Error fetching campaigns:", err);
        setError(err instanceof Error ? err.message : "Unknown error");

        // Fallback mock data
        setCampaigns([
          {
            id: "camp_001",
            workspace_id: "medrx",
            name: "MedRx Awareness Q1",
            platform: "meta",
            status: "ACTIVE",
            daily_budget: 25,
            metrics: {
              impressions: 15000,
              clicks: 450,
              spend: 75.5,
              conversions: 12,
              revenue: 480,
              kpis: { ctr: 3.0, cpc: 0.17, cpa: 6.29, roas: 6.36, cvr: 2.67 },
            },
          },
          {
            id: "camp_002",
            workspace_id: "bookadoc2u",
            name: "Bookadoc2u Launch",
            platform: "meta",
            status: "ACTIVE",
            daily_budget: 30,
            metrics: {
              impressions: 22000,
              clicks: 680,
              spend: 102.3,
              conversions: 18,
              revenue: 720,
              kpis: { ctr: 3.09, cpc: 0.15, cpa: 5.68, roas: 7.04, cvr: 2.65 },
            },
          },
          {
            id: "camp_003",
            workspace_id: "inkwellpublishing",
            name: "InkwellPublishing Retargeting",
            platform: "meta",
            status: "PAUSED",
            daily_budget: 20,
            metrics: {
              impressions: 8000,
              clicks: 240,
              spend: 48,
              conversions: 6,
              revenue: 180,
              kpis: { ctr: 3.0, cpc: 0.2, cpa: 8.0, roas: 3.75, cvr: 2.5 },
            },
          },
        ]);
      } finally {
        setLoading(false);
      }
    }

    fetchCampaigns();
  }, [filter, platformFilter]);

  const filteredCampaigns =
    filter === "all"
      ? campaigns
      : campaigns.filter((c) => c.status?.toUpperCase() === filter.toUpperCase());

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case "ACTIVE":
        return "text-emerald-400 bg-emerald-400/10";
      case "PAUSED":
        return "text-amber-400 bg-amber-400/10";
      case "DRAFT":
        return "text-blue-400 bg-blue-400/10";
      case "ARCHIVED":
        return "text-slate-400 bg-slate-400/10";
      default:
        return "text-slate-400 bg-slate-400/10";
    }
  };

  const totalDailyBudget = campaigns.reduce((sum, c) => sum + (c.daily_budget || 0), 0);
  const totalSpend = campaigns.reduce((sum, c) => sum + (c.metrics?.spend || 0), 0);
  const totalConversions = campaigns.reduce((sum, c) => sum + (c.metrics?.conversions || 0), 0);
  const totalRevenue = campaigns.reduce((sum, c) => sum + (c.metrics?.revenue || 0), 0);
  const avgRoas = totalSpend > 0 ? totalRevenue / totalSpend : 0;

  const handleStatusChange = async (campaignId: string, newStatus: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/adai/campaigns/${campaignId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        // Refresh campaigns
        setCampaigns((prev) =>
          prev.map((c) => (c.id === campaignId ? { ...c, status: newStatus } : c))
        );
      } else {
        alert("Failed to update campaign status");
      }
    } catch (err) {
      console.error("Error updating campaign:", err);
      alert("Error updating campaign");
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
              <span>Campaigns</span>
            </div>
            <h1 className="text-3xl font-bold mt-2">All Campaigns</h1>
            <p className="mt-2 text-slate-400">
              Campaign performance across all workspaces
            </p>
          </div>
          <div className="flex gap-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="draft">Draft</option>
            </select>
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm"
            >
              <option value="all">All Platforms</option>
              <option value="meta">Meta</option>
              <option value="google">Google</option>
              <option value="tiktok">TikTok</option>
            </select>
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="rounded-xl border border-amber-700 bg-amber-900/30 p-4 text-amber-200">
            <strong>Note:</strong> Using cached data. API error: {error}
          </div>
        )}

        {/* Summary Stats */}
        <section className="grid gap-4 md:grid-cols-5">
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Total Campaigns
            </div>
            <div className="mt-2 text-3xl font-semibold">{campaigns.length}</div>
            <p className="mt-1 text-xs text-slate-400">
              {campaigns.filter((c) => c.status === "ACTIVE").length} active
            </p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Daily Budget
            </div>
            <div className="mt-2 text-3xl font-semibold">
              ${totalDailyBudget.toFixed(2)}
            </div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Total Spend
            </div>
            <div className="mt-2 text-3xl font-semibold">
              ${totalSpend.toFixed(2)}
            </div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Total Conversions
            </div>
            <div className="mt-2 text-3xl font-semibold">{totalConversions}</div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">
              Avg ROAS
            </div>
            <div
              className={`mt-2 text-3xl font-semibold ${avgRoas >= 4 ? "text-emerald-400" : avgRoas >= 2 ? "text-amber-400" : "text-red-400"}`}
            >
              {avgRoas.toFixed(2)}x
            </div>
          </div>
        </section>

        {/* Campaigns Table */}
        <section className="rounded-xl border border-slate-700 bg-slate-900/70 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-slate-400">Loading campaigns...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="text-left px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      Campaign
                    </th>
                    <th className="text-left px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      Status
                    </th>
                    <th className="text-right px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      Budget
                    </th>
                    <th className="text-right px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      Spend
                    </th>
                    <th className="text-right px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      Impr.
                    </th>
                    <th className="text-right px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      CTR
                    </th>
                    <th className="text-right px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      Conv.
                    </th>
                    <th className="text-right px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      ROAS
                    </th>
                    <th className="text-center px-4 py-3 text-xs uppercase tracking-wide text-slate-400">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {filteredCampaigns.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-8 text-center text-slate-400">
                        No campaigns found
                      </td>
                    </tr>
                  ) : (
                    filteredCampaigns.map((campaign) => (
                      <tr key={campaign.id} className="hover:bg-slate-800/30">
                        <td className="px-4 py-3">
                          <div className="font-medium">{campaign.name}</div>
                          <div className="text-xs text-slate-400">
                            {campaign.workspace_id} • {campaign.platform}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(campaign.status)}`}
                          >
                            {campaign.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          ${campaign.daily_budget?.toFixed(2) || "—"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          ${campaign.metrics?.spend?.toFixed(2) || "0.00"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {campaign.metrics?.impressions?.toLocaleString() || "—"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {campaign.metrics?.kpis?.ctr?.toFixed(2) || "—"}%
                        </td>
                        <td className="px-4 py-3 text-right">
                          {campaign.metrics?.conversions || 0}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span
                            className={
                              (campaign.metrics?.kpis?.roas || 0) >= 4
                                ? "text-emerald-400"
                                : (campaign.metrics?.kpis?.roas || 0) >= 2
                                  ? "text-amber-400"
                                  : "text-red-400"
                            }
                          >
                            {campaign.metrics?.kpis?.roas?.toFixed(2) || "—"}x
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex justify-center gap-1">
                            {campaign.status === "ACTIVE" ? (
                              <button
                                onClick={() => handleStatusChange(campaign.id, "PAUSED")}
                                className="px-2 py-1 text-xs bg-amber-600/20 text-amber-400 rounded hover:bg-amber-600/30"
                              >
                                Pause
                              </button>
                            ) : (
                              <button
                                onClick={() => handleStatusChange(campaign.id, "ACTIVE")}
                                className="px-2 py-1 text-xs bg-emerald-600/20 text-emerald-400 rounded hover:bg-emerald-600/30"
                              >
                                Activate
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </Shell>
  );
}
