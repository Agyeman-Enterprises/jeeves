export type RoutingStrategy =
  | 'weighted'
  | 'latency_optimized'
  | 'cost_optimized'
  | 'failover';

export type RoutingDecisionResult = {
  providerKey: string | null;
  strategy: RoutingStrategy;
  score: number | null;
  reason: string;
  debug: {
    policy: {
      strategy: RoutingStrategy;
      healthThreshold: number;
      maxFailureRate: number;
      maxLatencyMs: number;
      preferLowCost: boolean;
    };
    candidates: Array<{
      providerKey: string;
      displayName: string | null;
      channel: string;
      baseWeight: number;
      status: string;
      region: string | null;
      costPerUnit: number | null;
      healthScore: number | null;
      routingScore: number | null;
      predictedFailureRate: number | null;
      predictedP95LatencyMs: number | null;
      combinedScore: number | null;
    }>;
  };
};

