import { supabaseServer } from '@/lib/supabase/server';
import {
  PredictionType,
  LatencyPredictionInput,
  LatencyPredictionResult,
  FailurePredictionInput,
  FailurePredictionResult,
  SpendPredictionInput,
  SpendPredictionResult,
  RoutingRecommendationInput,
  RoutingRecommendationResult
} from './types';
import { maybeUseMLEngine } from './mlBridge';

const DEFAULT_CACHE_TTL_SECONDS = 300; // 5 minutes

async function getCachedPrediction<T>(
  workspaceId: string,
  type: PredictionType,
  targetKey: string,
  horizon: string
): Promise<T | null> {
  const supabase = supabaseServer;

  const nowIso = new Date().toISOString();

  const { data, error } = await ((supabase as any)
    .from('jarvis_prediction_cache')
    .select('result, valid_until')
    .eq('workspace_id', workspaceId)
    .eq('prediction_type', type)
    .eq('target_key', targetKey)
    .eq('horizon', horizon)
    .gte('valid_until', nowIso)
    .maybeSingle());

  if (error) {
    console.error('[Prediction] getCachedPrediction error:', error);
    return null;
  }

  if (!data) return null;

  return (data.result as T) ?? null;
}

async function setCachedPrediction<T>(
  workspaceId: string,
  type: PredictionType,
  targetKey: string,
  horizon: string,
  result: T,
  ttlSeconds = DEFAULT_CACHE_TTL_SECONDS
): Promise<void> {
  const supabase = supabaseServer;
  const now = new Date();
  const validUntil = new Date(now.getTime() + ttlSeconds * 1000);

  const { error } = await ((supabase as any)
    .from('jarvis_prediction_cache')
    .upsert(
      {
        workspace_id: workspaceId,
        prediction_type: type,
        target_key: targetKey,
        horizon,
        result,
        computed_at: now.toISOString(),
        valid_until: validUntil.toISOString()
      },
      {
        onConflict: 'workspace_id,prediction_type,target_key,horizon'
      }
    ));

  if (error) {
    console.error('[Prediction] setCachedPrediction error:', error);
  }
}

// Helper to compute percentile from array
function percentile(values: number[], p: number): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.floor((p / 100) * (sorted.length - 1));
  return sorted[idx] ?? null;
}

/**
 * IT-10C:
 * Latency prediction using jarvis_pim_latency_curves and jarvis_pim_daily_rollups.
 * v0: statistical; v1+: ML override via mlBridge.
 */
export async function predictProviderLatency(
  input: LatencyPredictionInput
): Promise<LatencyPredictionResult> {
  const { workspaceId, provider, channel, horizonHours } = input;
  const targetKey = `${provider}:${channel}`;
  const horizon = `${horizonHours}h`;

  // Try cache first
  const cached = await getCachedPrediction<LatencyPredictionResult>(
    workspaceId,
    'latency',
    targetKey,
    horizon
  );
  if (cached) return cached;

  const supabase = supabaseServer;

  // Use last 24–72 hours as baseline
  const windowHours = Math.max(horizonHours * 2, 24);
  const since = new Date();
  since.setHours(since.getHours() - windowHours);

  // We rely primarily on jarvis_pim_latency_curves
  const { data, error } = await ((supabase as any)
    .from('jarvis_pim_latency_curves')
    .select('latency_p95_ms, samples, time_bucket')
    .eq('workspace_id', workspaceId)
    .eq('provider', provider)
    .eq('channel', channel)
    .gte('time_bucket', since.toISOString()));

  if (error) {
    console.error('[Prediction] predictProviderLatency query error:', error);
  }

  const rows = (data ?? []) as any[];
  const p95Values: number[] = [];
  let totalSamples = 0;

  for (const row of rows) {
    if (row.latency_p95_ms != null) {
      p95Values.push(Number(row.latency_p95_ms));
      totalSamples += row.samples ?? 0;
    }
  }

  let predictedP95Ms: number | null = null;
  let confidence = 0;

  if (p95Values.length > 0) {
    predictedP95Ms = percentile(p95Values, 50); // median of p95s
    // crude confidence: more samples => higher confidence
    confidence = Math.min(1, totalSamples / 500); // 500 samples ~ 1.0
  } else {
    predictedP95Ms = null;
    confidence = 0;
  }

  const statResult: LatencyPredictionResult = {
    provider,
    channel,
    horizonHours,
    predictedP95Ms,
    confidence,
    basis: {
      windowHours,
      samples: totalSamples
    }
  };

  const finalResult = await maybeUseMLEngine<LatencyPredictionResult>(
    'latency',
    input,
    statResult
  );

  await setCachedPrediction(workspaceId, 'latency', targetKey, horizon, finalResult);

  return finalResult;
}

/**
 * IT-10C:
 * Failure rate prediction using jarvis_pim_daily_rollups.
 * v0: simple baseline + last-day deviation; v1+: ML override.
 */
export async function predictProviderFailureRate(
  input: FailurePredictionInput
): Promise<FailurePredictionResult> {
  const { workspaceId, provider, channel, horizonHours } = input;
  const targetKey = `${provider}:${channel}`;
  const horizon = `${horizonHours}h`;

  const cached = await getCachedPrediction<FailurePredictionResult>(
    workspaceId,
    'failure_rate',
    targetKey,
    horizon
  );
  if (cached) return cached;

  const supabase = supabaseServer;

  const baselineDays = 7;
  const { data, error } = await ((supabase as any)
    .from('jarvis_pim_daily_rollups')
    .select('date_bucket, messages_total, messages_failed')
    .eq('workspace_id', workspaceId)
    .eq('provider', provider)
    .eq('channel', channel)
    .order('date_bucket', { ascending: true })
    .limit(baselineDays));

  if (error) {
    console.error('[Prediction] predictProviderFailureRate query error:', error);
  }

  const rows = (data ?? []) as any[];

  if (rows.length < 2) {
    const fallback: FailurePredictionResult = {
      provider,
      channel,
      horizonHours,
      predictedFailureRate: 0.01,
      confidence: 0,
      basis: {
        baselineFailureRate: 0.01,
        lastFailureRate: 0.01,
        sampleDays: rows.length
      }
    };
    await setCachedPrediction(workspaceId, 'failure_rate', targetKey, horizon, fallback);
    return fallback;
  }

  const last = rows[rows.length - 1];
  const baselineRows = rows.slice(0, rows.length - 1);

  function fr(row: any): number {
    if (!row.messages_total || row.messages_total <= 0) return 0;
    return Number(row.messages_failed ?? 0) / Number(row.messages_total);
  }

  const baselineFrVals = baselineRows.map(fr);
  const baselineFailureRate =
    baselineFrVals.reduce((sum, v) => sum + v, 0) / baselineFrVals.length;

  const lastFailureRate = fr(last);

  // simple projection: baseline + half of the last deviation
  const deviation = lastFailureRate - baselineFailureRate;
  let predictedFailureRate = baselineFailureRate + deviation * 0.5;
  if (predictedFailureRate < 0) predictedFailureRate = 0;
  if (predictedFailureRate > 1) predictedFailureRate = 1;

  // confidence: more days => higher confidence
  const confidence = Math.min(1, rows.length / 14);

  const statResult: FailurePredictionResult = {
    provider,
    channel,
    horizonHours,
    predictedFailureRate,
    confidence,
    basis: {
      baselineFailureRate,
      lastFailureRate,
      sampleDays: rows.length
    }
  };

  const finalResult = await maybeUseMLEngine<FailurePredictionResult>(
    'failure_rate',
    input,
    statResult
  );

  await setCachedPrediction(workspaceId, 'failure_rate', targetKey, horizon, finalResult);

  return finalResult;
}

/**
 * IT-10C:
 * Spend / volume prediction using jarvis_aim_enterprise_cycles.
 * v0: forecast volumes; pricing can be applied later.
 */
export async function predictWorkspaceSpend(
  input: SpendPredictionInput
): Promise<SpendPredictionResult> {
  const { workspaceId, horizonDays } = input;
  const targetKey = 'workspace:all';
  const horizon = `${horizonDays}d`;

  const cached = await getCachedPrediction<SpendPredictionResult>(
    workspaceId,
    'spend',
    targetKey,
    horizon
  );
  if (cached) return cached;

  const supabase = supabaseServer;

  const baselineDays = Math.max(7, horizonDays);
  const { data, error } = await ((supabase as any)
    .from('jarvis_aim_enterprise_cycles')
    .select('msg_total, call_total, email_total')
    .eq('workspace_id', workspaceId)
    .order('date_bucket', { ascending: true })
    .limit(baselineDays));

  if (error) {
    console.error('[Prediction] predictWorkspaceSpend query error:', error);
  }

  const rows = (data ?? []) as any[];

  if (!rows.length) {
    const empty: SpendPredictionResult = {
      workspaceId,
      horizonDays,
      predictedMessageVolume: 0,
      predictedCallVolume: 0,
      predictedEmailVolume: 0,
      confidence: 0,
      basis: {
        baselineDays: 0,
        avgMessagesPerDay: 0,
        avgCallsPerDay: 0,
        avgEmailsPerDay: 0
      }
    };
    await setCachedPrediction(workspaceId, 'spend', targetKey, horizon, empty);
    return empty;
  }

  const baselineDaysUsed = rows.length;
  const sums = rows.reduce(
    (acc, row) => {
      acc.msg += row.msg_total ?? 0;
      acc.call += row.call_total ?? 0;
      acc.email += row.email_total ?? 0;
      return acc;
    },
    { msg: 0, call: 0, email: 0 }
  );

  const avgMessagesPerDay = sums.msg / baselineDaysUsed;
  const avgCallsPerDay = sums.call / baselineDaysUsed;
  const avgEmailsPerDay = sums.email / baselineDaysUsed;

  const predictedMessageVolume = Math.max(0, avgMessagesPerDay * horizonDays);
  const predictedCallVolume = Math.max(0, avgCallsPerDay * horizonDays);
  const predictedEmailVolume = Math.max(0, avgEmailsPerDay * horizonDays);

  const confidence = Math.min(1, baselineDaysUsed / 30);

  const statResult: SpendPredictionResult = {
    workspaceId,
    horizonDays,
    predictedMessageVolume,
    predictedCallVolume,
    predictedEmailVolume,
    confidence,
    basis: {
      baselineDays: baselineDaysUsed,
      avgMessagesPerDay,
      avgCallsPerDay,
      avgEmailsPerDay
    }
  };

  const finalResult = await maybeUseMLEngine<SpendPredictionResult>(
    'spend',
    input,
    statResult
  );

  await setCachedPrediction(workspaceId, 'spend', targetKey, horizon, finalResult);

  return finalResult;
}

/**
 * IT-10C:
 * Routing recommendation score combining:
 * - Current health score (from PIM daily rollups)
 * - Predicted failure rate
 * - Predicted latency
 */
export async function computeRoutingRecommendation(
  input: RoutingRecommendationInput
): Promise<RoutingRecommendationResult> {
  const { workspaceId, provider, channel } = input;
  const targetKey = `${provider}:${channel}`;
  const horizon = '24h'; // default horizon for routing recommendation

  const cached = await getCachedPrediction<RoutingRecommendationResult>(
    workspaceId,
    'routing',
    targetKey,
    horizon
  );
  if (cached) return cached;

  const supabase = supabaseServer;

  // Get last daily rollup as current health score
  const { data: rollData, error: rollErr } = await ((supabase as any)
    .from('jarvis_pim_daily_rollups')
    .select('health_score')
    .eq('workspace_id', workspaceId)
    .eq('provider', provider)
    .eq('channel', channel)
    .order('date_bucket', { ascending: false })
    .limit(1));

  if (rollErr) {
    console.error('[Prediction] computeRoutingRecommendation rollup error:', rollErr);
  }

  const currentHealthScore =
    rollData && rollData.length > 0 && rollData[0].health_score != null
      ? Number(rollData[0].health_score)
      : null;

  // Predicted failure rate and latency
  const failurePred = await predictProviderFailureRate({
    workspaceId,
    provider,
    channel,
    horizonHours: 24
  });

  const latencyPred = await predictProviderLatency({
    workspaceId,
    provider,
    channel,
    horizonHours: 24
  });

  const fr = failurePred.predictedFailureRate;
  const p95 = latencyPred.predictedP95Ms ?? 0;

  // Normalize latency (assume 0–3000ms typical range)
  const normLatency = Math.min(1, Math.max(0, p95 / 3000));

  // Start from current health or neutral 0.7
  let score = currentHealthScore != null ? currentHealthScore : 0.7;

  // Penalize predicted failure
  score -= fr * 0.6; // heavy penalty

  // Penalize latency
  score -= normLatency * 0.3;

  // Clamp 0–1
  if (score < 0) score = 0;
  if (score > 1) score = 1;

  const statResult: RoutingRecommendationResult = {
    provider,
    channel,
    score: Number(score.toFixed(3)),
    factors: {
      currentHealthScore,
      predictedFailureRate: fr,
      predictedP95LatencyMs: latencyPred.predictedP95Ms
    }
  };

  const finalResult = await maybeUseMLEngine<RoutingRecommendationResult>(
    'routing',
    input,
    statResult
  );

  await setCachedPrediction(workspaceId, 'routing', targetKey, horizon, finalResult);

  return finalResult;
}

