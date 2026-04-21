import { supabaseServer } from '@/lib/supabase/server';
import {
  IncidentStatus,
  IncidentStepStatus,
  IncidentStepType,
  PlaybookStepConfig
} from './types';
import { AgentAction } from '@/lib/jarvis/agents/types';
import { executeAgentAction } from '@/lib/jarvis/agents/actions';

type IncidentRow = {
  id: string;
  workspace_id: string;
  playbook_id: string | null;
  status: string;
  severity: string;
  title: string;
  description: string | null;
  context: any;
  opened_at: string;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
};

type PlaybookRow = {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  is_enabled: boolean;
  trigger_source: string;
  trigger_matcher: any;
  default_severity: string;
  steps: any;
  created_at: string;
  updated_at: string;
};

type AlertEventRow = {
  id: string;
  workspace_id: string;
  rule_id: string;
  triggered_at: string;
  event_type: string;
  payload: any;
  delivery_channel: string;
  delivery_status: string;
  created_at: string;
};

type IncidentStepRow = {
  id: string;
  incident_id: string;
  step_index: number;
  step_type: string;
  status: string;
  config: any;
  result: any;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

function nowIso() {
  return new Date().toISOString();
}

function matchPlaybookTriggerWithAlert(
  playbook: PlaybookRow,
  alert: AlertEventRow
): boolean {
  if (!playbook.trigger_matcher) return false;
  const matcher = playbook.trigger_matcher as any;
  const alertMatcher = matcher.alert;
  if (!alertMatcher) return false;

  // event_type match
  if (alertMatcher.event_type && alertMatcher.event_type !== alert.event_type) {
    return false;
  }

  // optional source match inside payload
  if (alertMatcher.source) {
    const src =
      (alert.payload as any)?.source ??
      (alert.payload as any)?.condition?.source ??
      null;
    if (src !== alertMatcher.source) {
      return false;
    }
  }

  // optional channel match inside payload
  if (alertMatcher.channel) {
    const ch =
      (alert.payload as any)?.channel ??
      (alert.payload as any)?.metadata?.channel ??
      null;
    if (ch !== alertMatcher.channel) {
      return false;
    }
  }

  return true;
}

/**
 * Open a new incident from an alert event.
 */
export async function openIncidentFromAlert(input: {
  workspaceId: string;
  alertId: string;
}): Promise<IncidentRow | null> {
  const { workspaceId, alertId } = input;
  const supabase = supabaseServer;

  const { data: alertData, error: alertError } = await ((supabase as any)
    .from('jarvis_alert_events')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('id', alertId)
    .maybeSingle());

  if (alertError) {
    console.error('[Incidents] openIncidentFromAlert alert query error:', alertError);
    return null;
  }

  if (!alertData) {
    console.warn('[Incidents] openIncidentFromAlert: alert not found', {
      workspaceId,
      alertId
    });
    return null;
  }

  const alert = alertData as AlertEventRow;

  // Find a matching playbook
  const { data: playbooksData, error: pbError } = await ((supabase as any)
    .from('jarvis_incident_playbooks')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('is_enabled', true)
    .eq('trigger_source', 'alert'));

  if (pbError) {
    console.error('[Incidents] playbooks query error:', pbError);
    return null;
  }

  const playbooks = (playbooksData ?? []) as PlaybookRow[];

  let matchedPlaybook: PlaybookRow | null = null;

  for (const pb of playbooks) {
    if (matchPlaybookTriggerWithAlert(pb, alert)) {
      matchedPlaybook = pb;
      break;
    }
  }

  const severity = matchedPlaybook?.default_severity ?? 'medium';
  const title =
    `Alert: ${alert.event_type}` +
    (alert.delivery_channel ? ` (${alert.delivery_channel})` : '');

  const { data: incidentInsert, error: incidentError } = await ((supabase as any)
    .from('jarvis_incidents')
    .insert({
      workspace_id: workspaceId,
      playbook_id: matchedPlaybook?.id ?? null,
      status: 'open' as IncidentStatus,
      severity,
      title,
      description: `Incident created from alert ${alert.id}`,
      context: alert,
      opened_at: nowIso(),
      created_at: nowIso(),
      updated_at: nowIso()
    })
    .select('*')
    .maybeSingle());

  if (incidentError) {
    console.error('[Incidents] incident insert error:', incidentError);
    return null;
  }

  const incident = incidentInsert as IncidentRow;

  // Materialize steps from playbook if available
  if (matchedPlaybook && Array.isArray(matchedPlaybook.steps)) {
    const steps = (matchedPlaybook.steps as any[]).map((s, idx) => {
      const stepConfig: PlaybookStepConfig = {
        index: typeof s.index === 'number' ? s.index : idx,
        type: s.type as IncidentStepType,
        config: s.config
      };
      return stepConfig;
    });

    if (steps.length > 0) {
      const stepRows = steps.map((s) => ({
        incident_id: incident.id,
        step_index: s.index,
        step_type: s.type,
        status: 'pending' as IncidentStepStatus,
        config: s.config,
        created_at: nowIso(),
        updated_at: nowIso()
      }));

      const { error: stepsError } = await ((supabase as any)
        .from('jarvis_incident_steps')
        .insert(stepRows));

      if (stepsError) {
        console.error('[Incidents] incident steps insert error:', stepsError);
      }
    }
  }

  return incident;
}

/**
 * Open a manual incident (optionally linked to a playbook).
 */
export async function openIncidentManual(input: {
  workspaceId: string;
  title: string;
  severity?: string;
  description?: string;
  context?: any;
  playbookId?: string | null;
}): Promise<IncidentRow | null> {
  const { workspaceId, title, severity, description, context, playbookId } = input;
  const supabase = supabaseServer;
  const now = nowIso();

  let playbook: PlaybookRow | null = null;

  if (playbookId) {
    const { data: pbData, error: pbError } = await ((supabase as any)
      .from('jarvis_incident_playbooks')
      .select('*')
      .eq('workspace_id', workspaceId)
      .eq('id', playbookId)
      .maybeSingle());

    if (pbError) {
      console.error('[Incidents] openIncidentManual playbook query error:', pbError);
    } else {
      playbook = pbData as PlaybookRow | null;
    }
  }

  const effSeverity = severity ?? playbook?.default_severity ?? 'medium';

  const { data: incidentInsert, error: incidentError } = await ((supabase as any)
    .from('jarvis_incidents')
    .insert({
      workspace_id: workspaceId,
      playbook_id: playbook?.id ?? playbookId ?? null,
      status: 'open' as IncidentStatus,
      severity: effSeverity,
      title,
      description: description ?? null,
      context: context ?? null,
      opened_at: now,
      created_at: now,
      updated_at: now
    })
    .select('*')
    .maybeSingle());

  if (incidentError) {
    console.error('[Incidents] openIncidentManual insert error:', incidentError);
    return null;
  }

  const incident = incidentInsert as IncidentRow;

  // If playbook exists, materialize steps
  if (playbook && Array.isArray(playbook.steps)) {
    const steps = (playbook.steps as any[]).map((s, idx) => {
      const stepConfig: PlaybookStepConfig = {
        index: typeof s.index === 'number' ? s.index : idx,
        type: s.type as IncidentStepType,
        config: s.config
      };
      return stepConfig;
    });

    if (steps.length > 0) {
      const stepRows = steps.map((s) => ({
        incident_id: incident.id,
        step_index: s.index,
        step_type: s.type,
        status: 'pending' as IncidentStepStatus,
        config: s.config,
        created_at: nowIso(),
        updated_at: nowIso()
      }));

      const { error: stepsError } = await ((supabase as any)
        .from('jarvis_incident_steps')
        .insert(stepRows));

      if (stepsError) {
        console.error('[Incidents] openIncidentManual steps insert error:', stepsError);
      }
    }
  }

  return incident;
}

/**
 * Run the next pending step for an incident.
 */
export async function runNextIncidentStep(incidentId: string): Promise<{
  step: IncidentStepRow | null;
  incident: IncidentRow | null;
}> {
  const supabase = supabaseServer;

  const { data: incidentData, error: incidentError } = await ((supabase as any)
    .from('jarvis_incidents')
    .select('*')
    .eq('id', incidentId)
    .maybeSingle());

  if (incidentError) {
    console.error('[Incidents] runNextIncidentStep incident query error:', incidentError);
    return { step: null, incident: null };
  }

  if (!incidentData) {
    console.warn('[Incidents] runNextIncidentStep: incident not found', incidentId);
    return { step: null, incident: null };
  }

  const incident = incidentData as IncidentRow;

  const { data: stepsData, error: stepsError } = await ((supabase as any)
    .from('jarvis_incident_steps')
    .select('*')
    .eq('incident_id', incidentId)
    .order('step_index', { ascending: true }));

  if (stepsError) {
    console.error('[Incidents] runNextIncidentStep steps query error:', stepsError);
    return { step: null, incident };
  }

  const steps = (stepsData ?? []) as IncidentStepRow[];

  const pending = steps.find((s) => s.status === ('pending' as IncidentStepStatus));

  if (!pending) {
    // No pending steps: mark resolved if not already
    if (incident.status !== 'resolved') {
      const now = nowIso();
      const { error: updateError } = await ((supabase as any)
        .from('jarvis_incidents')
        .update({
          status: 'resolved' as IncidentStatus,
          resolved_at: now,
          updated_at: now
        })
        .eq('id', incident.id));

      if (updateError) {
        console.error('[Incidents] runNextIncidentStep resolve incident error:', updateError);
      }
    }
    return { step: null, incident };
  }

  const now = nowIso();

  // Mark step as running
  const { error: startError } = await ((supabase as any)
    .from('jarvis_incident_steps')
    .update({
      status: 'running' as IncidentStepStatus,
      started_at: now,
      updated_at: now
    })
    .eq('id', pending.id));

  if (startError) {
    console.error('[Incidents] runNextIncidentStep start step error:', startError);
    return { step: null, incident };
  }

  let stepStatus: IncidentStepStatus = 'completed';
  let result: any = null;

  const config = pending.config as any;
  const stepType = pending.step_type as IncidentStepType;

  try {
    if (stepType === 'notify') {
      console.log('[Incidents] notify step:', {
        incidentId: incident.id,
        message: config?.message,
        channel: config?.channel ?? 'log'
      });
      result = { delivered: true };
    } else if (stepType === 'agentAction') {
      const action = config?.action as AgentAction;
      if (!action || typeof action !== 'object') {
        throw new Error('Invalid agentAction config: missing action');
      }
      const execRes = await executeAgentAction(action);
      result = execRes;
      stepStatus = execRes.status === 'success' ? 'completed' : 'failed';
    } else if (stepType === 'runAgentRule') {
      console.log('[Incidents] runAgentRule step (stub):', config);
      result = { stub: true };
      stepStatus = 'completed';
    } else if (stepType === 'wait') {
      console.log('[Incidents] wait step (no-op for now):', config);
      result = { stub: true };
      stepStatus = 'completed';
    } else if (stepType === 'manualCheck') {
      console.log('[Incidents] manualCheck step (mark as skipped for now):', config);
      result = { stub: true };
      stepStatus = 'skipped';
    } else {
      console.warn('[Incidents] unknown step type, skipping:', stepType);
      result = { stub: true, unknownType: stepType };
      stepStatus = 'skipped';
    }
  } catch (err: any) {
    console.error('[Incidents] step execution error:', err);
    stepStatus = 'failed';
    result = { error: err.message ?? 'Unknown error' };
  }

  const completedAt = nowIso();

  const { data: updatedStepData, error: finishError } = await ((supabase as any)
    .from('jarvis_incident_steps')
    .update({
      status: stepStatus,
      result,
      completed_at: completedAt,
      updated_at: completedAt
    })
    .eq('id', pending.id)
    .select('*')
    .maybeSingle());

  if (finishError) {
    console.error('[Incidents] runNextIncidentStep finish error:', finishError);
  }

  // Update incident status to in_progress if it was open
  if (incident.status === 'open') {
    const { error: incidentUpdateError } = await ((supabase as any)
      .from('jarvis_incidents')
      .update({
        status: 'in_progress' as IncidentStatus,
        updated_at: nowIso()
      })
      .eq('id', incident.id));

    if (incidentUpdateError) {
      console.error(
        '[Incidents] runNextIncidentStep incident status update error:',
        incidentUpdateError
      );
    }
  }

  return {
    step: (updatedStepData as IncidentStepRow | null) ?? pending,
    incident
  };
}

