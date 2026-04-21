import { supabaseServer } from '@/lib/supabase/server';
import {
  AgentAction,
  AgentSource,
  AgentTriggerType,
  Comparator
} from './types';

import {
  predictProviderLatency,
  predictProviderFailureRate,
  computeRoutingRecommendation,
  predictWorkspaceSpend
} from '@/lib/jarvis/prediction/engine';

import { executeAgentAction } from './actions';

type Db = typeof supabaseServer;

function compare(c: Comparator, a: number, b: number) {
  switch (c) {
    case '>':
      return a > b;
    case '<':
      return a < b;
    case '>=':
      return a >= b;
    case '<=':
      return a <= b;
    default:
      return false;
  }
}

function canTrigger(rule: any) {
  if (!rule.last_triggered_at) return true;
  const now = Date.now();
  const last = new Date(rule.last_triggered_at).getTime();
  return (now - last) / 1000 >= rule.min_interval_seconds;
}

async function evaluatePredictionRule(
  supabase: Db,
  workspaceId: string,
  rule: any
) {
  const cond = rule.condition;
  const provider = cond.provider ?? 'ghexit';
  const channel = cond.channel ?? 'sms';
  const horizonHours = cond.horizonHours ?? 24;

  let snapshot: any;
  let metricValue: number | null = null;

  try {
    switch (rule.source as AgentSource) {
      case 'prediction:latency':
        snapshot = await predictProviderLatency({ workspaceId, provider, channel, horizonHours });
        break;
      case 'prediction:failure_rate':
        snapshot = await predictProviderFailureRate({ workspaceId, provider, channel, horizonHours });
        break;
      case 'prediction:routing':
        snapshot = await computeRoutingRecommendation({ workspaceId, provider, channel });
        break;
      case 'prediction:spend':
        snapshot = await predictWorkspaceSpend({
          workspaceId,
          horizonDays: Math.max(1, Math.round(horizonHours / 24))
        });
        break;
      default:
        return null;
    }

    const value = snapshot?.[cond.metric];
    if (typeof value === 'number') {
      metricValue = value;
    }
  } catch (err) {
    console.error('[IT12] prediction rule error', err);
    return null;
  }

  if (metricValue == null) return null;

  const hit = compare(cond.comparator, metricValue, cond.threshold);
  return hit ? { snapshot, metricValue } : null;
}

async function evaluateAnomalyRule(
  supabase: Db,
  workspaceId: string,
  rule: any
) {
  const cond = rule.condition;
  const anomalyType = cond.anomalyType;
  const minSeverity = cond.minSeverity ?? 0.5;

  const baselineSince = rule.last_triggered_at
    ? rule.last_triggered_at
    : new Date(Date.now() - 24 * 3600 * 1000).toISOString();

  const { data, error } = await ((supabase as any)
    .from('jarvis_aim_anomalies')
    .select('*')
    .eq('workspace_id', workspaceId)
    .gte('detected_at', baselineSince)
    .order('detected_at', { ascending: true }));

  if (error) {
    console.error('[IT12] anomaly rule query error', error);
    return null;
  }

  const rows = data ?? [];
  const matches = rows.filter((r: any) => {
    if (anomalyType && r.anomaly_type !== anomalyType) return false;
    return (r.severity ?? 0) >= minSeverity;
  });

  if (!matches.length) return null;

  const latest = matches[matches.length - 1];
  return { matches, latest };
}

async function recordExecution(
  supabase: Db,
  workspaceId: string,
  rule: any,
  action: AgentAction,
  result: any
) {
  const nowIso = new Date().toISOString();

  const { error } = await ((supabase as any)
    .from('jarvis_agent_executions')
    .insert({
      workspace_id: workspaceId,
      rule_id: rule.id,
      triggered_at: nowIso,
      action_type: action.type,
      action_payload: action,
      result_status: result.status,
      result_detail: result.detail ?? null
    }));

  if (error) {
    console.error('[IT12] recordExecution error', error);
  }

  await ((supabase as any)
    .from('jarvis_agent_rules')
    .update({
      last_triggered_at: nowIso,
      updated_at: nowIso
    })
    .eq('id', rule.id));
}

export async function evaluateAgentRulesForWorkspace(workspaceId: string) {
  const supabase = supabaseServer;

  const { data, error } = await ((supabase as any)
    .from('jarvis_agent_rules')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('is_enabled', true));

  if (error) {
    console.error('[IT12] rules query error', error);
    return { rules: 0, executions: 0 };
  }

  const rules = data ?? [];
  let executions = 0;

  for (const rule of rules) {
    if (!canTrigger(rule)) continue;

    let triggerResult: any = null;

    if (rule.trigger_type === 'prediction_threshold') {
      triggerResult = await evaluatePredictionRule(supabase, workspaceId, rule);
    } else if (rule.trigger_type === 'anomaly_trigger') {
      triggerResult = await evaluateAnomalyRule(supabase, workspaceId, rule);
    }

    if (!triggerResult) continue;

    const action = rule.action as AgentAction;
    const result = await executeAgentAction(action);

    await recordExecution(supabase, workspaceId, rule, action, result);
    executions++;
  }

  return { rules: rules.length, executions };
}

export async function evaluateAgentRulesForAllWorkspaces() {
  const supabase = supabaseServer;

  const { data, error } = await ((supabase as any)
    .from('jarvis_agent_rules')
    .select('workspace_id')
    .eq('is_enabled', true));

  if (error) {
    console.error('[IT12] workspace fetch error', error);
    return { workspaces: 0, totalRules: 0, totalExecutions: 0 };
  }

  const workspaceIds = Array.from(
    new Set((data ?? []).map((row: any) => row.workspace_id as string))
  ) as string[];

  let totalRules = 0;
  let totalExecutions = 0;

  for (const ws of workspaceIds) {
    const res = await evaluateAgentRulesForWorkspace(ws);
    totalRules += res.rules;
    totalExecutions += res.executions;
  }

  return {
    workspaces: workspaceIds.length,
    totalRules,
    totalExecutions
  };
}

