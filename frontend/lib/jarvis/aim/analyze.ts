import { supabaseServer } from '@/lib/supabase/server';
import { AIMAnomalyDetectionInput, AIMAnomalyDetectionResult, AIMEntityType } from './types';

// Adjust this type to match your actual jarvis_events schema.
type JarvisEventRow = {
  id: string;
  workspace_id: string;
  user_id: string | null;
  event_type: string;
  created_at: string;
  payload: any;
};

type WorkspaceDailyStats = {
  workspace_id: string;
  date_bucket: string;
  msg_total: number;
  call_total: number;
  email_total: number;
  hoursHistogram: Record<number, number>; // hour -> event count
};

function getDateBucket(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function ensureUserActivityKey(
  map: Map<string, {
    workspace_id: string;
    user_id: string;
    date_bucket: string;
    messages_sent: number;
    messages_received: number;
    calls_made: number;
    calls_received: number;
    emails_sent: number;
    emails_received: number;
    active_minutes: number;
  }>,
  key: string,
  workspaceId: string,
  userId: string,
  dateBucket: string
) {
  if (!map.has(key)) {
    map.set(key, {
      workspace_id: workspaceId,
      user_id: userId,
      date_bucket: dateBucket,
      messages_sent: 0,
      messages_received: 0,
      calls_made: 0,
      calls_received: 0,
      emails_sent: 0,
      emails_received: 0,
      active_minutes: 0
    });
  }
}

function ensureWorkspaceDailyStats(
  map: Map<string, WorkspaceDailyStats>,
  workspaceId: string,
  dateBucket: string
) {
  const key = `${workspaceId}:${dateBucket}`;
  if (!map.has(key)) {
    map.set(key, {
      workspace_id: workspaceId,
      date_bucket: dateBucket,
      msg_total: 0,
      call_total: 0,
      email_total: 0,
      hoursHistogram: {}
    });
  }
  return map.get(key)!;
}

// Basic anomaly detection using z-scores on msg_total/call_total/email_total.
export function detectAIMAnomaly(
  input: AIMAnomalyDetectionInput
): AIMAnomalyDetectionResult {
  const metrics = input.metrics;
  const mean = input.baselineStats.mean;
  const stddev = input.baselineStats.stddev;

  let maxDeviation = 0;
  let anomalyType: string | undefined;
  const details: string[] = [];

  for (const key of Object.keys(metrics)) {
    const m = metrics[key];
    const mu = mean[key] ?? 0;
    const sigma = stddev[key] ?? 0;

    if (sigma === 0) {
      // If no variation, treat any non-zero delta beyond small epsilon as potential anomaly.
      if (Math.abs(m - mu) > mu * 0.5 && mu > 0) {
        const severity = 0.7;
        if (severity > maxDeviation) {
          maxDeviation = severity;
          anomalyType = m > mu ? 'volume_spike' : 'volume_drop';
        }
        details.push(`${key}: baseline=${mu}, current=${m} (sigma=0)`);
      }
      continue;
    }

    const z = (m - mu) / sigma;
    const absZ = Math.abs(z);
    if (absZ > maxDeviation) {
      maxDeviation = absZ;
      anomalyType = z > 0 ? 'volume_spike' : 'volume_drop';
    }
    details.push(`${key}: z=${z.toFixed(2)} (baseline=${mu}, current=${m}, sigma=${sigma})`);
  }

  // Threshold: consider anomaly if |z| > 2
  if (!anomalyType || maxDeviation <= 2) {
    return {
      anomaly: false,
      severity: 0,
      anomalyType: undefined,
      notes: details.join('; ')
    };
  }

  // Map z-score to severity in 0–1 roughly
  const severity = Math.min(1, maxDeviation / 4); // z=4 => severity ~1

  return {
    anomaly: true,
    severity,
    anomalyType,
    notes: details.join('; ')
  };
}

/**
 * IT-10B:
 * Roll up recent events into user activity and enterprise cycles.
 * This function is designed to be called periodically via a cron route.
 *
 * Strategy:
 * - Query jarvis_events in a recent time window (e.g. last 10 minutes).
 * - For each event, classify it as message/call/email and direction.
 * - Aggregate into per-user and per-workspace daily counts.
 * - Upsert into jarvis_aim_user_activity and jarvis_aim_enterprise_cycles.
 */
export async function rollupRecentActivity(windowMinutes = 10): Promise<{
  processedEvents: number;
  userUpserts: number;
  workspaceUpserts: number;
}> {
  const supabase = supabaseServer;

  const since = new Date();
  since.setMinutes(since.getMinutes() - windowMinutes);

  const { data, error } = await ((supabase as any)
    .from('jarvis_events')
    .select('id, workspace_id, user_id, event_type, created_at, payload')
    .gte('created_at', since.toISOString()));

  if (error) {
    console.error('[AIM] rollupRecentActivity query error:', error);
    throw error;
  }

  const events = (data ?? []) as JarvisEventRow[];
  if (!events.length) {
    return { processedEvents: 0, userUpserts: 0, workspaceUpserts: 0 };
  }

  const userMap = new Map<
    string,
    {
      workspace_id: string;
      user_id: string;
      date_bucket: string;
      messages_sent: number;
      messages_received: number;
      calls_made: number;
      calls_received: number;
      emails_sent: number;
      emails_received: number;
      active_minutes: number;
    }
  >();

  const workspaceMap = new Map<string, WorkspaceDailyStats>();

  for (const ev of events) {
    const workspaceId = ev.workspace_id;
    const userId = ev.user_id ?? '00000000-0000-0000-0000-000000000000'; // fallback if null
    const createdAt = new Date(ev.created_at);
    const dateBucket = getDateBucket(createdAt);
    const hour = createdAt.getHours();
    const type = ev.event_type;

    // Classify event as message/call/email & direction
    let isMessage = false;
    let isCall = false;
    let isEmail = false;
    let direction: 'sent' | 'received' | 'unknown' = 'unknown';

    if (type.startsWith('external.provider.ghexit.')) {
      if (type.includes('.sms.')) {
        isMessage = true;
      } else if (type.includes('.mms.')) {
        isMessage = true;
      } else if (type.includes('.email.')) {
        isEmail = true;
      } else if (type.includes('.voice.')) {
        isCall = true;
      }

      if (type.endsWith('.sent')) direction = 'sent';
      if (type.endsWith('.received')) direction = 'received';
      if (type.endsWith('.started')) direction = 'sent';
    }

    if (!isMessage && !isCall && !isEmail) {
      // ignore non-communication events for AIM rollup
      continue;
    }

    // Per-user aggregation
    const userKey = `${workspaceId}:${userId}:${dateBucket}`;
    ensureUserActivityKey(userMap, userKey, workspaceId, userId, dateBucket);
    const userEntry = userMap.get(userKey)!;

    if (isMessage) {
      if (direction === 'sent') userEntry.messages_sent += 1;
      else if (direction === 'received') userEntry.messages_received += 1;
      else userEntry.messages_sent += 1;
    }

    if (isCall) {
      if (direction === 'sent') userEntry.calls_made += 1;
      else if (direction === 'received') userEntry.calls_received += 1;
      else userEntry.calls_made += 1;
    }

    if (isEmail) {
      if (direction === 'sent') userEntry.emails_sent += 1;
      else if (direction === 'received') userEntry.emails_received += 1;
      else userEntry.emails_sent += 1;
    }

    // Approx engagement: each event contributes a small amount
    userEntry.active_minutes += 1;

    // Per-workspace daily stats
    const wsStats = ensureWorkspaceDailyStats(workspaceMap, workspaceId, dateBucket);
    if (isMessage) wsStats.msg_total += 1;
    if (isCall) wsStats.call_total += 1;
    if (isEmail) wsStats.email_total += 1;

    wsStats.hoursHistogram[hour] = (wsStats.hoursHistogram[hour] ?? 0) + 1;
  }

  // Upsert user activity
  const userRows = Array.from(userMap.values());
  let userUpserts = 0;
  if (userRows.length > 0) {
    const { error: userError } = await ((supabase as any)
      .from('jarvis_aim_user_activity')
      .upsert(userRows, {
        onConflict: 'workspace_id,user_id,date_bucket'
      }));

    if (userError) {
      console.error('[AIM] rollupRecentActivity user upsert error:', userError);
      throw userError;
    }

    userUpserts = userRows.length;
  }

  // Upsert workspace cycles
  const workspaceRows = Array.from(workspaceMap.values()).map((ws) => {
    const histogram = ws.hoursHistogram;
    const entries = Object.entries(histogram);
    let peakHour: number | null = null;
    let offPeakHour: number | null = null;

    if (entries.length > 0) {
      entries.sort((a, b) => (b[1] as number) - (a[1] as number));
      peakHour = Number(entries[0][0]);
      offPeakHour = Number(entries[entries.length - 1][0]);
    }

    // naive cycle_score: more concentrated hours => higher score
    const totalEvents = entries.reduce((sum, [, count]) => sum + (count as number), 0);
    let cycleScore: number | null = null;
    if (totalEvents > 0) {
      const peakCount = entries[0]?.[1] as number;
      const ratio = peakCount / totalEvents;
      cycleScore = Number(Math.min(1, Math.max(0, ratio)).toFixed(3));
    }

    return {
      workspace_id: ws.workspace_id,
      date_bucket: ws.date_bucket,
      msg_total: ws.msg_total,
      call_total: ws.call_total,
      email_total: ws.email_total,
      peak_hour_local: peakHour,
      off_peak_hour_local: offPeakHour,
      weekday_pattern: null,
      cycle_score: cycleScore
    };
  });

  let workspaceUpserts = 0;
  if (workspaceRows.length > 0) {
    const { error: wsError } = await ((supabase as any)
      .from('jarvis_aim_enterprise_cycles')
      .upsert(workspaceRows, {
        onConflict: 'workspace_id,date_bucket'
      }));

    if (wsError) {
      console.error('[AIM] rollupRecentActivity workspace upsert error:', wsError);
      throw wsError;
    }

    workspaceUpserts = workspaceRows.length;
  }

  return {
    processedEvents: events.length,
    userUpserts,
    workspaceUpserts
  };
}

/**
 * IT-10B:
 * Run anomaly detection at workspace level using jarvis_aim_enterprise_cycles.
 *
 * Strategy:
 * - For each workspace with sufficient history, fetch the last N days of cycles (e.g. 8).
 * - Use first N-1 days as baseline; last day as "current".
 * - Compute basic stats and run detectAIMAnomaly.
 * - If anomaly, insert into jarvis_aim_anomalies.
 */
export async function detectWorkspaceAnomaliesForRecentDay(
  baselineDays = 7
): Promise<{ workspacesChecked: number; anomaliesInserted: number }> {
  const supabase = supabaseServer;

  // Get distinct workspace_ids that have enterprise_cycles data
  const { data: wsData, error: wsErr } = await ((supabase as any)
    .from('jarvis_aim_enterprise_cycles')
    .select('workspace_id')
    .limit(1000)
    .order('workspace_id', { ascending: true }));

  if (wsErr) {
    console.error('[AIM] detectWorkspaceAnomaliesForRecentDay workspace query error:', wsErr);
    throw wsErr;
  }

  const workspaceIds = Array.from(
    new Set((wsData ?? []).map((r: any) => r.workspace_id as string))
  ) as string[];

  let workspacesChecked = 0;
  let anomaliesInserted = 0;

  for (const workspaceId of workspaceIds) {
    // fetch last baselineDays+1 entries for this workspace
    const { data: cycleData, error: cycleErr } = await ((supabase as any)
      .from('jarvis_aim_enterprise_cycles')
      .select('date_bucket, msg_total, call_total, email_total')
      .eq('workspace_id', workspaceId)
      .order('date_bucket', { ascending: true })
      .limit(baselineDays + 1));

    if (cycleErr) {
      console.error(
        '[AIM] detectWorkspaceAnomaliesForRecentDay cycles error:',
        workspaceId,
        cycleErr
      );
      continue;
    }

    const cycles = cycleData ?? [];
    if (cycles.length < baselineDays + 1) {
      continue;
    }

    workspacesChecked += 1;

    const baseline = cycles.slice(0, baselineDays);
    const current = cycles[cycles.length - 1];

    const metricKeys: Array<'msg_total' | 'call_total' | 'email_total'> = [
      'msg_total',
      'call_total',
      'email_total'
    ];

    const mean: Record<string, number> = {};
    const stddev: Record<string, number> = {};

    for (const key of metricKeys) {
      const vals = baseline.map((c) => (c as any)[key] as number);
      const mu = vals.reduce((sum, v) => sum + v, 0) / vals.length;
      const variance =
        vals.length > 1
          ? vals.reduce((sum, v) => sum + Math.pow(v - mu, 2), 0) / (vals.length - 1)
          : 0;
      const sigma = Math.sqrt(variance);
      mean[key] = mu;
      stddev[key] = sigma;
    }

    const metrics: Record<string, number> = {
      msg_total: (current as any).msg_total ?? 0,
      call_total: (current as any).call_total ?? 0,
      email_total: (current as any).email_total ?? 0
    };

    const anomalyResult = detectAIMAnomaly({
      workspaceId,
      entityType: 'workspace',
      metrics,
      baselineStats: { mean, stddev }
    });

    if (!anomalyResult.anomaly) {
      continue;
    }

    const { error: insertErr } = await ((supabase as any)
      .from('jarvis_aim_anomalies')
      .insert({
        workspace_id: workspaceId,
        entity_type: 'workspace' as AIMEntityType,
        entity_id: null,
        detected_at: new Date().toISOString(),
        anomaly_type: anomalyResult.anomalyType ?? 'unknown',
        severity: anomalyResult.severity,
        baseline_window: `${baselineDays}d`,
        notes: anomalyResult.notes ?? null,
        raw_metrics: metrics
      }));

    if (insertErr) {
      console.error(
        '[AIM] detectWorkspaceAnomaliesForRecentDay insert anomaly error:',
        workspaceId,
        insertErr
      );
      continue;
    }

    anomaliesInserted += 1;
  }

  return { workspacesChecked, anomaliesInserted };
}

