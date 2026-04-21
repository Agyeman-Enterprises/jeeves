'use client';

import { useEffect, useState } from 'react';

interface MetricCardWidgetProps {
  config: {
    metric?: string;
  };
  workspaceId: string;
}

export function MetricCardWidget({ config, workspaceId }: MetricCardWidgetProps) {
  const { metric = 'commands_last_24h' } = config;
  const [value, setValue] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMetric() {
      try {
        const res = await fetch(`/api/nexus/situations/metrics?workspaceId=${workspaceId}&metric=${metric}`);
        if (res.ok) {
          const data = await res.json();
          setValue(data.value);
        }
      } catch (err) {
        console.error('Failed to fetch metric:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchMetric();
    const interval = setInterval(fetchMetric, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [workspaceId, metric]);

  return (
    <div className="border rounded p-4 h-full flex flex-col">
      <h2 className="font-semibold mb-2 text-sm text-gray-600">Command Volume (24h)</h2>
      <div className="flex-1 flex items-center justify-center">
        {loading ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : (
          <div className="text-3xl font-bold">{value ?? 0}</div>
        )}
      </div>
    </div>
  );
}

