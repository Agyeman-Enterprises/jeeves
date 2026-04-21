'use client';

import React, { useEffect, useState } from 'react';
import { PredictionWidgetProps } from '@/lib/jarvis/widgets/types';

type SpendData = {
  workspaceId: string;
  horizonDays: number;
  predictedMessageVolume: number;
  predictedCallVolume: number;
  predictedEmailVolume: number;
  confidence: number;
  basis: {
    baselineDays: number;
    avgMessagesPerDay: number;
    avgCallsPerDay: number;
    avgEmailsPerDay: number;
  };
};

interface SpendForecastWidgetProps extends PredictionWidgetProps {
  horizonDays?: number;
}

export const SpendForecastWidget: React.FC<SpendForecastWidgetProps> = ({
  workspaceId,
  config,
  horizonDays: propHorizonDays
}) => {
  const horizonDays = (propHorizonDays || (config?.horizonDays as number)) ?? 7;

  const [data, setData] = useState<SpendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchSpend() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams({
          workspaceId,
          horizonDays: String(horizonDays)
        });

        const res = await fetch(`/api/jarvis/prediction/spend?${params.toString()}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (!json.ok) throw new Error(json.error || 'Unknown error');

        if (!cancelled) setData(json.data as SpendData);
      } catch (err: any) {
        if (!cancelled) {
          console.error('[SpendForecastWidget] fetch error:', err);
          setError(err.message || 'Failed to load data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchSpend();
    const id = setInterval(fetchSpend, 10 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [workspaceId, horizonDays]);

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-950 p-4 text-slate-100 shadow-md">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
          {horizonDays}-Day Volume Forecast
        </h3>
        <span className="text-xs text-slate-500">
          Confidence: {data ? (data.confidence * 100).toFixed(0) : '--'}%
        </span>
      </div>

      {loading && (
        <div className="mt-4 text-sm text-slate-400">
          Calculating forecast…
        </div>
      )}

      {error && !loading && (
        <div className="mt-4 text-xs text-red-400">Error: {error}</div>
      )}

      {!loading && !error && data && (
        <div className="mt-3 space-y-3 text-xs text-slate-300">
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg bg-slate-900/60 p-2">
              <div className="text-slate-500">Messages</div>
              <div className="text-lg font-semibold">
                {Math.round(data.predictedMessageVolume)}
              </div>
              <div className="text-[10px] text-slate-500">
                ~{Math.round(data.basis.avgMessagesPerDay)}/day
              </div>
            </div>
            <div className="rounded-lg bg-slate-900/60 p-2">
              <div className="text-slate-500">Calls</div>
              <div className="text-lg font-semibold">
                {Math.round(data.predictedCallVolume)}
              </div>
              <div className="text-[10px] text-slate-500">
                ~{Math.round(data.basis.avgCallsPerDay)}/day
              </div>
            </div>
            <div className="rounded-lg bg-slate-900/60 p-2">
              <div className="text-slate-500">Emails</div>
              <div className="text-lg font-semibold">
                {Math.round(data.predictedEmailVolume)}
              </div>
              <div className="text-[10px] text-slate-500">
                ~{Math.round(data.basis.avgEmailsPerDay)}/day
              </div>
            </div>
          </div>
          <div className="text-[10px] text-slate-500">
            Baseline window: {data.basis.baselineDays} days
          </div>
        </div>
      )}

      {!loading && !error && !data && (
        <div className="mt-4 text-xs text-slate-500">
          No baseline usage data available yet.
        </div>
      )}
    </div>
  );
};

