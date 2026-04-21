export type EventCategory = "CLINICAL" | "OPERATIONAL" | "FINANCIAL" | "BUSINESS_PROJECT" | "PERSONAL_STATE" | "SYSTEM";
export type SubscriberType = "AGENT" | "SITUATION_ROOM" | "SIMULATION" | "NOTIFICATION";
export type DeliveryStatus = "PENDING" | "DELIVERED" | "FAILED" | "ACKNOWLEDGED";

export interface EventRoute {
  id?: string;
  user_id: string;
  event_type: string;
  event_category: EventCategory;
  target_agents?: string[];
  target_situation_rooms?: string[];
  triggers_simulation?: boolean;
  simulation_type?: string;
  requires_notification?: boolean;
  notification_priority?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  auto_route?: boolean;
  conditions?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface EventMeshEvent {
  id?: string;
  user_id: string;
  event_type: string;
  event_category: EventCategory;
  source: string; // "myhealthally" | "solopractice" | "bookadoc" | "nexus" | "agent" | "system" | "user"
  source_id?: string;
  payload: Record<string, any>;
  classification?: Record<string, any>;
  routing_decision?: Record<string, any>;
  status?: "PENDING" | "ROUTED" | "PROCESSED" | "FAILED";
  processed_at?: string;
  created_at?: string;
}

export interface EventSubscription {
  id?: string;
  user_id: string;
  subscriber_type: SubscriberType;
  subscriber_id: string;
  event_types?: string[];
  event_categories?: EventCategory[];
  filters?: Record<string, any>;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface EventDelivery {
  id?: string;
  user_id: string;
  event_id: string;
  subscriber_type: SubscriberType;
  subscriber_id: string;
  delivery_status?: DeliveryStatus;
  delivered_at?: string;
  acknowledged_at?: string;
  error?: string;
  created_at?: string;
}

export interface EventPattern {
  id?: string;
  user_id: string;
  pattern_name: string;
  pattern_description?: string;
  event_sequence: Record<string, any>;
  trigger_simulation?: boolean;
  simulation_type?: string;
  trigger_alert?: boolean;
  alert_severity?: string;
  detected_count?: number;
  last_detected_at?: string;
  created_at?: string;
  updated_at?: string;
}

