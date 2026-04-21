export type IncidentStatus = 'open' | 'in_progress' | 'resolved' | 'cancelled';

export type IncidentStepStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped';

export type IncidentStepType =
  | 'notify'
  | 'agentAction'
  | 'runAgentRule'
  | 'wait'
  | 'manualCheck';

export type PlaybookStepConfig = {
  index: number;
  type: IncidentStepType;
  config: any;
};

