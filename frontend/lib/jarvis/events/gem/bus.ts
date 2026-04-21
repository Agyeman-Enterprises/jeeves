// src/lib/jarvis/events/bus.ts
import { getSupabaseClient } from "@/lib/supabase/client";
import type { Database } from "@/lib/supabase/types";
import { JarvisEventEnvelope, JarvisEventType } from "./types";

interface HandlerOptions {
  maxAttempts?: number;      // default 3
  retryDelayMs?: number;     // default 5000 ms
}

interface RegisteredHandler {
  key: string;
  fn: (event: JarvisEventEnvelope) => Promise<void>;
  options: Required<HandlerOptions>;
}

const handlers: RegisteredHandler[] = [];

/**
 * Register a durable handler.
 */
export function registerHandler(
  key: string,
  options: HandlerOptions,
  fn: (event: JarvisEventEnvelope) => Promise<void>
) {
  handlers.push({
    key,
    fn,
    options: {
      maxAttempts: options.maxAttempts ?? 3,
      retryDelayMs: options.retryDelayMs ?? 5000,
    }
  });
}

/**
 * Emits an event and schedules delivery for all registered handlers.
 */
export async function emitEvent<T extends JarvisEventType>(
  event: JarvisEventEnvelope<T>
): Promise<JarvisEventEnvelope<T>> {
  const now = new Date().toISOString();
  const client = getSupabaseClient();

  // 1. Persist event
  const result = await client
    .from('jarvis_events')
    .insert({
      workspace_id: event.workspaceId,
      user_id: event.userId,
      event_type: event.type,
      source: event.source,
      subject_id: event.subjectId,
      correlation_id: event.correlationId,
      causation_id: event.causationId,
      payload: event.payload,
      status: 'stored',
      created_at: now,
      updated_at: now
    } as any)
    .select('*')
    .single();

  const { data, error } = result as { data: any; error: any };

  if (error || !data) {
    console.error('emitEvent DB error', error);
    throw error || new Error('Failed to insert event');
  }

  const savedEvent: JarvisEventEnvelope<T> = {
    ...event,
    id: data.id,
    createdAt: data.created_at,
  };

  // 2. Create delivery rows for each handler
  const clientAny = client as any;
  for (const h of handlers) {
    try {
      await clientAny
        .from('jarvis_event_deliveries')
        .insert({
          workspace_id: event.workspaceId,
          user_id: event.userId,
          event_id: data.id,
          handler_key: h.key,
          status: 'pending',
          attempts: 0,
          created_at: now,
          updated_at: now
        });
    } catch (insertErr) {
      console.error('Failed to create delivery row:', insertErr);
    }
  }

  return savedEvent;
}

/**
 * Attempt delivery for a single handler.
 */
async function attemptDelivery(handler: RegisteredHandler, event: JarvisEventEnvelope, deliveryRow: any) {
  const { key, fn, options } = handler;
  const client = getSupabaseClient() as any;

  try {
    await fn(event);

    // mark success
    try {
      await client
        .from('jarvis_event_deliveries')
        .update({
          status: 'success',
          attempts: deliveryRow.attempts + 1,
          updated_at: new Date().toISOString()
        })
        .eq('id', deliveryRow.id);
    } catch (updateErr) {
      console.error('Failed to update delivery status to success:', updateErr);
    }

  } catch (err: any) {
    const now = new Date().toISOString();
    const nextAttempt = deliveryRow.attempts + 1;

    const failedPermanently = nextAttempt >= options.maxAttempts;

    try {
      await client
        .from('jarvis_event_deliveries')
        .update({
          status: failedPermanently ? 'failed' : 'pending',
          attempts: nextAttempt,
          last_error: err?.message ?? String(err),
          updated_at: now
        })
        .eq('id', deliveryRow.id);
    } catch (updateErr) {
      console.error('Failed to update delivery status:', updateErr);
    }

    if (!failedPermanently) {
      // optional retry delay (handled by polling loop)
    }
  }
}

/**
 * Polls pending deliveries and attempts dispatch.
 * v0: runs every 5 seconds.
 */
async function pollPendingDeliveries() {
  try {
    const client = getSupabaseClient();
    const { data: deliveries } = await client
      .from('jarvis_event_deliveries')
      .select('*, jarvis_events(*)')
      .eq('status', 'pending')
      .limit(20) as any;

    if (!deliveries || deliveries.length === 0) return;

    for (const d of deliveries) {
      const handler = handlers.find(h => h.key === d.handler_key);
      if (!handler) continue;

      const eventData = d.jarvis_events;
      const event: JarvisEventEnvelope = {
        id: d.event_id,
        type: eventData.event_type,
        source: eventData.source,
        subjectId: eventData.subject_id,
        correlationId: eventData.correlation_id,
        causationId: eventData.causation_id,
        workspaceId: eventData.workspace_id,
        userId: eventData.user_id,
        payload: eventData.payload,
        createdAt: eventData.created_at,
      };

      await attemptDelivery(handler, event, d);
    }
  } catch (err) {
    console.error('GEM dispatcher error:', err);
  }
}

// Start polling loop (only in server environment)
if (typeof window === 'undefined') {
  setInterval(pollPendingDeliveries, 5000);
}

