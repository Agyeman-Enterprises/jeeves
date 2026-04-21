'use client';

import React, { useEffect, useState } from 'react';
import { PredictionWidgetProps } from '@/lib/jarvis/widgets/types';

type RoutingData = {
  provider: string;
  channel: string;
  score: number; // 0–1
  factors: {
    currentHealthScore: number | null;
    predictedFailureRate: number | null;
    predictedP95LatencyMs: number | null;
  };
};

export const RoutingScoreWidget: React.FC<PredictionWidgetProps> = ({
  workspaceId,
  config,
  provider: propProvider,
  channel: propChannel
}) => {
  const provider = (propProvider || (config?.provider as string)) ?? 'ghexit';
  const channel = (propChannel || (config?.channel as string)) ?? 'sms';

  const [data, setData] = useState<RoutingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchRouting() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams({
          workspaceId,
          provider,
          channel
        });

        const res = await fetch(`/api/jarvis/prediction/routing?${params.toString()}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (!json.ok) throw new Error(json.error || 'Unknown error');

        if (!cancelled) setData(json.data as RoutingData);
      } catch (err: any) {
        if (!cancelled) {
          console.error('[RoutingScoreWidget] fetch error:', err);
          setError(err.message || 'Failed to load data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchRouting();
    const id = setInterval(fetchRouting, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [workspaceId, provider, channel]);

  const renderScoreBar = (score: number) => {
    const pct = score * 100;
    let color = 'bg-emerald-500';
    if (score < 0.3) color = 'bg-red-500';
    else if (score < 0.7) color = 'bg-amber-500';

    return (
      <div className="mt-2">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Routing Score</span>
          <span className="font-medium text-slate-100">{pct.toFixed(0)}%</span>
        </div>
        <div className="mt-1 h-2 w-full rounded-full bg-slate-800">
          <div
            className={`h-2 rounded-full ${color} transition-all`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-950 p-4 text-slate-100 shadow-md">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
          Routing Recommendation
        </h3>
        <span className="text-xs text-slate-500">
          {provider}/{channel}
        </span>
      </div>

      {loading && (
        <div className="mt-4 text-sm text-slate-400">
          Computing routing score…
        </div>
      )}

      {error && !loading && (
        <div className="mt-4 text-xs text-red-400">
          Error: {error}
        </div>
      )}

      {!loading && !error && data && (
        <div className="mt-3 space-y-3">
          {renderScoreBar(data.score)}
          <div className="grid grid-cols-3 gap-3 text-xs text-slate-400">
            <div>
              <div className="text-slate-500">Current Health</div>
              <div className="font-medium">
                {data.factors.currentHealthScore != null
                  ? (data.factors.currentHealthScore * 100).toFixed(0) + '%'
                  : '—'}
              </div>
            </div>
            <div>
              <div className="text-slate-500">Predicted Failure</div>
              <div className="font-medium">
                {data.factors.predictedFailureRate != null
                  ? (data.factors.predictedFailureRate * 100).toFixed(2) + '%'
                  : '—'}
              </div>
            </div>
            <div>
              <div className="text-slate-500">Predicted P95</div>
              <div className="font-medium">
                {data.factors.predictedP95LatencyMs != null
                  ? `${Math.round(data.factors.predictedP95LatencyMs)} ms`
                  : '—'}
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <div className="mt-4 text-xs text-slate-500">
          No routing data available yet.
        </div>
      )}
    </div>
  );
};

