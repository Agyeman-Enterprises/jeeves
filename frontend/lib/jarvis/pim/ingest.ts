import { supabaseServer } from '@/lib/supabase/server';

// Adjust this type to match your actual jarvis_events schema:
type JarvisEventRow = {
  id: string;
  workspace_id: string;
  event_type: string;
  created_at: string;
  payload: any;
};

function parseProviderEvent(row: JarvisEventRow) {
  // event_type shape: external.provider.ghexit.<channel>.<eventType>
  const parts = row.event_type.split('.');
  const provider = parts[2] ?? 'ghexit';
  const channel = (parts[3] ?? 'other') as string;
  const eventType = parts[4] ?? 'unknown';

  const payload = row.payload ?? {};

  // latency: prefer explicit latencyMs in payload; else infer if timestamps exist
  let latencyMs: number | null = null;
  if (typeof payload.latencyMs === 'number') {
    latencyMs = payload.latencyMs;
  } else if (payload.sentAt && payload.deliveredAt) {
    const sent = new Date(payload.sentAt).getTime();
    const delivered = new Date(payload.deliveredAt).getTime();
    if (!Number.isNaN(sent) && !Number.isNaN(delivered) && delivered >= sent) {
      latencyMs = delivered - sent;
    }
  }

  // basic error normalization
  const errorCode: string | null = payload.errorCode ?? null;
  let errorGroup: string | null = null;

  if (eventType === 'failed' || errorCode) {
    const code = (errorCode ?? '').toLowerCase();
    if (code.includes('auth') || code.includes('401') || code.includes('403')) {
      errorGroup = 'auth';
    } else if (code.includes('timeout') || code.includes('network')) {
      errorGroup = 'network';
    } else if (code.includes('throttle') || code.includes('rate') || code.includes('limit')) {
      errorGroup = 'throttle';
    } else if (code.includes('remote') || code.includes('carrier')) {
      errorGroup = 'remote';
    } else if (code.includes('config') || code.includes('invalid')) {
      errorGroup = 'config';
    } else {
      errorGroup = 'unknown';
    }
  }

  const routing_path = payload.routingPath ?? null;
  const metadata = payload.metadata ?? payload;

  return {
    source_event_id: row.id,
    workspace_id: row.workspace_id,
    provider,
    channel,
    event_type: eventType,
    occurred_at: row.created_at,
    latency_ms: latencyMs,
    error_code: errorCode,
    error_group: errorGroup,
    routing_path,
    metadata
  };
}

/**
 * IT-10A:
 * Ingest recent Ghexit-related GEM events into jarvis_pim_provider_events.
 * This function is intended to be called periodically (e.g., via a cron route).
 *
 * Strategy:
 * - Process events in a recent time window (e.g., last 10 minutes).
 * - Use source_event_id UNIQUE constraint to make the operation idempotent.
 */
export async function ingestRecentProviderEvents(windowMinutes = 10): Promise<{
  processed: number;
  inserted: number;
}> {
  const supabase = supabaseServer;

  const since = new Date();
  since.setMinutes(since.getMinutes() - windowMinutes);

  const { data, error } = await ((supabase as any)
    .from('jarvis_events')
    .select('id, workspace_id, event_type, created_at, payload')
    .like('event_type', 'external.provider.ghexit.%')
    .gte('created_at', since.toISOString()));

  if (error) {
    console.error('[PIM] ingestRecentProviderEvents query error:', error);
    throw error;
  }

  const rows = (data ?? []) as JarvisEventRow[];
  if (!rows.length) {
    return { processed: 0, inserted: 0 };
  }

  const normalized = rows.map(parseProviderEvent);

  const { error: insertError } = await ((supabase as any)
    .from('jarvis_pim_provider_events')
    .upsert(normalized, { onConflict: 'source_event_id' }));

  if (insertError) {
    console.error('[PIM] ingestRecentProviderEvents insert error:', insertError);
    throw insertError;
  }

  return { processed: rows.length, inserted: normalized.length };
}

