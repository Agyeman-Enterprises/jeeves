// Metric providers for Situation Room analytics
import { getSupabaseClient } from "@/lib/supabase/client";

export async function getEventCount(
  workspaceId: string,
  types: string[],
  sinceMs: number
): Promise<number> {
  const client = getSupabaseClient();
  const since = new Date(Date.now() - sinceMs).toISOString();

  const { data, error } = await client
    .from('jarvis_events')
    .select('id')
    .eq('workspace_id', workspaceId)
    .gte('created_at', since)
    .in('event_type', types) as any;

  if (error) {
    console.error('Failed to get event count:', error);
    return 0;
  }

  return data?.length ?? 0;
}

export async function getMetricValue(
  workspaceId: string,
  metric: string
): Promise<number> {
  switch (metric) {
    case 'commands_last_24h':
      return getEventCount(workspaceId, ['jarvis.command.completed'], 24 * 3600 * 1000);
    case 'errors_last_24h':
      return getEventCount(workspaceId, ['jarvis.error.logged', 'jarvis.command.failed'], 24 * 3600 * 1000);
    case 'commands_last_hour':
      return getEventCount(workspaceId, ['jarvis.command.completed'], 3600 * 1000);
    default:
      return 0;
  }
}

