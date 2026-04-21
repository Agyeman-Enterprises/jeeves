// src/hooks/useEventFeed.ts
import { useEffect, useState } from 'react';
import { fetchEventFeed, EventFeedFilter } from '@/lib/jarvis/events/gem/feed';

export function useEventFeed(filters: EventFeedFilter, pollMs = 5000) {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const data = await fetchEventFeed(filters);
        if (!cancelled) {
          setEvents(data);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const id = setInterval(load, pollMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [JSON.stringify(filters), pollMs]);

  return { events, loading, error };
}

