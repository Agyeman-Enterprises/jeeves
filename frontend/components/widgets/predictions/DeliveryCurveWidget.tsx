'use client';

import React, { useEffect, useState } from 'react';
import { PredictionWidgetProps } from '@/lib/jarvis/widgets/types';

type LatencyPoint = {
  horizonHours: number;
  p95: number | null;
};

export const DeliveryCurveWidget: React.FC<PredictionWidgetProps> = ({
  workspaceId,
  provider = 'ghexit',
  channel = 'sms'
}) => {

  const [points, setPoints] = useState<LatencyPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const horizons = [1, 4, 12, 24];

  useEffect(() => {
    let cancelled = false;

    async function fetchAll() {
      try {
        setLoading(true);
        setError(null);
        const newPoints: LatencyPoint[] = [];

        for (const h of horizons) {
          const params = new URLSearchParams({
            workspaceId,
            provider,
            channel,
            horizonHours: String(h)
          });
          const res = await fetch(`/api/jarvis/prediction/latency?${params.toString()}`);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const json = await res.json();
          if (!json.ok) throw new Error(json.error || 'Unknown error');

          const d = json.data as {
            horizonHours: number;
            predictedP95Ms: number | null;
          };

          newPoints.push({
            horizonHours: h,
            p95: d.predictedP95Ms
          });
        }

        if (!cancelled) {
          setPoints(newPoints);
        }
      } catch (err: any) {
        if (!cancelled) {
          console.error('[DeliveryCurveWidget] fetch error:', err);
          setError(err.message || 'Failed to load data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchAll();
    const id = setInterval(fetchAll, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [workspaceId, provider, channel]);

  const maxP95 = Math.max(
    ...points
      .map((p) => (p.p95 ?? 0))
      .concat([0])
  );

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-950 p-4 text-slate-100 shadow-md">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
          Expected Delivery Time Curve
        </h3>
        <span className="text-xs text-slate-500">
          {provider}/{channel}
        </span>
      </div>

      {loading && (
        <div className="mt-4 text-sm text-slate-400">
          Building latency curve…
        </div>
      )}

      {error && !loading && (
        <div className="mt-4 text-xs text-red-400">
          Error: {error}
        </div>
      )}

      {!loading && !error && points.length > 0 && (
        <div className="mt-3 space-y-3">
          <div className="flex items-end gap-2">
            {points.map((p) => {
              const value = p.p95 ?? 0;
              const ratio = maxP95 > 0 ? value / maxP95 : 0;
              const height = `${Math.max(10, ratio * 100)}%`;

              return (
                <div key={p.horizonHours} className="flex-1 text-center text-xs">
                  <div className="mb-1 flex h-24 items-end justify-center">
                    <div
                      className="w-4 rounded-t-md bg-sky-500"
                      style={{ height }}
                      title={p.p95 != null ? `${Math.round(p.p95)} ms` : 'No data'}
                    />
                  </div>
                  <div className="text-slate-400">{p.horizonHours}h</div>
                  <div className="text-[10px] text-slate-500">
                    {p.p95 != null ? `${Math.round(p.p95)} ms` : '—'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && !error && points.length === 0 && (
        <div className="mt-4 text-xs text-slate-500">
          No latency data available yet.
        </div>
      )}
    </div>
  );
};

