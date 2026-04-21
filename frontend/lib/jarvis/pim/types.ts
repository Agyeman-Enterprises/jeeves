// IT-10A: Provider Intelligence Module (PIM) types

export type ProviderChannel =
  | 'sms'
  | 'mms'
  | 'email'
  | 'voice'
  | 'video'
  | 'chat'
  | 'other';

export type PIMHealthSnapshotRequest = {
  workspaceId: string;
  provider: string;        // e.g. 'ghexit'
  channel: ProviderChannel;
  windowHours: number;     // time window to analyze, e.g. 24
};

export type PIMHealthSnapshot = {
  provider: string;
  channel: ProviderChannel;
  windowHours: number;
  messagesTotal: number;
  messagesFailed: number;
  failureRate: number;
  avgLatencyMs: number | null;
  p95LatencyMs: number | null;
  jitterMs: number | null;
  healthScore: number;     // 0–1
};

