// src/lib/jarvis/events/types.ts
// Global Event Mesh (GEM) - Event Types for JARVIS Ecosystem
// Supports: Jarvis core, Nexus business intel, AdAI advertising, Ghexit comms, Social

// ============================================================================
// Event Type Definitions
// ============================================================================

export type JarvisEventType =
  // Core Jarvis events
  | 'jarvis.command.received'
  | 'jarvis.command.completed'
  | 'jarvis.command.failed'
  | 'jarvis.memory.item.created'
  | 'jarvis.timeline.event.recorded'
  | 'jarvis.journal.entry.created'
  | 'jarvis.error.logged'
  // Nexus events (Business Intelligence)
  | 'nexus.briefing.requested'
  | 'nexus.briefing.completed'
  | 'nexus.alert.triggered'
  | 'nexus.alert.resolved'
  | 'nexus.business.status.changed'
  | 'nexus.kpi.threshold.exceeded'
  | 'nexus.report.generated'
  // AdAI events (Advertising Automation)
  | 'adai.run.started'
  | 'adai.run.completed'
  | 'adai.run.failed'
  | 'adai.sync.completed'
  | 'adai.decision.proposed'
  | 'adai.decision.executed'
  | 'adai.approval.required'
  | 'adai.approval.granted'
  | 'adai.approval.rejected'
  | 'adai.anomaly.detected'
  | 'adai.budget.exceeded'
  | 'adai.monthly.spend.alert'
  | 'adai.token.expiring'
  | 'adai.token.expired'
  | 'adai.creative.rotated'
  | 'adai.campaign.paused'
  | 'adai.campaign.scaled'
  // Ghexit events (Communications)
  | 'ghexit.email.sent'
  | 'ghexit.email.failed'
  | 'ghexit.email.bounced'
  | 'ghexit.sms.sent'
  | 'ghexit.sms.failed'
  | 'ghexit.call.initiated'
  | 'ghexit.call.completed'
  | 'ghexit.push.sent'
  | 'ghexit.webhook.received'
  // Social Media events
  | 'social.post.scheduled'
  | 'social.post.published'
  | 'social.post.failed'
  | 'social.engagement.received'
  | 'social.mention.detected';

// ============================================================================
// Event Source Definitions
// ============================================================================

export type JarvisEventSource =
  // Core sources
  | 'jarvis.command'
  | 'jarvis.memory'
  | 'jarvis.timeline'
  | 'jarvis.journal'
  | 'jarvis.core'
  // Agent sources
  | 'agent.nexus'
  | 'agent.adai'
  | 'agent.social'
  | 'agent.communications'
  | 'agent.finance'
  | 'agent.content'
  // External provider sources
  | 'external.webhook'
  | 'external.provider.meta'
  | 'external.provider.google'
  | 'external.provider.tiktok'
  | 'external.provider.twitter'
  | 'external.provider.resend'
  | 'external.provider.twilio'
  | 'external.provider.stripe';

// ============================================================================
// Base Payload Interface
// ============================================================================

export interface BaseEventPayload {
  workspaceId: string;
  userId: string;
  context?: Record<string, unknown>;
}

// ============================================================================
// Event-Specific Payload Types
// ============================================================================

export interface JarvisEventPayloadMap {
  // Core Jarvis events
  'jarvis.command.received': BaseEventPayload & {
    commandName: string;
    rawInput: unknown;
    correlationId?: string;
  };

  'jarvis.command.completed': BaseEventPayload & {
    commandName: string;
    resultSummary?: string;
    correlationId?: string;
  };

  'jarvis.command.failed': BaseEventPayload & {
    commandName: string;
    errorMessage: string;
    correlationId?: string;
  };

  'jarvis.memory.item.created': BaseEventPayload & {
    memoryId: string;
    memoryType: string;
    summary: string;
  };

  'jarvis.timeline.event.recorded': BaseEventPayload & {
    timelineEventId: string;
    timelineType: string;
    label: string;
  };

  'jarvis.journal.entry.created': BaseEventPayload & {
    journalEntryId: string;
    title?: string;
  };

  'jarvis.error.logged': BaseEventPayload & {
    location: string;
    message: string;
    stack?: string;
  };

  // Nexus events
  'nexus.briefing.requested': BaseEventPayload & {
    briefingType: 'ceo' | 'portfolio' | 'business';
    businessId?: string;
  };

  'nexus.briefing.completed': BaseEventPayload & {
    briefingType: string;
    summary: string;
    alertCount: number;
    topPerformers?: string[];
    atRisk?: string[];
  };

  'nexus.alert.triggered': BaseEventPayload & {
    alertId: string;
    alertType: string;
    severity: 'info' | 'warning' | 'critical';
    businessId: string;
    businessName: string;
    message: string;
  };

  'nexus.alert.resolved': BaseEventPayload & {
    alertId: string;
    resolvedBy: string;
    resolution: string;
  };

  'nexus.business.status.changed': BaseEventPayload & {
    businessId: string;
    businessName: string;
    oldStatus: string;
    newStatus: string;
  };

  'nexus.kpi.threshold.exceeded': BaseEventPayload & {
    businessId: string;
    kpiName: string;
    threshold: number;
    actualValue: number;
    direction: 'above' | 'below';
  };

  'nexus.report.generated': BaseEventPayload & {
    reportType: string;
    reportId: string;
    period: string;
    summary: string;
  };

  // AdAI events
  'adai.run.started': BaseEventPayload & {
    runId: string;
    mode: 'dry_run' | 'execute';
  };

  'adai.run.completed': BaseEventPayload & {
    runId: string;
    decisionsProposed: number;
    decisionsExecuted: number;
    totalSpendImpact: number;
  };

  'adai.run.failed': BaseEventPayload & {
    runId: string;
    error: string;
    stage: string;
  };

  'adai.sync.completed': BaseEventPayload & {
    campaignsSynced: number;
    adsetsSynced: number;
    adsSynced: number;
    monthlySpendTotal: number;
  };

  'adai.decision.proposed': BaseEventPayload & {
    decisionId: string;
    decisionType: 'scale' | 'pause' | 'rotate' | 'create';
    entityType: 'campaign' | 'adset' | 'ad';
    entityId: string;
    reason: string;
  };

  'adai.decision.executed': BaseEventPayload & {
    decisionId: string;
    decisionType: string;
    entityId: string;
    result: 'success' | 'failed';
  };

  'adai.approval.required': BaseEventPayload & {
    approvalId: string;
    decisionId: string;
    changeSet: unknown;
    totalSpendImpact: number;
    reason: string;
  };

  'adai.approval.granted': BaseEventPayload & {
    approvalId: string;
    approvedBy: string;
  };

  'adai.approval.rejected': BaseEventPayload & {
    approvalId: string;
    rejectedBy: string;
    reason: string;
  };

  'adai.anomaly.detected': BaseEventPayload & {
    anomalyType: 'spend_spike' | 'cpa_spike' | 'performance_drop';
    entityType: string;
    entityId: string;
    expectedValue: number;
    actualValue: number;
    severity: 'warning' | 'critical';
  };

  'adai.budget.exceeded': BaseEventPayload & {
    budgetType: 'daily' | 'campaign' | 'workspace';
    limit: number;
    actual: number;
  };

  'adai.monthly.spend.alert': BaseEventPayload & {
    threshold: number;
    currentSpend: number;
    projectedMonthEnd: number;
  };

  'adai.token.expiring': BaseEventPayload & {
    connectionId: string;
    platform: string;
    expiresAt: string;
    daysRemaining: number;
  };

  'adai.token.expired': BaseEventPayload & {
    connectionId: string;
    platform: string;
  };

  'adai.creative.rotated': BaseEventPayload & {
    adId: string;
    oldCreativeId: string;
    newCreativeId: string;
    reason: string;
  };

  'adai.campaign.paused': BaseEventPayload & {
    campaignId: string;
    reason: string;
    rule: string;
  };

  'adai.campaign.scaled': BaseEventPayload & {
    campaignId: string;
    oldBudget: number;
    newBudget: number;
    reason: string;
  };

  // Ghexit events
  'ghexit.email.sent': BaseEventPayload & {
    emailId: string;
    to: string[];
    subject: string;
    template?: string;
    provider: 'resend' | 'gmail' | 'outlook';
  };

  'ghexit.email.failed': BaseEventPayload & {
    to: string[];
    subject: string;
    error: string;
    provider: string;
  };

  'ghexit.email.bounced': BaseEventPayload & {
    emailId: string;
    to: string;
    bounceType: 'hard' | 'soft';
  };

  'ghexit.sms.sent': BaseEventPayload & {
    messageId: string;
    to: string;
    body: string;
    provider: 'twilio' | 'ghexit';
  };

  'ghexit.sms.failed': BaseEventPayload & {
    to: string;
    error: string;
    provider: string;
  };

  'ghexit.call.initiated': BaseEventPayload & {
    callId: string;
    to: string;
    purpose: string;
    provider: 'twilio' | 'ghexit';
  };

  'ghexit.call.completed': BaseEventPayload & {
    callId: string;
    duration: number;
    status: string;
  };

  'ghexit.push.sent': BaseEventPayload & {
    notificationId: string;
    title: string;
    priority: number;
    provider: 'pushover';
  };

  'ghexit.webhook.received': BaseEventPayload & {
    provider: string;
    webhookType: string;
    rawPayload: unknown;
  };

  // Social Media events
  'social.post.scheduled': BaseEventPayload & {
    postId: string;
    platform: string;
    businessId: string;
    scheduledFor: string;
    content: string;
  };

  'social.post.published': BaseEventPayload & {
    postId: string;
    platform: string;
    platformPostId: string;
    publishedAt: string;
  };

  'social.post.failed': BaseEventPayload & {
    postId: string;
    platform: string;
    error: string;
  };

  'social.engagement.received': BaseEventPayload & {
    postId: string;
    platform: string;
    engagementType: 'like' | 'comment' | 'share' | 'save';
    count: number;
  };

  'social.mention.detected': BaseEventPayload & {
    platform: string;
    mentionId: string;
    author: string;
    content: string;
    sentiment?: 'positive' | 'neutral' | 'negative';
  };
}

// ============================================================================
// Event Envelope (wire format)
// ============================================================================

export interface JarvisEventEnvelope<T extends JarvisEventType = JarvisEventType> {
  id?: string; // filled after DB insert
  type: T;
  source: JarvisEventSource;
  subjectId?: string;
  correlationId?: string;
  causationId?: string;
  workspaceId: string;
  userId: string;
  payload: T extends keyof JarvisEventPayloadMap
    ? JarvisEventPayloadMap[T]
    : BaseEventPayload & Record<string, unknown>;
  createdAt?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

export function isNexusEvent(eventType: string): boolean {
  return eventType.startsWith('nexus.');
}

export function isAdAIEvent(eventType: string): boolean {
  return eventType.startsWith('adai.');
}

export function isGhexitEvent(eventType: string): boolean {
  return eventType.startsWith('ghexit.');
}

export function isSocialEvent(eventType: string): boolean {
  return eventType.startsWith('social.');
}

export function getEventSeverity(eventType: string): 'info' | 'warning' | 'critical' {
  const criticalEvents = [
    'adai.token.expired',
    'adai.budget.exceeded',
    'nexus.kpi.threshold.exceeded',
    'ghexit.email.bounced',
    'adai.run.failed',
  ];
  const warningEvents = [
    'adai.token.expiring',
    'adai.anomaly.detected',
    'adai.approval.required',
    'adai.monthly.spend.alert',
    'nexus.alert.triggered',
    'social.post.failed',
    'ghexit.email.failed',
    'ghexit.sms.failed',
  ];

  if (criticalEvents.includes(eventType)) return 'critical';
  if (warningEvents.includes(eventType)) return 'warning';
  return 'info';
}
