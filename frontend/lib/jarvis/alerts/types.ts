export type AlertRuleType = 'prediction_threshold' | 'anomaly_watch';

export type AlertSource =
  | 'prediction:latency'
  | 'prediction:failure_rate'
  | 'prediction:spend'
  | 'prediction:routing'
  | 'anomaly:aim';

export type Comparator = '>' | '<' | '>=' | '<=';

export type PredictionThresholdCondition = {
  provider?: string;
  channel?: string;
  horizonHours?: number;
  metric: string; // e.g. 'predictedP95Ms', 'predictedFailureRate', 'score'
  comparator: Comparator;
  threshold: number;
};

export type AnomalyWatchCondition = {
  anomalyType?: string; // e.g. 'volume_spike', 'volume_drop'
  minSeverity?: number; // 0–1
};

export type AlertChannel = 'log' | 'sms' | 'email' | 'webhook';

export type AlertEventType = 'prediction_threshold' | 'anomaly_detected';

