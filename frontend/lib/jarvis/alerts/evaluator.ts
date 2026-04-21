import { supabaseServer } from '@/lib/supabase/server';
import {
  AlertRuleType,
  AlertSource,
  Comparator,
  PredictionThresholdCondition,
  AnomalyWatchCondition,
  AlertChannel,
  AlertEventType
} from './types';

import {
  predictProviderLatency,
  predictProviderFailureRate,
  predictWorkspaceSpend,
  computeRoutingRecommendation
} from '@/lib/jarvis/prediction/engine';

type AlertRuleRow = {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  is_enabled: boolean;
  rule_type: string;
  source: string;
  condition: any;
  channel: string;
  target: string | null;
  min_interval_seconds: number;
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
};

function compare(comparator: Comparator, value: number, threshold: number): boolean {
  switch (comparator) {
    case '>':
      return value > threshold;
    case '<':
      return value < threshold;
    case '>=':
      return value >= threshold;
    case '<=':
      return value <= threshold;
    default:
      return false;
  }
}

function parsePredictionCondition(condition: any): PredictionThresholdCondition | null {
  if (!condition || typeof condition !== 'object') return null;
  if (typeof condition.metric !== 'string') return null;
  if (!['>', '<', '>=', '<='].includes(condition.comparator)) return null;
  if (typeof condition.threshold !== 'number') return null;

  return {
    provider: condition.provider,
    channel: condition.channel,
    horizonHours: condition.horizonHours,
    metric: condition.metric,
    comparator: condition.comparator as Comparator,
    threshold: condition.threshold
  };
}

function parseAnomalyCondition(condition: any): AnomalyWatchCondition | null {
  if (!condition || typeof condition !== 'object') return null;
  const out: AnomalyWatchCondition = {};
  if (condition.anomalyType && typeof condition.anomalyType === 'string') {
    out.anomalyType = condition.anomalyType;
  }
  if (typeof condition.minSeverity === 'number') {
    out.minSeverity = condition.minSeverity;
  }
  return out;
}

function canTrigger(rule: AlertRuleRow, now: Date): boolean {
  if (!rule.last_triggered_at) return true;
  const last = new Date(rule.last_triggered_at);
  const diffSeconds = (now.getTime() - last.getTime()) / 1000;
  return diffSeconds >= (rule.min_interval_seconds ?? 0);
}

async function recordAlertEvent(
  supabase: typeof supabaseServer,
  workspaceId: string,
  rule: AlertRuleRow,
  eventType: AlertEventType,
  payload: any
): Promise<void> {
  const nowIso = new Date().toISOString();

  const { error: insertError } = await ((supabase as any)
    .from('jarvis_alert_events')
    .insert({
      workspace_id: workspaceId,
      rule_id: rule.id,
      triggered_at: nowIso,
      event_type: eventType,
      payload,
      delivery_channel: rule.channel as AlertChannel,
      delivery_status: 'pending'
    }));

  if (insertError) {
    console.error('[Alerts] recordAlertEvent insert error:', insertError);
  }

  const { error: updateError } = await ((supabase as any)
    .from('jarvis_alert_rules')
    .update({
      last_triggered_at: nowIso,
      updated_at: nowIso
    })
    .eq('id', rule.id));

  if (updateError) {
    console.error('[Alerts] recordAlertEvent rule update error:', updateError);
  }
}

async function evaluatePredictionRule(
  supabase: typeof supabaseServer,
  workspaceId: string,
  rule: AlertRuleRow
): Promise<boolean> {
  const source = rule.source as AlertSource;
  const cond = parsePredictionCondition(rule.condition);
  if (!cond) {
    console.warn('[Alerts] Invalid prediction condition for rule:', rule.id);
    return false;
  }

  const provider = cond.provider ?? 'ghexit';
  const channel = cond.channel ?? 'sms';
  const horizonHours = cond.horizonHours ?? 24;

  let metricValue: number | null = null;
  let snapshot: any = null;

  try {
    if (source === 'prediction:latency') {
      const res = await predictProviderLatency({
        workspaceId,
        provider,
        channel,
        horizonHours
      });
      snapshot = res;
      const key = cond.metric as keyof typeof res;
      const value = (res as any)[key];
      if (typeof value === 'number') metricValue = value;
    } else if (source === 'prediction:failure_rate') {
      const res = await predictProviderFailureRate({
        workspaceId,
        provider,
        channel,
        horizonHours
      });
      snapshot = res;
      const key = cond.metric as keyof typeof res;
      const value = (res as any)[key];
      if (typeof value === 'number') metricValue = value;
    } else if (source === 'prediction:spend') {
      const res = await predictWorkspaceSpend({
        workspaceId,
        horizonDays: Math.max(1, Math.round(horizonHours / 24))
      });
      snapshot = res;
      const key = cond.metric as keyof typeof res;
      const value = (res as any)[key];
      if (typeof value === 'number') metricValue = value;
    } else if (source === 'prediction:routing') {
      const res = await computeRoutingRecommendation({
        workspaceId,
        provider,
        channel
      });
      snapshot = res;
      const key = cond.metric as keyof typeof res;
      const value = (res as any)[key];
      if (typeof value === 'number') metricValue = value;
    } else {
      console.warn('[Alerts] Unsupported prediction source:', source);
      return false;
    }
  } catch (err) {
    console.error('[Alerts] evaluatePredictionRule prediction error:', err);
    return false;
  }

  if (metricValue == null) {
    console.warn(
      '[Alerts] evaluatePredictionRule metric not found or null:',
      cond.metric,
      'for rule',
      rule.id
    );
    return false;
  }

  const isTriggered = compare(cond.comparator, metricValue, cond.threshold);
  if (!isTriggered) return false;

  const now = new Date();
  if (!canTrigger(rule, now)) return false;

  const payload = {
    source,
    condition: cond,
    metricValue,
    snapshot
  };

  await recordAlertEvent(supabase, workspaceId, rule, 'prediction_threshold', payload);
  return true;
}

async function evaluateAnomalyRule(
  supabase: typeof supabaseServer,
  workspaceId: string,
  rule: AlertRuleRow
): Promise<number> {
  const cond = parseAnomalyCondition(rule.condition);
  if (!cond) {
    console.warn('[Alerts] Invalid anomaly condition for rule:', rule.id);
    return 0;
  }

  const baselineSince = (() => {
    if (rule.last_triggered_at) {
      return rule.last_triggered_at;
    }
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString();
  })();

  const { data, error } = await ((supabase as any)
    .from('jarvis_aim_anomalies')
    .select('*')
    .eq('workspace_id', workspaceId)
    .gte('detected_at', baselineSince)
    .order('detected_at', { ascending: true }));

  if (error) {
    console.error('[Alerts] evaluateAnomalyRule query error:', error);
    return 0;
  }

  const rows = (data ?? []) as any[];

  if (!rows.length) return 0;

  const minSeverity = cond.minSeverity ?? 0;
  const anomalyTypeFilter = cond.anomalyType;

  const now = new Date();
  if (!canTrigger(rule, now)) {
    return 0;
  }

  let triggeredCount = 0;
  let latestDetected: string | null = null;

  for (const row of rows) {
    if (anomalyTypeFilter && row.anomaly_type !== anomalyTypeFilter) {
      continue;
    }
    const sev = Number(row.severity ?? 0);
    if (sev < minSeverity) continue;

    const payload = {
      source: 'anomaly:aim',
      ruleCondition: cond,
      anomaly: row
    };

    await recordAlertEvent(supabase, workspaceId, rule, 'anomaly_detected', payload);
    triggeredCount += 1;
    latestDetected = row.detected_at;
  }

  if (triggeredCount > 0 && latestDetected) {
    const { error: updateError } = await ((supabase as any)
      .from('jarvis_alert_rules')
      .update({
        last_triggered_at: latestDetected,
        updated_at: new Date().toISOString()
      })
      .eq('id', rule.id));

    if (updateError) {
      console.error('[Alerts] evaluateAnomalyRule update error:', updateError);
    }
  }

  return triggeredCount;
}

/**
 * Evaluate alert rules for a single workspace.
 * Returns number of rules evaluated and number of alerts created.
 */
export async function evaluateAlertsForWorkspace(
  workspaceId: string
): Promise<{ rulesEvaluated: number; alertsCreated: number }> {
  const supabase = supabaseServer;

  const { data, error } = await ((supabase as any)
    .from('jarvis_alert_rules')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('is_enabled', true));

  if (error) {
    console.error('[Alerts] evaluateAlertsForWorkspace rules query error:', error);
    return { rulesEvaluated: 0, alertsCreated: 0 };
  }

  const rules = (data ?? []) as AlertRuleRow[];
  let alertsCreated = 0;

  for (const rule of rules) {
    if (rule.rule_type === 'prediction_threshold') {
      const triggered = await evaluatePredictionRule(supabase, workspaceId, rule);
      if (triggered) alertsCreated += 1;
    } else if (rule.rule_type === 'anomaly_watch') {
      const count = await evaluateAnomalyRule(supabase, workspaceId, rule);
      alertsCreated += count;
    } else {
      console.warn('[Alerts] Unknown rule_type for rule:', rule.id, rule.rule_type);
    }
  }

  return {
    rulesEvaluated: rules.length,
    alertsCreated
  };
}

/**
 * Evaluate alert rules for all workspaces that have rules.
 */
export async function evaluateAlertsForAllWorkspaces(): Promise<{
  workspaces: number;
  totalRulesEvaluated: number;
  totalAlertsCreated: number;
}> {
  const supabase = supabaseServer;

  const { data, error } = await ((supabase as any)
    .from('jarvis_alert_rules')
    .select('workspace_id')
    .eq('is_enabled', true));

  if (error) {
    console.error('[Alerts] evaluateAlertsForAllWorkspaces workspace query error:', error);
    return { workspaces: 0, totalRulesEvaluated: 0, totalAlertsCreated: 0 };
  }

  const workspaceIds = Array.from(
    new Set((data ?? []).map((row: any) => row.workspace_id as string))
  ) as string[];

  let totalRulesEvaluated = 0;
  let totalAlertsCreated = 0;

  for (const workspaceId of workspaceIds) {
    const result = await evaluateAlertsForWorkspace(workspaceId);
    totalRulesEvaluated += result.rulesEvaluated;
    totalAlertsCreated += result.alertsCreated;
  }

  return {
    workspaces: workspaceIds.length,
    totalRulesEvaluated,
    totalAlertsCreated
  };
}

