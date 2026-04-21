export type PredictionType = 'latency' | 'failure_rate' | 'spend' | 'routing';

export type LatencyPredictionInput = {
  workspaceId: string;
  provider: string;
  channel: string;
  horizonHours: number; // e.g. 1, 4, 24
};

export type LatencyPredictionResult = {
  provider: string;
  channel: string;
  horizonHours: number;
  predictedP95Ms: number | null;
  confidence: number; // 0–1
  basis: {
    windowHours: number;
    samples: number;
  };
};

export type FailurePredictionInput = {
  workspaceId: string;
  provider: string;
  channel: string;
  horizonHours: number;
};

export type FailurePredictionResult = {
  provider: string;
  channel: string;
  horizonHours: number;
  predictedFailureRate: number; // 0–1
  confidence: number; // 0–1
  basis: {
    baselineFailureRate: number; // avg over baseline window
    lastFailureRate: number;     // last day
    sampleDays: number;
  };
};

export type SpendPredictionInput = {
  workspaceId: string;
  horizonDays: number; // e.g. 1, 7, 30
};

export type SpendPredictionResult = {
  workspaceId: string;
  horizonDays: number;
  predictedMessageVolume: number;
  predictedCallVolume: number;
  predictedEmailVolume: number;
  confidence: number;
  basis: {
    baselineDays: number;
    avgMessagesPerDay: number;
    avgCallsPerDay: number;
    avgEmailsPerDay: number;
  };
};

export type RoutingRecommendationInput = {
  workspaceId: string;
  provider: string;
  channel: string;
};

export type RoutingRecommendationResult = {
  provider: string;
  channel: string;
  score: number; // 0–1
  factors: {
    currentHealthScore: number | null;
    predictedFailureRate: number | null;
    predictedP95LatencyMs: number | null;
  };
};

