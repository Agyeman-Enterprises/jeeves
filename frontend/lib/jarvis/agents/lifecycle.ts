// AgentStatus not yet defined in types.ts - using local type for now
type AgentStatus = "ACTIVE" | "PAUSED" | "DISABLED" | "DEGRADED";

export type AgentLifecycleStatus = "ACTIVE" | "PAUSED" | "DISABLED" | "DEGRADED";
export type RunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "RETRYING" | "CANCELLED";
export type ErrorKind = "NETWORK" | "VALIDATION" | "FATAL" | "RATE_LIMIT" | "TRANSIENT";

export interface ClaimWorkRequest {
  agent_slug: string;
  max_batch?: number;
}

export interface ClaimedRun {
  id: string;
  input: Record<string, any>;
  user: {
    userId: string;
    workspaceId?: string | null;
  };
  planId?: string | null;
  planStepId?: string | null;
}

export interface ClaimWorkResponse {
  runs: ClaimedRun[];
}

export interface ReportResultRequest {
  run_id: string;
  status: "COMPLETED" | "FAILED";
  result?: any;
  error?: string;
  logs?: string[];
}

export interface HeartbeatRequest {
  agent_slug: string;
  version?: string;
  metrics?: {
    uptime_sec?: number;
    runs_completed?: number;
    runs_failed?: number;
  };
}

export function isRetryableError(errorKind: ErrorKind | null | undefined): boolean {
  if (!errorKind) return false;
  return ["NETWORK", "RATE_LIMIT", "TRANSIENT"].includes(errorKind);
}

export function calculateBackoff(attemptCount: number): Date {
  // Exponential backoff with jitter
  // Attempt 1 → +5 minutes
  // Attempt 2 → +30 minutes
  const backoffMinutes = attemptCount === 1 ? 5 : 30;
  return new Date(Date.now() + backoffMinutes * 60_000);
}

