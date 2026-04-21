// Stripe event normalization
import type { NormalizedProviderEvent } from '../types';

export function normalizeStripe(payload: any): NormalizedProviderEvent {
  return {
    provider: 'stripe',
    type: payload.type || 'unknown',
    subjectId: payload.id || payload.data?.object?.id,
    workspaceId: payload.workspaceId || payload.metadata?.workspaceId || '',
    userId: payload.userId || payload.metadata?.userId || '',
    payload: payload.data || payload,
  };
}

