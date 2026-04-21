export type SignalType = "CLINICAL" | "FINANCIAL" | "OPERATIONAL" | "SYSTEM" | "PERSONAL";
export type SignalSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type BriefingType = "DAILY" | "WEEKLY" | "MONTHLY" | "ALERT";

export interface Signal {
  id?: string;
  user_id: string;
  type: SignalType;
  severity: SignalSeverity;
  domain?: string;
  title: string;
  description?: string;
  payload?: Record<string, any>;
  priority_score?: number;
  created_at?: string;
}

export interface PrioritizedItem extends Signal {
  urgency: number; // 0-100
  impact: number; // 0-100
  risk: number; // 0-100
  reversibility: number; // 0-100 (higher = more reversible)
  deadline_proximity?: number; // days until deadline
}

export interface BriefingContent {
  clinical?: {
    overview: string;
    priorities: PrioritizedItem[];
    stats: {
      new_messages: number;
      refills_pending: number;
      glp_overdue: number;
      hospitalizations: number;
      lab_results: number;
    };
  };
  business?: {
    overview: string;
    priorities: PrioritizedItem[];
    stats: {
      appointments_today: number;
      no_shows_projected: number;
      open_tasks: number;
    };
  };
  financial?: {
    overview: string;
    priorities: PrioritizedItem[];
    stats: {
      total_cash: number;
      burn_rate: number;
      tax_estimate: number;
      missing_receipts: number;
    };
  };
  system?: {
    overview: string;
    priorities: PrioritizedItem[];
    stats: {
      active_agents: number;
      degraded_agents: number;
      retried_tasks: number;
      stuck_runs: number;
    };
  };
  personal?: {
    schedule: any[];
    email_summaries: string[];
  };
  strategic?: {
    projects: any[];
    recommendations: string[];
  };
}

export interface Briefing {
  id?: string;
  user_id: string;
  type: BriefingType;
  period_start: string;
  period_end: string;
  content: BriefingContent;
  summary_text?: string;
  signals_included?: string[];
  created_at?: string;
}

