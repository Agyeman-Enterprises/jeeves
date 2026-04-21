import { supabaseServer } from '@/lib/supabase/server';
import { PIMHealthSnapshotRequest, PIMHealthSnapshot, ProviderChannel } from './types';

type RawEventRow = {
  latency_ms: number | null;
  event_type: string;
};

function computePercentile(values: number[], percentile: number): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.floor((percentile / 100) * (sorted.length - 1));
  return sorted[idx] ?? null;
}

function computeStdDev(values: number[]): number | null {
  if (values.length < 2) return null;
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const variance =
    values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / (values.length - 1);
  return Math.sqrt(variance);
}

function computeHealthScore(params: {
  failureRate: number;
  p95LatencyMs: number | null;
  jitterMs: number | null;
}): number {
  let score = 1.0;

  // Failure rate penalty
  const fr = params.failureRate; // 0–1
  if (fr > 0) {
    if (fr <= 0.01) {
      score -= fr * 2; // up to ~0.02 penalty
    } else if (fr <= 0.05) {
      score -= 0.02 + (fr - 0.01) * 5; // up to ~0.22 penalty
    } else {
      score -= 0.22 + (fr - 0.05) * 8; // can go much lower if failure rate is high
    }
  }

  // Latency penalty (based on p95)
  const p95 = params.p95LatencyMs ?? 0;
  if (p95 > 0) {
    if (p95 <= 500) {
      // good
    } else if (p95 <= 1000) {
      score -= 0.05;
    } else if (p95 <= 2000) {
      score -= 0.15;
    } else {
      score -= 0.3;
    }
  }

  // Jitter penalty
  const jitter = params.jitterMs ?? 0;
  if (jitter > 0) {
    if (jitter <= 200) {
      // good
    } else if (jitter <= 500) {
      score -= 0.05;
    } else {
      score -= 0.1;
    }
  }

  if (score < 0) score = 0;
  if (score > 1) score = 1;
  return Number(score.toFixed(3));
}

/**
 * IT-10A:
 * Get a health snapshot for a given provider/channel over a recent time window.
 * v0: purely statistical, based on jarvis_pim_provider_events.
 * v1 (IT-10C): may integrate with an ML model to override / calibrate healthScore.
 */
export async function getPIMHealthSnapshot(
  req: PIMHealthSnapshotRequest
): Promise<PIMHealthSnapshot> {
  const supabase = supabaseServer;

  const since = new Date();
  since.setHours(since.getHours() - req.windowHours);

  const { data, error } = await ((supabase as any)
    .from('jarvis_pim_provider_events')
    .select('latency_ms, event_type')
    .eq('workspace_id', req.workspaceId)
    .eq('provider', req.provider)
    .eq('channel', req.channel as ProviderChannel)
    .gte('occurred_at', since.toISOString()));

  if (error) {
    console.error('[PIM] getPIMHealthSnapshot error:', error);
    // In case of DB error, return a worst-case snapshot with healthScore 0
    return {
      provider: req.provider,
      channel: req.channel,
      windowHours: req.windowHours,
      messagesTotal: 0,
      messagesFailed: 0,
      failureRate: 1,
      avgLatencyMs: null,
      p95LatencyMs: null,
      jitterMs: null,
      healthScore: 0
    };
  }

  const rows = (data ?? []) as RawEventRow[];

  const messagesTotal = rows.length;
  const messagesFailed = rows.filter((r) => r.event_type === 'failed').length;
  const failureRate = messagesTotal ? messagesFailed / messagesTotal : 0;

  const latencies = rows
    .map((r) => (typeof r.latency_ms === 'number' ? r.latency_ms : null))
    .filter((v): v is number => v !== null);

  const avgLatencyMs =
    latencies.length > 0
      ? latencies.reduce((sum, v) => sum + v, 0) / latencies.length
      : null;

  const p95LatencyMs = computePercentile(latencies, 95);
  const jitterMs = computeStdDev(latencies);

  const healthScore = computeHealthScore({
    failureRate,
    p95LatencyMs,
    jitterMs
  });

  return {
    provider: req.provider,
    channel: req.channel,
    windowHours: req.windowHours,
    messagesTotal,
    messagesFailed,
    failureRate,
    avgLatencyMs: avgLatencyMs !== null ? Number(avgLatencyMs.toFixed(2)) : null,
    p95LatencyMs: p95LatencyMs !== null ? Number(p95LatencyMs.toFixed(2)) : null,
    jitterMs: jitterMs !== null ? Number(jitterMs.toFixed(2)) : null,
    healthScore
  };
}

