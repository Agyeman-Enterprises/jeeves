'use client';

import { useEventFeed } from '@/hooks/useEventFeed';

interface EventFeedWidgetProps {
  config: {
    types?: string[];
    limit?: number;
  };
  workspaceId: string;
}

export function EventFeedWidget({ config, workspaceId }: EventFeedWidgetProps) {
  const { types = [], limit = 50 } = config;
  const { events, loading, error } = useEventFeed(
    { workspaceId, types, limit },
    5000
  );

  return (
    <div className="border rounded p-4 h-full flex flex-col">
      <h2 className="font-semibold mb-2">Event Feed</h2>
      <div className="flex-1 overflow-auto space-y-2">
        {loading && <p className="text-sm text-gray-500">Loading events…</p>}
        {error && <p className="text-sm text-red-500">Error: {error.message}</p>}
        {events.map((e: any) => (
          <div key={e.id} className="border-b py-2 text-sm">
            <div className="text-xs text-gray-500">
              {new Date(e.created_at).toLocaleString()}
            </div>
            <div className="font-mono text-sm">{e.event_type}</div>
            {e.payload && (
              <div className="text-xs text-gray-600 mt-1 truncate">
                {typeof e.payload === 'string' ? e.payload : JSON.stringify(e.payload).slice(0, 100)}
              </div>
            )}
          </div>
        ))}
        {events.length === 0 && !loading && (
          <p className="text-sm text-gray-500">No events yet.</p>
        )}
      </div>
    </div>
  );
}

