import { supabaseServer } from "@/lib/supabase/server";
import type { EventRoute, EventCategory } from "./types";

export async function createEventRoute(route: Partial<EventRoute>): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_event_routes")
    .upsert({
      user_id: route.user_id,
      event_type: route.event_type,
      event_category: route.event_category!,
      target_agents: route.target_agents,
      target_situation_rooms: route.target_situation_rooms,
      triggers_simulation: route.triggers_simulation,
      simulation_type: route.simulation_type,
      requires_notification: route.requires_notification,
      notification_priority: route.notification_priority,
      auto_route: route.auto_route,
      conditions: route.conditions,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "user_id,event_type",
    })
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create event route: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getEventRoute(userId: string, eventType: string): Promise<EventRoute | null> {
  const { data } = await supabaseServer
    .from("jarvis_event_routes")
    .select("*")
    .eq("user_id", userId)
    .eq("event_type", eventType)
    .single();

  if (data) {
    return data as EventRoute;
  }

  return null;
}

export async function getAllEventRoutes(userId: string): Promise<EventRoute[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_event_routes")
    .select("*")
    .eq("user_id", userId)
    .order("event_type", { ascending: true });

  if (error) {
    throw new Error(`Failed to get event routes: ${error.message}`);
  }

  return (data || []) as EventRoute[];
}

export async function initializeDefaultRoutes(userId: string): Promise<void> {
  // Clinical event routes
  const clinicalEvents = [
    "PATIENT_MESSAGE",
    "LAB_RESULT_RECEIVED",
    "CRITICAL_LAB_RESULT",
    "PATIENT_HOSPITALIZED",
    "DISCHARGE_SUMMARY_RECEIVED",
    "MED_REFILL_REQUESTED",
    "NO_SHOW",
    "APPOINTMENT_BOOKED",
    "APPOINTMENT_RESCHEDULED",
  ];

  for (const eventType of clinicalEvents) {
    await createEventRoute({
      user_id: userId,
      event_type: eventType,
      event_category: "CLINICAL",
      target_agents: ["triage_agent", "chartprep_agent"],
      target_situation_rooms: ["CLINIC"],
      triggers_simulation: eventType.includes("PATIENT") || eventType.includes("LAB"),
      simulation_type: "CLINICAL",
      requires_notification: eventType.includes("CRITICAL") || eventType.includes("HOSPITALIZED"),
      notification_priority: eventType.includes("CRITICAL") ? "CRITICAL" : "HIGH",
      auto_route: true,
    });
  }

  // Financial event routes
  const financialEvents = [
    "TRANSACTION_POSTED",
    "INVOICE_CREATED",
    "SUBSCRIPTION_CHARGED",
    "EXPENSE_CATEGORIZED",
    "ANOMALY_DETECTED",
    "TAX_CHANGE",
  ];

  for (const eventType of financialEvents) {
    await createEventRoute({
      user_id: userId,
      event_type: eventType,
      event_category: "FINANCIAL",
      target_agents: ["financial_agent", "categorization_agent"],
      target_situation_rooms: ["FINANCIAL"],
      triggers_simulation: eventType.includes("TRANSACTION") || eventType.includes("REVENUE"),
      simulation_type: "FINANCIAL",
      requires_notification: false,
      auto_route: true,
    });
  }

  // Operational event routes
  const operationalEvents = [
    "APPOINTMENT_BOOKED",
    "APPOINTMENT_CANCELLED",
    "MA_WORKLOAD_SPIKE",
    "AUTOMATION_FAILURE",
    "CHART_BACKLOG",
  ];

  for (const eventType of operationalEvents) {
    await createEventRoute({
      user_id: userId,
      event_type: eventType,
      event_category: "OPERATIONAL",
      target_agents: ["scheduler_agent", "intake_agent"],
      target_situation_rooms: ["BUSINESS_OPS"],
      triggers_simulation: eventType.includes("WORKLOAD") || eventType.includes("BOTTLENECK"),
      simulation_type: "OPERATIONAL",
      requires_notification: false,
      auto_route: true,
    });
  }

  // System event routes
  const systemEvents = [
    "AGENT_FAILURE",
    "AGENT_RECOVERY",
    "RETRY_STORM",
    "HIGH_LOAD",
    "KILL_SWITCH_ENGAGED",
  ];

  for (const eventType of systemEvents) {
    await createEventRoute({
      user_id: userId,
      event_type: eventType,
      event_category: "SYSTEM",
      target_agents: [],
      target_situation_rooms: ["BUSINESS_OPS"],
      triggers_simulation: false,
      requires_notification: eventType.includes("FAILURE") || eventType.includes("CRITICAL"),
      notification_priority: "HIGH",
      auto_route: true,
    });
  }
}

