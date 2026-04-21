import { supabaseServer } from '@/lib/supabase/server';
import { RoutingDecisionResult, RoutingStrategy } from './types';
import { computeRoutingRecommendation } from '@/lib/jarvis/prediction/engine';

type RoutingProviderRow = {
  id: string;
  workspace_id: string;
  provider_key: string;
  channel: string;
  display_name: string | null;
  base_weight: number;
  region: string | null;
  cost_per_unit: number | null;
  status: string;
  is_default: boolean;
  metadata: any;
  created_at: string;
  updated_at: string;
};

type RoutingPolicyRow = {
  id: string;
  workspace_id: string;
  channel: string;
  strategy: string;
  health_threshold: number;
  max_failure_rate: number;
  max_latency_ms: number;
  prefer_low_cost: boolean;
  metadata: any;
  created_at: string;
  updated_at: string;
};

const DEFAULT_STRATEGY: RoutingStrategy = 'weighted';

function normalizeStrategy(strategy?: string | null): RoutingStrategy {
  if (!strategy) return DEFAULT_STRATEGY;
  if (
    strategy === 'weighted' ||
    strategy === 'latency_optimized' ||
    strategy === 'cost_optimized' ||
    strategy === 'failover'
  ) {
    return strategy;
  }
  return DEFAULT_STRATEGY;
}

export async function chooseRoutingProvider(input: {
  workspaceId: string;
  channel: string;
  region?: string;
  requestId?: string;
}): Promise<RoutingDecisionResult> {
  const { workspaceId, channel, region, requestId } = input;
  const supabase = supabaseServer;

  // 1) Load providers
  const { data: providersData, error: providersError } = await ((supabase as any)
    .from('jarvis_routing_providers')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('channel', channel)
    .in('status', ['active', 'degraded']));

  if (providersError) {
    console.error('[Routing] providers query error:', providersError);
  }

  let providers = (providersData ?? []) as RoutingProviderRow[];

  if (region) {
    // prefer providers matching region, but allow null region if none
    const regionMatches = providers.filter(
      (p) => p.region && p.region === region
    );
    if (regionMatches.length > 0) {
      providers = regionMatches;
    }
  }

  if (providers.length === 0) {
    const result: RoutingDecisionResult = {
      providerKey: null,
      strategy: DEFAULT_STRATEGY,
      score: null,
      reason: 'No routing providers configured for this workspace/channel.',
      debug: {
        policy: {
          strategy: DEFAULT_STRATEGY,
          healthThreshold: 0.6,
          maxFailureRate: 0.05,
          maxLatencyMs: 1500,
          preferLowCost: false
        },
        candidates: []
      }
    };

    // Log decision
    await ((supabase as any).from('jarvis_routing_decisions').insert({
      workspace_id: workspaceId,
      channel,
      request_id: requestId ?? null,
      chosen_provider_key: null,
      strategy: DEFAULT_STRATEGY,
      score: null,
      reason: result.reason,
      snapshot: result.debug
    }));

    return result;
  }

  // 2) Load policy
  const { data: policyData, error: policyError } = await ((supabase as any)
    .from('jarvis_routing_policies')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('channel', channel)
    .maybeSingle());

  if (policyError) {
    console.error('[Routing] policy query error:', policyError);
  }

  const policy = policyData as RoutingPolicyRow | null;

  const strategy = normalizeStrategy(policy?.strategy);
  const healthThreshold = Number(policy?.health_threshold ?? 0.6);
  const maxFailureRate = Number(policy?.max_failure_rate ?? 0.05);
  const maxLatencyMs = Number(policy?.max_latency_ms ?? 1500);
  const preferLowCost = Boolean(policy?.prefer_low_cost ?? false);

  // 3) Build candidate metrics (uses IT-10C routing recommendation)
  const candidates: RoutingDecisionResult['debug']['candidates'] = [];

  // track max cost for normalization
  let maxCost = 0;
  for (const p of providers) {
    if (p.cost_per_unit != null) {
      const v = Number(p.cost_per_unit);
      if (v > maxCost) maxCost = v;
    }
  }
  if (maxCost <= 0) maxCost = 1;

  for (const provider of providers) {
    try {
      const routing = await computeRoutingRecommendation({
        workspaceId,
        provider: provider.provider_key,
        channel
      });

      const healthScore =
        routing.factors.currentHealthScore != null
          ? Number(routing.factors.currentHealthScore)
          : routing.score ?? null;

      const predictedFailureRate =
        routing.factors.predictedFailureRate != null
          ? Number(routing.factors.predictedFailureRate)
          : null;

      const predictedP95LatencyMs =
        routing.factors.predictedP95LatencyMs != null
          ? Number(routing.factors.predictedP95LatencyMs)
          : null;

      const baseWeight = Number(provider.base_weight ?? 1) || 1;
      const costPerUnit =
        provider.cost_per_unit != null ? Number(provider.cost_per_unit) : null;

      const routingScore = routing.score ?? null;

      // Basic combined score for weighted strategy
      const effectiveHealth = healthScore ?? (routingScore ?? 0.7);

      const failurePenalty =
        predictedFailureRate != null
          ? 1 - Math.min(1, predictedFailureRate * 5) // >20% failure → heavy penalty
          : 1;

      const latencyPenalty =
        predictedP95LatencyMs != null
          ? Math.min(1, predictedP95LatencyMs / 3000)
          : 0;

      const costPenalty =
        costPerUnit != null ? Math.min(1, costPerUnit / maxCost) : 0.5;

      let combinedScore =
        baseWeight *
        effectiveHealth *
        failurePenalty *
        (1 - 0.3 * latencyPenalty);

      if (preferLowCost) {
        combinedScore *= 1 - 0.3 * costPenalty;
      }

      candidates.push({
        providerKey: provider.provider_key,
        displayName: provider.display_name ?? null,
        channel,
        baseWeight,
        status: provider.status ?? 'active',
        region: provider.region ?? null,
        costPerUnit,
        healthScore,
        routingScore,
        predictedFailureRate,
        predictedP95LatencyMs,
        combinedScore
      });
    } catch (err) {
      console.error(
        '[Routing] computeRoutingRecommendation error for provider',
        provider.provider_key,
        err
      );
      candidates.push({
        providerKey: provider.provider_key,
        displayName: provider.display_name ?? null,
        channel,
        baseWeight: Number(provider.base_weight ?? 1) || 1,
        status: provider.status ?? 'active',
        region: provider.region ?? null,
        costPerUnit:
          provider.cost_per_unit != null
            ? Number(provider.cost_per_unit)
            : null,
        healthScore: null,
        routingScore: null,
        predictedFailureRate: null,
        predictedP95LatencyMs: null,
        combinedScore: null
      });
    }
  }

  // Filter out any with non-positive combinedScore where relevant
  const positiveCandidates = candidates.filter(
    (c) => c.combinedScore && c.combinedScore > 0
  );
  const effectiveCandidates =
    strategy === 'weighted' && positiveCandidates.length > 0
      ? positiveCandidates
      : candidates;

  let chosen: (typeof candidates)[number] | null = null;
  let finalScore: number | null = null;
  let reason = '';

  if (effectiveCandidates.length === 0) {
    const result: RoutingDecisionResult = {
      providerKey: null,
      strategy,
      score: null,
      reason: 'No viable routing candidates after scoring.',
      debug: {
        policy: {
          strategy,
          healthThreshold,
          maxFailureRate,
          maxLatencyMs,
          preferLowCost
        },
        candidates
      }
    };

    await ((supabase as any).from('jarvis_routing_decisions').insert({
      workspace_id: workspaceId,
      channel,
      request_id: requestId ?? null,
      chosen_provider_key: null,
      strategy,
      score: null,
      reason: result.reason,
      snapshot: result.debug
    }));

    return result;
  }

  if (strategy === 'weighted') {
    const totalScore = effectiveCandidates.reduce(
      (sum, c) => sum + (c.combinedScore ?? 0),
      0
    );
    let r = Math.random() * totalScore;
    for (const c of effectiveCandidates) {
      const s = c.combinedScore ?? 0;
      if (r <= s) {
        chosen = c;
        break;
      }
      r -= s;
    }
    if (!chosen) {
      chosen = effectiveCandidates[effectiveCandidates.length - 1];
    }
    finalScore = chosen.combinedScore ?? null;
    reason = `Selected ${chosen.providerKey} for ${channel} using weighted strategy (${effectiveCandidates.length} candidates).`;
  } else if (strategy === 'latency_optimized') {
    // Choose the provider with the lowest predicted latency
    const sorted = [...effectiveCandidates].sort((a, b) => {
      const la = a.predictedP95LatencyMs ?? Number.MAX_SAFE_INTEGER;
      const lb = b.predictedP95LatencyMs ?? Number.MAX_SAFE_INTEGER;
      if (la === lb) {
        const ha = a.healthScore ?? 0;
        const hb = b.healthScore ?? 0;
        return hb - ha;
      }
      return la - lb;
    });
    chosen = sorted[0];
    finalScore =
      chosen.predictedP95LatencyMs != null
        ? 1 - Math.min(1, chosen.predictedP95LatencyMs / 3000)
        : null;
    reason = `Selected ${chosen.providerKey} for ${channel} using latency_optimized strategy.`;
  } else if (strategy === 'cost_optimized') {
    // Choose provider with best cost/effectiveHealth ratio
    const sorted = [...effectiveCandidates].sort((a, b) => {
      const ca = a.costPerUnit ?? Number.MAX_SAFE_INTEGER;
      const cb = b.costPerUnit ?? Number.MAX_SAFE_INTEGER;
      const ha = a.healthScore ?? 0.5;
      const hb = b.healthScore ?? 0.5;

      const ra = ca / Math.max(ha, 0.1);
      const rb = cb / Math.max(hb, 0.1);

      if (ra === rb) {
        return (b.healthScore ?? 0) - (a.healthScore ?? 0);
      }
      return ra - rb;
    });
    chosen = sorted[0];
    finalScore =
      chosen.costPerUnit != null ? 1 / (1 + chosen.costPerUnit) : null;
    reason = `Selected ${chosen.providerKey} for ${channel} using cost_optimized strategy.`;
  } else if (strategy === 'failover') {
    const eligible = effectiveCandidates.filter((c) => {
      const hs = c.healthScore ?? 0;
      const fr = c.predictedFailureRate ?? 0;
      const lat = c.predictedP95LatencyMs ?? 0;
      return (
        hs >= healthThreshold &&
        fr <= maxFailureRate &&
        (lat === 0 || lat <= maxLatencyMs)
      );
    });

    if (eligible.length > 0) {
      const sorted = [...eligible].sort(
        (a, b) => (b.healthScore ?? 0) - (a.healthScore ?? 0)
      );
      chosen = sorted[0];
      finalScore = chosen.healthScore ?? null;
      reason = `Selected ${chosen.providerKey} for ${channel} using failover strategy (passed thresholds).`;
    } else {
      const sorted = [...effectiveCandidates].sort(
        (a, b) => (b.healthScore ?? 0) - (a.healthScore ?? 0)
      );
      chosen = sorted[0];
      finalScore = chosen.healthScore ?? null;
      reason = `Selected ${chosen.providerKey} for ${channel} using failover strategy (best available, no provider met thresholds).`;
    }
  } else {
    // default backstop
    chosen = effectiveCandidates[0];
    finalScore = chosen.combinedScore ?? null;
    reason = `Selected ${chosen.providerKey} for ${channel} using default strategy fallback.`;
  }

  const result: RoutingDecisionResult = {
    providerKey: chosen.providerKey,
    strategy,
    score: finalScore,
    reason,
    debug: {
      policy: {
        strategy,
        healthThreshold,
        maxFailureRate,
        maxLatencyMs,
        preferLowCost
      },
      candidates
    }
  };

  await ((supabase as any).from('jarvis_routing_decisions').insert({
    workspace_id: workspaceId,
    channel,
    request_id: requestId ?? null,
    chosen_provider_key: chosen.providerKey,
    strategy,
    score: finalScore,
    reason,
    snapshot: result.debug
  }));

  return result;
}

