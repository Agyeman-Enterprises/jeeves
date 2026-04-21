'use client';

import React, { useEffect, useState } from 'react';
import { PredictionWidgetProps } from '@/lib/jarvis/widgets/types';

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

interface LatencyForecastWidgetProps extends PredictionWidgetProps {
  horizonHours?: number;
}

export const LatencyForecastWidget: React.FC<LatencyForecastWidgetProps> = ({
  workspaceId,
  config,
  provider: propProvider,
  channel: propChannel,
  horizonHours: propHorizonHours
}) => {
  const provider = (propProvider || (config?.provider as string)) ?? 'ghexit';
  const channel = (propChannel || (config?.channel as string)) ?? 'sms';
  const horizonHours = (propHorizonHours || (config?.horizonHours as number)) ?? 24;

  const [data, setData] = useState<LatencyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchLatency() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams({
          workspaceId,
          provider,
          channel,
          horizonHours: String(horizonHours)
        });

        const res = await fetch(`/api/jarvis/prediction/latency?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const json = await res.json();
        if (!json.ok) throw new Error(json.error || 'Unknown error');

        if (!cancelled) {
          setData(json.data as LatencyData);
        }
      } catch (err: any) {
        if (!cancelled) {
          console.error('[LatencyForecastWidget] fetch error:', err);
          setError(err.message || 'Failed to load data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchLatency();

    // Optional refresh interval (5 minutes)
    const id = setInterval(fetchLatency, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [workspaceId, provider, channel, horizonHours]);

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-950 p-4 text-slate-100 shadow-md">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
          Predicted Latency
        </h3>
        <span className="text-xs text-slate-500">
          {provider}/{channel}
        </span>
      </div>

      {loading && (
        <div className="mt-4 text-sm text-slate-400">Loading latency forecast…</div>
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
              {data.predictedP95Ms != null ? `${Math.round(data.predictedP95Ms)} ms` : '—'}
            </span>
            <span className="text-xs text-slate-500">
              P95 over next {data.horizonHours}h
            </span>
          </div>
          <div className="flex gap-4 text-xs text-slate-400">
            <div>
              <div className="text-slate-500">Confidence</div>
              <div className="font-medium">
                {(data.confidence * 100).toFixed(0)}%
              </div>
            </div>
            <div>
              <div className="text-slate-500">Window</div>
              <div className="font-medium">{data.basis.windowHours}h</div>
            </div>
            <div>
              <div className="text-slate-500">Samples</div>
              <div className="font-medium">{data.basis.samples}</div>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <div className="mt-4 text-xs text-slate-500">
          No latency data available yet.
        </div>
      )}
    </div>
  );
};

