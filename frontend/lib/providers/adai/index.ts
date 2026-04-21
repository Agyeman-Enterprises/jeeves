// AdAI provider adapter - handles Meta Marketing API webhooks and internal AdAI events
import { verifyAdAISignature } from './verify';
import { normalizeAdAI, normalizeMetaEventBatch } from './normalize';
import type { ProviderAdapter, NormalizedProviderEvent } from '../types';

export const AdAIAdapter: ProviderAdapter = {
  verify: verifyAdAISignature,
  normalize: normalizeAdAI,
};

// Re-export for convenience
export { verifyAdAISignature } from './verify';
export { normalizeAdAI, normalizeMetaEventBatch } from './normalize';
export type { AdAIEventType, AdAIInternalEventType, MetaAdEventType } from './normalize';

/**
 * Priority companies for ad spend (from user config)
 * These get priority in optimization cycles and reporting
 */
export const PRIORITY_COMPANIES = [
  'medrx',
  'bookadoc2u',
  'myhealthally',
  'inkwellpublishing',
  'accessmd',
] as const;

/**
 * Monthly spend alert threshold (USD)
 * Alert user when total ad spend across all companies reaches this amount
 */
export const MONTHLY_SPEND_ALERT_THRESHOLD = 150;

/**
 * Check if a company is a priority company
 */
export function isPriorityCompany(companySlug: string): boolean {
  return PRIORITY_COMPANIES.includes(
    companySlug.toLowerCase().replace(/[^a-z0-9]/g, '') as any
  );
}

/**
 * AdAI Event Types for GEM integration
 */
export const ADAI_EVENT_TYPES = {
  // Sync events
  SYNC_STARTED: 'adai.sync.started',
  SYNC_COMPLETED: 'adai.sync.completed',
  SYNC_FAILED: 'adai.sync.failed',

  // Decision events
  DECISION_PROPOSED: 'adai.decision.proposed',
  DECISION_APPROVED: 'adai.decision.approved',
  DECISION_REJECTED: 'adai.decision.rejected',
  DECISION_EXECUTED: 'adai.decision.executed',
  DECISION_FAILED: 'adai.decision.failed',
  DECISION_ROLLED_BACK: 'adai.decision.rolled_back',

  // Approval events
  APPROVAL_REQUIRED: 'adai.approval.required',

  // Alert events
  ANOMALY_DETECTED: 'adai.anomaly.detected',
  BUDGET_EXCEEDED: 'adai.budget.exceeded',
  MONTHLY_SPEND_ALERT: 'adai.monthly_spend.alert',
  TOKEN_EXPIRING: 'adai.token.expiring',
  TOKEN_EXPIRED: 'adai.token.expired',

  // Experiment events
  EXPERIMENT_STARTED: 'adai.experiment.started',
  EXPERIMENT_COMPLETED: 'adai.experiment.completed',
  EXPERIMENT_WINNER: 'adai.experiment.winner',

  // Run events
  RUN_STARTED: 'adai.run.started',
  RUN_COMPLETED: 'adai.run.completed',
  RUN_FAILED: 'adai.run.failed',
} as const;

export type AdAIEventTypeKey = keyof typeof ADAI_EVENT_TYPES;
