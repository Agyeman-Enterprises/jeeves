// Resend event normalization
import type { NormalizedProviderEvent } from '../types';

export function normalizeResend(payload: any): NormalizedProviderEvent {
  return {
    provider: 'resend',
    type: payload.type || payload.event || 'unknown',
    subjectId: payload.data?.email_id || payload.id,
    workspaceId: payload.workspaceId || payload.metadata?.workspaceId || '',
    userId: payload.userId || payload.metadata?.userId || '',
    payload: payload.data || payload,
  };
}

