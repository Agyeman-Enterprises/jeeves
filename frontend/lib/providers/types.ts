// Provider adapter interface for GEM webhook integration
import { NextRequest } from 'next/server';

export interface NormalizedProviderEvent {
  provider: string;        // 'ghexit', 'twilio', 'resend', etc.
  type: string;            // 'sms.received', 'email.sent', 'call.ended'
  subjectId?: string;      // message ID, call ID, email ID
  workspaceId: string;     // derived from metadata or internal routing
  userId: string;          // same
  payload: any;            // normalized structured payload
}

export interface ProviderAdapter {
  verify(req: NextRequest, rawBody: string): Promise<boolean>;
  normalize(rawPayload: any): NormalizedProviderEvent;
}

