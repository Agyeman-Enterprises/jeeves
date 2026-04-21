// src/lib/jarvis/events/feed.ts

export interface EventFeedFilter {
  workspaceId: string;
  types?: string[];
  since?: string;
  subjectId?: string;
  correlationId?: string;
  limit?: number;
}

export async function fetchEventFeed(filters: EventFeedFilter) {
  const params = new URLSearchParams();
  params.set('workspaceId', filters.workspaceId);
  if (filters.types?.length) {
    params.set('types', filters.types.join(','));
  }
  if (filters.since) {
    params.set('since', filters.since);
  }
  if (filters.subjectId) {
    params.set('subjectId', filters.subjectId);
  }
  if (filters.correlationId) {
    params.set('correlationId', filters.correlationId);
  }
  if (filters.limit) {
    params.set('limit', String(filters.limit));
  }

  const res = await fetch(`/api/jarvis/events?${params.toString()}`);
  if (!res.ok) {
    throw new Error('Failed to fetch event feed');
  }
  const json = await res.json();
  return json.events;
}

