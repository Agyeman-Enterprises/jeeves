"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

interface RemediationItem {
  cardCode: string;
  severity: "critical" | "high" | "medium";
  title: string;
  whyItMatters: string;
  whatsMissing: string;
  vouchsafeWillDo: string;
  userMustDo: string;
  autoFixAvailable: boolean;
  estimatedMinutes: number;
  status: "OPEN" | "AUTO_FIXED" | "MANUAL_REQUIRED" | "RESOLVED";
  firstDetected: string;
  lastUpdated: string;
}

interface ReadinessReport {
  status: "SHIP" | "WARN" | "BLOCKED" | "ERROR";
  timestamp: string;
  blockers: string[];
  warnings: string[];
  remediationItems: RemediationItem[];
  checks: Array<{
    name: string;
    status: string;
    message: string;
  }>;
}

export default function RemediationPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [report, setReport] = useState<ReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [applyingFixes, setApplyingFixes] = useState(false);

  useEffect(() => {
    // Load readiness report
    fetch("/api/vouchsafe/readiness")
      .then((res) => res.json())
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load readiness report:", err);
        setLoading(false);
      });
  }, []);

  const handleApplyFixes = async () => {
    setApplyingFixes(true);
    try {
      const response = await fetch("/api/vouchsafe/apply-fixes", {
        method: "POST",
      });
      const result = await response.json();
      
      if (result.success) {
        // Reload report
        const updated = await fetch("/api/vouchsafe/readiness").then((res) =>
          res.json()
        );
        setReport(updated);
      } else {
        alert(`Failed to apply fixes: ${result.error}`);
      }
    } catch (error) {
      console.error("Failed to apply fixes:", error);
      alert("Failed to apply fixes. Please try again.");
    } finally {
      setApplyingFixes(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#120122] to-[#1a0132] p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-white">Loading remediation data...</div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#120122] to-[#1a0132] p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-purple-900/40 backdrop-blur-lg rounded-lg p-6 text-white">
            <h1 className="text-2xl font-bold mb-4">Remediation Not Available</h1>
            <p>No readiness report found. Run `npx vouchsafe prod-check` first.</p>
          </div>
        </div>
      </div>
    );
  }

  const totalItems = report.remediationItems.length;
  const autoFixable = report.remediationItems.filter(
    (item) => item.autoFixAvailable && item.status === "OPEN"
  ).length;
  const resolved = report.remediationItems.filter(
    (item) => item.status === "RESOLVED"
  ).length;
  const open = report.remediationItems.filter(
    (item) => item.status === "OPEN"
  ).length;
  const estimatedMinutes = report.remediationItems
    .filter((item) => item.status === "OPEN")
    .reduce((sum, item) => sum + item.estimatedMinutes, 0);

  const progressPercentage =
    totalItems > 0 ? (resolved / totalItems) * 100 : 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#120122] to-[#1a0132] p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-purple-900/40 backdrop-blur-lg rounded-lg p-6 text-white">
          <h1 className="text-3xl font-bold mb-2">Vouchsafe Remediation</h1>
          <p className="text-purple-200">Project: {projectId}</p>
        </div>

        {/* Status Card */}
        <div className="bg-purple-900/40 backdrop-blur-lg rounded-lg p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold mb-2">
                Status:{" "}
                <span
                  className={
                    report.status === "SHIP"
                      ? "text-green-400"
                      : report.status === "BLOCKED"
                      ? "text-red-400"
                      : "text-yellow-400"
                  }
                >
                  {report.status}
                </span>
              </h2>
              <p className="text-purple-200">
                Last checked: {new Date(report.timestamp).toLocaleString()}
              </p>
            </div>
            {autoFixable > 0 && (
              <button
                onClick={handleApplyFixes}
                disabled={applyingFixes}
                className="bg-[#FFC300] text-black px-6 py-3 rounded-lg font-semibold hover:bg-[#FFD700] transition-colors disabled:opacity-50"
              >
                {applyingFixes ? "Applying..." : `Apply ${autoFixable} Auto-Fixes`}
              </button>
            )}
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span>Progress to SHIP</span>
              <span>{Math.round(progressPercentage)}%</span>
            </div>
            <div className="w-full bg-purple-800/50 rounded-full h-3">
              <div
                className="bg-[#FFC300] h-3 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 mt-6">
            <div>
              <div className="text-2xl font-bold">{totalItems}</div>
              <div className="text-sm text-purple-200">Total Issues</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-400">{resolved}</div>
              <div className="text-sm text-purple-200">Resolved</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-400">
                {autoFixable}
              </div>
              <div className="text-sm text-purple-200">Auto-Fixable</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-400">{open}</div>
              <div className="text-sm text-purple-200">Open</div>
            </div>
          </div>

          {estimatedMinutes > 0 && (
            <div className="mt-4 p-4 bg-purple-800/30 rounded-lg">
              <div className="text-lg font-semibold">
                ⏳ Estimated Time to SHIP: ~{estimatedMinutes} minutes
              </div>
            </div>
          )}
        </div>

        {/* Remediation Items */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white">Remediation Items</h2>
          {report.remediationItems.map((item) => (
            <div
              key={item.cardCode}
              className="bg-purple-900/40 backdrop-blur-lg rounded-lg p-6 text-white"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl font-bold">{item.cardCode}</span>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        item.severity === "critical"
                          ? "bg-red-500/20 text-red-300"
                          : item.severity === "high"
                          ? "bg-orange-500/20 text-orange-300"
                          : "bg-yellow-500/20 text-yellow-300"
                      }`}
                    >
                      {item.severity.toUpperCase()}
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full text-sm ${
                        item.status === "RESOLVED"
                          ? "bg-green-500/20 text-green-300"
                          : item.status === "AUTO_FIXED"
                          ? "bg-blue-500/20 text-blue-300"
                          : "bg-gray-500/20 text-gray-300"
                      }`}
                    >
                      {item.status}
                    </span>
                    {item.autoFixAvailable && (
                      <span className="px-3 py-1 rounded-full text-sm bg-[#FFC300]/20 text-[#FFC300]">
                        🤖 Auto-Fix Available
                      </span>
                    )}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                  <p className="text-purple-200 text-sm">
                    Estimated: ~{item.estimatedMinutes} minutes
                  </p>
                </div>
              </div>

              <div className="space-y-3 mt-4">
                <div>
                  <h4 className="font-semibold mb-1">Why This Matters</h4>
                  <p className="text-purple-200 text-sm">{item.whyItMatters}</p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">What's Missing</h4>
                  <p className="text-purple-200 text-sm">{item.whatsMissing}</p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">What Vouchsafe Will Do</h4>
                  <p className="text-purple-200 text-sm">
                    {item.vouchsafeWillDo}
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">What You Must Do</h4>
                  <p className="text-purple-200 text-sm">{item.userMustDo}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

