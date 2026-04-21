// src/lib/jarvis/events/handlers.ts
import { registerHandler } from './bus';
import type { JarvisEventEnvelope } from './types';
import { ADAI_EVENT_TYPES, MONTHLY_SPEND_ALERT_THRESHOLD } from '@/lib/providers/adai';
import { processAdAIEmailNotification } from '@/lib/email/adai-notifications';

registerHandler(
  'debug.logger',
  { maxAttempts: 3, retryDelayMs: 3000 },
  async (event: JarvisEventEnvelope) => {
    console.log('[GEM] Event received by logger:', event.type, event.id);
  }
);

// ============================================================================
// AdAI Event Handlers
// ============================================================================

/**
 * AdAI Processor - handles internal AdAI events for state updates
 */
registerHandler(
  'adai.processor',
  { maxAttempts: 5, retryDelayMs: 2000 },
  async (event: JarvisEventEnvelope) => {
    // Only process AdAI events
    if (!event.type.startsWith('adai.')) return;

    console.log('[AdAI] Processing event:', event.type, event.subjectId);

    // Log all AdAI events for debugging
    switch (event.type) {
      case ADAI_EVENT_TYPES.RUN_STARTED:
        console.log(`[AdAI] Run started for workspace ${event.workspaceId}`);
        break;
      case ADAI_EVENT_TYPES.RUN_COMPLETED:
        console.log(`[AdAI] Run completed for workspace ${event.workspaceId}`, event.payload);
        break;
      case ADAI_EVENT_TYPES.RUN_FAILED:
        console.error(`[AdAI] Run failed for workspace ${event.workspaceId}:`, (event.payload as any)?.error);
        break;
      case ADAI_EVENT_TYPES.DECISION_EXECUTED:
        console.log(`[AdAI] Decision executed:`, event.payload);
        break;
      case ADAI_EVENT_TYPES.ANOMALY_DETECTED:
        console.warn(`[AdAI] Anomaly detected in workspace ${event.workspaceId}:`, event.payload);
        break;
      default:
        // Log other events at debug level
        break;
    }
  }
);

/**
 * AdAI Email Notification Handler - sends critical alerts via Resend
 */
registerHandler(
  'adai.notification.email',
  { maxAttempts: 3, retryDelayMs: 5000 },
  async (event: JarvisEventEnvelope) => {
    // Only process AdAI events that require email notification
    const emailNotificationTypes = [
      ADAI_EVENT_TYPES.APPROVAL_REQUIRED,
      ADAI_EVENT_TYPES.ANOMALY_DETECTED,
      ADAI_EVENT_TYPES.BUDGET_EXCEEDED,
      ADAI_EVENT_TYPES.MONTHLY_SPEND_ALERT,
      ADAI_EVENT_TYPES.TOKEN_EXPIRING,
      ADAI_EVENT_TYPES.TOKEN_EXPIRED,
      ADAI_EVENT_TYPES.RUN_FAILED,
    ];

    if (!emailNotificationTypes.includes(event.type as any)) return;

    console.log('[AdAI] Triggering email notification for:', event.type);

    // Prepare payload with workspace context
    const payload = {
      workspaceId: event.workspaceId,
      timestamp: event.createdAt || new Date().toISOString(),
      ...event.payload,
    };

    // Send email via Resend integration
    try {
      const sent = await processAdAIEmailNotification(event.type, payload);
      if (sent) {
        console.log('[AdAI] Email notification sent successfully');
      } else {
        console.warn('[AdAI] Email notification skipped (not configured or unknown event)');
      }
    } catch (error) {
      console.error('[AdAI] Email notification failed:', error);
      throw error; // Re-throw to trigger retry
    }
  }
);

/**
 * AdAI Monthly Spend Monitor - alerts when spend reaches threshold
 */
registerHandler(
  'adai.spend.monitor',
  { maxAttempts: 3, retryDelayMs: 5000 },
  async (event: JarvisEventEnvelope) => {
    // Only process sync completion events
    if (event.type !== ADAI_EVENT_TYPES.SYNC_COMPLETED) return;

    const totalSpend = (event.payload as any)?.monthlySpendTotal;
    if (typeof totalSpend !== 'number') return;

    // Check if we've crossed the monthly spend threshold
    if (totalSpend >= MONTHLY_SPEND_ALERT_THRESHOLD) {
      console.warn(
        `[AdAI] Monthly spend alert: $${totalSpend.toFixed(2)} (threshold: $${MONTHLY_SPEND_ALERT_THRESHOLD})`
      );

      // Emit a monthly spend alert event
      // The notification handler will pick this up and send an email
      // This would be done via emitEvent, but we can't import it here due to circular deps
      // Instead, this logic should be in the Cloudflare Worker
    }
  }
);

// Helper functions for email formatting
function formatEmailSubject(eventType: string): string {
  const subjects: Record<string, string> = {
    [ADAI_EVENT_TYPES.APPROVAL_REQUIRED]: '[AdAI] Approval Required - Ad Change Pending',
    [ADAI_EVENT_TYPES.ANOMALY_DETECTED]: '[AdAI] Alert - Anomaly Detected',
    [ADAI_EVENT_TYPES.BUDGET_EXCEEDED]: '[AdAI] Alert - Budget Exceeded',
    [ADAI_EVENT_TYPES.MONTHLY_SPEND_ALERT]: '[AdAI] Alert - Monthly Spend Threshold Reached',
    [ADAI_EVENT_TYPES.TOKEN_EXPIRING]: '[AdAI] Action Required - Ad Token Expiring Soon',
    [ADAI_EVENT_TYPES.TOKEN_EXPIRED]: '[AdAI] Critical - Ad Token Expired',
    [ADAI_EVENT_TYPES.RUN_FAILED]: '[AdAI] Error - Optimization Run Failed',
  };
  return subjects[eventType] || `[AdAI] ${eventType.replace('adai.', '').replace(/\./g, ' ')}`;
}

function getEmailTemplate(eventType: string): string {
  const templates: Record<string, string> = {
    [ADAI_EVENT_TYPES.APPROVAL_REQUIRED]: 'adai-approval-required',
    [ADAI_EVENT_TYPES.ANOMALY_DETECTED]: 'adai-alert',
    [ADAI_EVENT_TYPES.BUDGET_EXCEEDED]: 'adai-alert',
    [ADAI_EVENT_TYPES.MONTHLY_SPEND_ALERT]: 'adai-spend-alert',
    [ADAI_EVENT_TYPES.TOKEN_EXPIRING]: 'adai-token-alert',
    [ADAI_EVENT_TYPES.TOKEN_EXPIRED]: 'adai-token-alert',
    [ADAI_EVENT_TYPES.RUN_FAILED]: 'adai-error',
  };
  return templates[eventType] || 'adai-generic';
}

