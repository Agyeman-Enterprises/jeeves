// AdAI event normalization - converts Meta/internal events to GEM format
import type { NormalizedProviderEvent } from '../types';

/**
 * Meta Marketing API webhook event types
 * @see https://developers.facebook.com/docs/marketing-api/webhooks
 */
export type MetaAdEventType =
  | 'ad_account_update'
  | 'campaign_update'
  | 'adset_update'
  | 'ad_update'
  | 'leadgen'
  | 'ad_creative_update';

/**
 * Internal AdAI event types (from Cloudflare Worker)
 */
export type AdAIInternalEventType =
  | 'adai.sync.started'
  | 'adai.sync.completed'
  | 'adai.sync.failed'
  | 'adai.decision.proposed'
  | 'adai.decision.approved'
  | 'adai.decision.rejected'
  | 'adai.decision.executed'
  | 'adai.decision.failed'
  | 'adai.decision.rolled_back'
  | 'adai.approval.required'
  | 'adai.anomaly.detected'
  | 'adai.budget.exceeded'
  | 'adai.token.expiring'
  | 'adai.token.expired'
  | 'adai.experiment.started'
  | 'adai.experiment.completed'
  | 'adai.experiment.winner'
  | 'adai.run.started'
  | 'adai.run.completed'
  | 'adai.run.failed';

export type AdAIEventType = MetaAdEventType | AdAIInternalEventType;

interface MetaWebhookEntry {
  id: string;           // Ad account ID
  time: number;         // Unix timestamp
  changes: Array<{
    field: string;      // 'campaign', 'adset', 'ad', etc.
    value: {
      ad_id?: string;
      adset_id?: string;
      campaign_id?: string;
      account_id?: string;
      [key: string]: any;
    };
  }>;
}

interface MetaWebhookPayload {
  object: 'ad_account';
  entry: MetaWebhookEntry[];
}

interface AdAIInternalPayload {
  eventType: AdAIInternalEventType;
  workspaceId: string;
  userId?: string;
  subjectId?: string;
  data: Record<string, any>;
  timestamp?: string;
}

/**
 * Normalize Meta Marketing API webhook events to GEM format
 */
function normalizeMetaEvent(payload: MetaWebhookPayload): NormalizedProviderEvent[] {
  const events: NormalizedProviderEvent[] = [];

  for (const entry of payload.entry || []) {
    for (const change of entry.changes || []) {
      const eventType = mapMetaFieldToEventType(change.field);
      const subjectId = getSubjectId(change.value);

      events.push({
        provider: 'adai',
        type: eventType,
        subjectId,
        workspaceId: '', // Must be resolved from account_id mapping
        userId: '',       // System event
        payload: {
          platform: 'meta',
          accountId: entry.id,
          field: change.field,
          value: change.value,
          timestamp: new Date(entry.time * 1000).toISOString(),
        },
      });
    }
  }

  return events;
}

function mapMetaFieldToEventType(field: string): string {
  const mapping: Record<string, string> = {
    campaign: 'campaign_update',
    adset: 'adset_update',
    ad: 'ad_update',
    account: 'ad_account_update',
    leadgen: 'leadgen',
    creative: 'ad_creative_update',
  };
  return mapping[field] || `meta.${field}.update`;
}

function getSubjectId(value: Record<string, any>): string | undefined {
  return value.ad_id || value.adset_id || value.campaign_id || value.account_id;
}

/**
 * Normalize internal AdAI events (from Cloudflare Worker)
 */
function normalizeInternalEvent(payload: AdAIInternalPayload): NormalizedProviderEvent {
  return {
    provider: 'adai',
    type: payload.eventType,
    subjectId: payload.subjectId,
    workspaceId: payload.workspaceId,
    userId: payload.userId || 'system',
    payload: {
      ...payload.data,
      timestamp: payload.timestamp || new Date().toISOString(),
    },
  };
}

/**
 * Main normalization function - detects event source and normalizes accordingly
 */
export function normalizeAdAI(rawPayload: any): NormalizedProviderEvent {
  // Check if this is a Meta webhook (has 'object' and 'entry' fields)
  if (rawPayload.object === 'ad_account' && Array.isArray(rawPayload.entry)) {
    const events = normalizeMetaEvent(rawPayload as MetaWebhookPayload);
    // Return first event (webhook handler should process all)
    return events[0] || {
      provider: 'adai',
      type: 'unknown',
      workspaceId: '',
      userId: '',
      payload: rawPayload,
    };
  }

  // Check if this is an internal AdAI event
  if (rawPayload.eventType && rawPayload.workspaceId) {
    return normalizeInternalEvent(rawPayload as AdAIInternalPayload);
  }

  // Fallback for unknown format
  return {
    provider: 'adai',
    type: rawPayload.type || rawPayload.eventType || 'unknown',
    subjectId: rawPayload.id || rawPayload.subjectId,
    workspaceId: rawPayload.workspaceId || '',
    userId: rawPayload.userId || '',
    payload: rawPayload,
  };
}

/**
 * Batch normalize Meta events (returns all events from a single webhook)
 * Use this in webhook handler to process all changes in a single webhook call
 */
export function normalizeMetaEventBatch(rawPayload: any): NormalizedProviderEvent[] {
  if (rawPayload.object === 'ad_account' && Array.isArray(rawPayload.entry)) {
    return normalizeMetaEvent(rawPayload as MetaWebhookPayload);
  }
  // Single event - wrap in array
  return [normalizeAdAI(rawPayload)];
}
