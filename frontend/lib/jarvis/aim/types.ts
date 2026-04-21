export type AIMEntityType = 'user' | 'workspace';

export type AIMAnomalyDetectionInput = {
  workspaceId: string;
  entityType: AIMEntityType;
  entityId?: string;
  metrics: Record<string, number>; // e.g. { msg_total: 123, call_total: 10, email_total: 50 }
  baselineStats: {
    mean: Record<string, number>;
    stddev: Record<string, number>;
  };
};

export type AIMAnomalyDetectionResult = {
  anomaly: boolean;
  severity: number;     // 0–1
  anomalyType?: string; // e.g. 'volume_spike', 'volume_drop'
  notes?: string;
};

export type AIMEnterpriseCycle = {
  workspaceId: string;
  dateBucket: string; // ISO date string
  msgTotal: number;
  callTotal: number;
  emailTotal: number;
  peakHourLocal: number | null;
  offPeakHourLocal: number | null;
  cycleScore: number | null;
};

