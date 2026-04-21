'use client';

import React, { useEffect, useState } from 'react';
import { PredictionWidgetProps } from '@/lib/jarvis/widgets/types';

type FailureData = {
  provider: string;
  channel: string;
  horizonHours: number;
  predictedFailureRate: number;
  confidence: number;
  basis: {
    baselineFailureRate: number;
    lastFailureRate: number;
    sampleDays: number;
  };
};

type LatencyData = {
  provider: string;
  channel: string;
  horizonHours: number;
  predictedP95Ms: number | null;
  confidence: number;
  basis: {
    windowHours: number;
    samples: number;
  };
};

type OutageData = {
  outageProbability: number; // 0–1
  details: {
    predictedFailureRate: number;
    normalizedLatency: number;
  };
};

export const OutageRadarWidget: React.FC<PredictionWidgetProps> = ({
  workspaceId,
  provider = 'ghexit',
  channel = 'sms'
}) => {

  const [data, setData] = useState<OutageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchOutageRisk() {
      try {
        setLoading(true);
        setError(null);

        const paramsCommon = {
          workspaceId,
          provider,
          channel,
          horizonHours: '24'
        };

        const failureRes = await fetch(
          `/api/jarvis/prediction/failures?${new URLSearchParams(
            paramsCommon
          ).toString()}`
        );
        if (!failureRes.ok) throw new Error(`HTTP ${failureRes.status}`);
        const failureJson = await failureRes.json();
        if (!failureJson.ok) throw new Error(failureJson.error || 'Unknown error');

        const failureData = failureJson.data as FailureData;

        const latencyRes = await fetch(
          `/api/jarvis/prediction/latency?${new URLSearchParams(
            paramsCommon
          ).toString()}`
        );
        if (!latencyRes.ok) throw new Error(`HTTP ${latencyRes.status}`);
        const latencyJson = await latencyRes.json();
        if (!latencyJson.ok) throw new Error(latencyJson.error || 'Unknown error');

        const latencyData = latencyJson.data as LatencyData;

        const fr = failureData.predictedFailureRate ?? 0;
        const p95 = latencyData.predictedP95Ms ?? 0;
        const normalizedLatency = Math.min(1, Math.max(0, p95 / 3000)); // 0–3s

        const outageProbability = Math.min(
          1,
          Math.max(0, fr * 0.7 + normalizedLatency * 0.3)
        );

        const result: OutageData = {
          outageProbability,
          details: {
            predictedFailureRate: fr,
            normalizedLatency
          }
        };

        if (!cancelled) setData(result);
      } catch (err: any) {
        if (!cancelled) {
          console.error('[OutageRadarWidget] fetch error:', err);
          setError(err.message || 'Failed to load data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchOutageRisk();
    const id = setInterval(fetchOutageRisk, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [workspaceId, provider, channel]);

  const renderGauge = (prob: number) => {
    const pct = prob * 100;
    let color = 'text-emerald-400 border-emerald-500';
    if (prob > 0.6) color = 'text-red-400 border-red-500';
    else if (prob > 0.3) color = 'text-amber-400 border-amber-500';

    return (
      <div className="flex flex-col items-center">
        <div
          className={`flex h-20 w-20 items-center justify-center rounded-full border-4 ${color} bg-slate-950/70`}
        >
          <span className="text-xl font-semibold">{pct.toFixed(0)}%</span>
        </div>
        <span className="mt-1 text-xs text-slate-400">Outage Risk</span>
      </div>
    );
  };

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-950 p-4 text-slate-100 shadow-md">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
          Outage Probability Radar
        </h3>
        <span className="text-xs text-slate-500">
          {provider}/{channel}
        </span>
      </div>

      {loading && (
        <div className="mt-4 text-sm text-slate-400">
          Assessing outage risk…
        </div>
      )}

      {error && !loading && (
        <div className="mt-4 text-xs text-red-400">
          Error: {error}
        </div>
      )}

      {!loading && !error && data && (
        <div className="mt-3 flex items-center justify-between gap-4">
          {renderGauge(data.outageProbability)}
          <div className="flex-1 space-y-2 text-xs text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Predicted Failure Rate</span>
              <span className="font-medium">
                {(data.details.predictedFailureRate * 100).toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Latency Pressure</span>
              <span className="font-medium">
                {(data.details.normalizedLatency * 100).toFixed(0)}%
              </span>
            </div>
            <div className="mt-2 text-[10px] text-slate-500">
              Outage risk is a weighted mix of predicted failure rate and high-latency
              conditions.
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <div className="mt-4 text-xs text-slate-500">
          Not enough data to estimate outage probability.
        </div>
      )}
    </div>
  );
};

