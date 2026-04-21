// Twilio event normalization
import type { NormalizedProviderEvent } from '../types';

export function normalizeTwilio(payload: any): NormalizedProviderEvent {
  return {
    provider: 'twilio',
    type: payload.EventType || payload.MessageStatus || 'unknown',
    subjectId: payload.MessageSid || payload.CallSid || payload.id,
    workspaceId: payload.workspaceId || payload.metadata?.workspaceId || '',
    userId: payload.userId || payload.metadata?.userId || '',
    payload: payload,
  };
}

