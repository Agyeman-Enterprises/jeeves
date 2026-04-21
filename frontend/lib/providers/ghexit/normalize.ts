// Ghexit event normalization
import type { NormalizedProviderEvent } from '../types';

export function normalizeGhexit(payload: any): NormalizedProviderEvent {
  return {
    provider: 'ghexit',
    type: payload.eventType || payload.type || 'unknown',
    subjectId: payload.id || payload.messageId || payload.callId,
    workspaceId: payload.workspaceId || payload.metadata?.workspaceId || '',
    userId: payload.userId || payload.metadata?.userId || '',
    payload: payload.data || payload,
  };
}

