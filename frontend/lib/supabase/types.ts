export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      jarvis_agents: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_agent_runs: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_plans: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_plan_steps: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_signals: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_briefings: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_briefing_preferences: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_memory_chunks: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_journal_entries: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_timeline_events: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_system_events: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_clinical_events: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_patient_state: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_patient_pipeline: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_patient_journey_events: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_chart_prep_packets: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_action_policies: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_action_logs: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_action_approvals: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_agent_permissions: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_audit_log: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
        };
      };
      jarvis_kill_switches: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_universe_nodes: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_universe_edges: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_universe_snapshots: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_universe_embeddings: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_universe_event_map: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_umg_traversal_cache: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_umg_statistics: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      jarvis_umg_queries: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      nexus_financial_entities: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      nexus_financial_transactions: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      nexus_financial_snapshots: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      nexus_tax_positions: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      nexus_analytics_signals: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      nexus_recommendations: {
        Row: {
          id: string;
          user_id: string;
          workspace_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          workspace_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
  };
}

export type JarvisTable =
  | "jarvis_agents"
  | "jarvis_agent_runs"
  | "jarvis_plans"
  | "jarvis_plan_steps"
  | "jarvis_signals"
  | "jarvis_briefings"
  | "jarvis_briefing_preferences"
  | "jarvis_memory_chunks"
  | "jarvis_journal_entries"
  | "jarvis_timeline_events"
  | "jarvis_system_events"
  | "jarvis_clinical_events"
  | "jarvis_patient_state"
  | "jarvis_patient_pipeline"
  | "jarvis_patient_journey_events"
  | "jarvis_chart_prep_packets"
  | "jarvis_action_policies"
  | "jarvis_action_logs"
  | "jarvis_action_approvals"
  | "jarvis_agent_permissions"
  | "jarvis_audit_log"
  | "jarvis_kill_switches"
  | "jarvis_universe_nodes"
  | "jarvis_universe_edges"
  | "jarvis_universe_snapshots"
  | "jarvis_universe_embeddings"
  | "jarvis_universe_event_map"
  | "jarvis_umg_traversal_cache"
  | "jarvis_umg_statistics"
  | "jarvis_umg_queries";

export type NexusTable =
  | "nexus_financial_entities"
  | "nexus_financial_transactions"
  | "nexus_financial_snapshots"
  | "nexus_tax_positions"
  | "nexus_analytics_signals"
  | "nexus_recommendations";
