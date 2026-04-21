// src/lib/nexus/situations/types.ts

export type SituationWidgetKind =
  | 'event_feed'
  | 'error_list'
  | 'metric_card';

export interface SituationRoom {
  id: string;
  workspace_id: string;
  user_id: string;
  slug: string;
  name: string;
  description?: string;
  is_default: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SituationWidget {
  id: string;
  room_id: string;
  workspace_id: string;
  user_id: string;
  kind: SituationWidgetKind;
  title: string;
  position: {
    x?: number;
    y?: number;
    w?: number;
    h?: number;
    [k: string]: unknown;
  };
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

