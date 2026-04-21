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

export const CarrierStabilityWidget: React.FC<PredictionWidgetProps> = ({
  workspaceId,
  config,
  provider: propProvider,
  channel: propChannel
}) => {
  const provider = (propProvider || (config?.provider as string)) ?? 'ghexit';
  const channel = (propChannel || (config?.channel as string)) ?? 'sms';

  const [data, setData] = useState<FailureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchFailure() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams({
          workspaceId,
          provider,
          channel,
          horizonHours: String(24)
        });

        const res = await fetch(`/api/jarvis/prediction/failures?${params.toString()}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (!json.ok) throw new Error(json.error || 'Unknown error');

        if (!cancelled) setData(json.data as FailureData);
      } catch (err: any) {
        if (!cancelled) {
          console.error('[CarrierStabilityWidget] fetch error:', err);
          setError(err.message || 'Failed to load data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchFailure();
    const id = setInterval(fetchFailure, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [workspaceId, provider, channel]);

  const formatPercent = (v: number) => `${(v * 100).toFixed(2)}%`;

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-950 p-4 text-slate-100 shadow-md">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
          Carrier Stability Forecast
        </h3>
        <span className="text-xs text-slate-500">
          {provider}/{channel}
        </span>
      </div>

      {loading && (
        <div className="mt-4 text-sm text-slate-400">
          Evaluating stability…
        </div>
      )}

      {error && !loading && (
        <div className="mt-4 text-xs text-red-400">
          Error loading forecast: {error}
        </div>
      )}

      {!loading && !error && data && (
        <div className="mt-3 space-y-3">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-semibold">
              {formatPercent(1 - data.predictedFailureRate)}
            </span>
            <span className="text-xs text-slate-500">predicted success rate</span>
          </div>
          <div className="grid grid-cols-3 gap-3 text-xs text-slate-400">
            <div>
              <div className="text-slate-500">Predicted Failure</div>
              <div className="font-medium">
                {formatPercent(data.predictedFailureRate)}
              </div>
            </div>
            <div>
              <div className="text-slate-500">Baseline</div>
              <div className="font-medium">
                {formatPercent(data.basis.baselineFailureRate)}
              </div>
            </div>
            <div>
              <div className="text-slate-500">Last Day</div>
              <div className="font-medium">
                {formatPercent(data.basis.lastFailureRate)}
              </div>
            </div>
            <div>
              <div className="text-slate-500">Confidence</div>
              <div className="font-medium">
                {(data.confidence * 100).toFixed(0)}%
              </div>
            </div>
            <div>
              <div className="text-slate-500">Sample Days</div>
              <div className="font-medium">
                {data.basis.sampleDays}
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <div className="mt-4 text-xs text-slate-500">
          No failure stats available yet.
        </div>
      )}
    </div>
  );
};

