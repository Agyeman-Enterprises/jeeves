// IT-6: Basic Agent Runtime types
export interface JarvisAgent {
  name: string;
  description: string;
  supportedIntents: string[];
  run(ctx: AgentContext): Promise<AgentResult>;
}

export interface AgentContext {
  userId: string;
  workspaceId: string;
  input: string;
  rewritten: string;
  intent: string;
  metadata?: Record<string, any>;
}

export interface AgentResult {
  status: 'success' | 'error';
  agent: string;
  summary: string;
  data?: Record<string, any>;
  error?: string;
}

// IT-12: Agent Trigger System types
export type AgentTriggerType = 'prediction_threshold' | 'anomaly_trigger';

export type AgentSource =
  | 'prediction:latency'
  | 'prediction:failure_rate'
  | 'prediction:routing'
  | 'prediction:spend'
  | 'anomaly:aim';

export type Comparator = '>' | '<' | '>=' | '<=';

export type PredictionTriggerCondition = {
  provider?: string;
  channel?: string;
  horizonHours?: number;
  metric: string;
  comparator: Comparator;
  threshold: number;
};

export type AnomalyTriggerCondition = {
  anomalyType?: string;
  minSeverity?: number;
};

export type AgentAction =
  | { type: 'adjustRouting'; provider: string; delta?: number; setWeight?: number }
  | { type: 'notify'; channel: string; target: string; message: string }
  | { type: 'invokeInternalAPI'; method: string; url: string; body?: any }
  | { type: 'runNexusTask'; task: string; params?: any };
