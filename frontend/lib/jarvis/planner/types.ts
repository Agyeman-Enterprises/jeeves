import type { JarvisTaskClassification, JarvisUserIdentity } from "../types";

export type PlanStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "PARTIAL";
export type PlanStepStatus =
  | "PENDING"
  | "RUNNING"
  | "WAITING_FOR_AGENT"
  | "COMPLETED"
  | "FAILED"
  | "SKIPPED";

export type PlanStepType = "tool" | "agent";

export interface Plan {
  id?: string;
  user: JarvisUserIdentity;
  workspaceId?: string | null;
  title?: string;
  status: PlanStatus;
  classification: JarvisTaskClassification;
  steps: PlanStep[];
}

export interface PlanStep {
  id?: string;
  orderIndex: number;
  type: PlanStepType;

  // tool-based step
  tool?: string;

  // agent-based step
  agentSlug?: string;

  input: Record<string, any>;
  status: PlanStepStatus;
  result?: any;
  error?: string;
}

