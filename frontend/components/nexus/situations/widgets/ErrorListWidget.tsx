'use client';

import { useEventFeed } from '@/hooks/useEventFeed';

interface ErrorListWidgetProps {
  config: {
    types?: string[];
    limit?: number;
  };
  workspaceId: string;
}

export function ErrorListWidget({ config, workspaceId }: ErrorListWidgetProps) {
  const { types = ['jarvis.error.logged'], limit = 20 } = config;
  const { events, loading, error } = useEventFeed(
    { workspaceId, types, limit },
    5000
  );

  const errorEvents = events.filter((e: any) => 
    e.event_type === 'jarvis.error.logged' || 
    e.event_type === 'jarvis.command.failed'
  );

  return (
    <div className="border rounded p-4 h-full flex flex-col">
      <h2 className="font-semibold mb-2 text-red-600">Recent Errors</h2>
      <div className="flex-1 overflow-auto space-y-2">
        {loading && <p className="text-sm text-gray-500">Loading errors…</p>}
        {error && <p className="text-sm text-red-500">Error: {error.message}</p>}
        {errorEvents.map((e: any) => (
          <div key={e.id} className="border-l-4 border-red-500 pl-3 py-2 text-sm">
            <div className="text-xs text-gray-500">
              {new Date(e.created_at).toLocaleString()}
            </div>
            <div className="font-semibold text-red-700">{e.event_type}</div>
            {e.payload?.message && (
              <div className="text-xs text-gray-700 mt-1">{e.payload.message}</div>
            )}
            {e.payload?.errorMessage && (
              <div className="text-xs text-gray-700 mt-1">{e.payload.errorMessage}</div>
            )}
          </div>
        ))}
        {errorEvents.length === 0 && !loading && (
          <p className="text-sm text-gray-500">No errors in the last period.</p>
        )}
      </div>
    </div>
  );
}

