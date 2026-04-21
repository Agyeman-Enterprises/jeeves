import { supabaseServer } from "@/lib/supabase/server";
import type { EventRoute, EventCategory, EventMeshEvent } from "./types";
import { classifyEvent } from "./classifier";
import { processAction } from "../actions/broker";
import type { ActionRequest } from "../actions/types";
import { generateSituationRoom } from "../situation/coordinator";
import { runSimulation } from "../simulation/engine";
import type { SimulationType } from "../simulation/types";

export async function ingestEvent(
  userId: string,
  eventType: string,
  source: string,
  payload: Record<string, any>,
  sourceId?: string
): Promise<string> {
  // Classify event
  const classification = await classifyEvent(eventType, payload, source);

  // Create event in mesh
  const { data: eventData, error: eventError } = await supabaseServer
    .from("jarvis_event_mesh_events")
    .insert({
      user_id: userId,
      event_type: eventType,
      event_category: classification.category,
      source,
      source_id: sourceId,
      payload,
      classification: classification.classification,
      status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (eventError || !eventData) {
    throw new Error(`Failed to ingest event: ${eventError?.message}`);
  }

  const eventId = (eventData as any).id;

  // Route event
  await routeEvent(userId, eventId, eventType, classification.category, payload);

  return eventId;
}

async function routeEvent(
  userId: string,
  eventId: string,
  eventType: string,
  category: EventCategory,
  payload: Record<string, any>
): Promise<void> {
  // Get routing rule
  const route = await getEventRoute(userId, eventType);

  if (!route) {
    // Use default routing based on category
    const defaultRoute = getDefaultRoute(category, eventType);
    await applyRoute(userId, eventId, defaultRoute, payload);
    return;
  }

  // Apply route
  await applyRoute(userId, eventId, route, payload);
}

async function getEventRoute(userId: string, eventType: string): Promise<EventRoute | null> {
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

function getDefaultRoute(category: EventCategory, eventType: string): Partial<EventRoute> {
  const defaults: Record<EventCategory, Partial<EventRoute>> = {
    CLINICAL: {
      target_agents: ["triage_agent", "chartprep_agent"],
      target_situation_rooms: ["CLINIC"],
      triggers_simulation: eventType.includes("PATIENT") || eventType.includes("LAB"),
      simulation_type: "CLINICAL",
      requires_notification: eventType.includes("CRITICAL") || eventType.includes("URGENT"),
      notification_priority: "HIGH",
    },
    FINANCIAL: {
      target_agents: ["financial_agent", "categorization_agent"],
      target_situation_rooms: ["FINANCIAL"],
      triggers_simulation: eventType.includes("TRANSACTION") || eventType.includes("REVENUE"),
      simulation_type: "FINANCIAL",
      requires_notification: false,
    },
    OPERATIONAL: {
      target_agents: ["scheduler_agent", "intake_agent"],
      target_situation_rooms: ["BUSINESS_OPS"],
      triggers_simulation: eventType.includes("WORKLOAD") || eventType.includes("BOTTLENECK"),
      simulation_type: "OPERATIONAL",
      requires_notification: false,
    },
    BUSINESS_PROJECT: {
      target_agents: [],
      target_situation_rooms: ["BUSINESS_OPS"],
      triggers_simulation: false,
      requires_notification: false,
    },
    PERSONAL_STATE: {
      target_agents: [],
      target_situation_rooms: ["LIFE"],
      triggers_simulation: false,
      requires_notification: false,
    },
    SYSTEM: {
      target_agents: [],
      target_situation_rooms: ["BUSINESS_OPS"],
      triggers_simulation: false,
      requires_notification: eventType.includes("FAILURE") || eventType.includes("CRITICAL"),
      notification_priority: "HIGH",
    },
  };

  return defaults[category] || {};
}

async function applyRoute(
  userId: string,
  eventId: string,
  route: Partial<EventRoute>,
  payload: Record<string, any>
): Promise<void> {
  const deliveries: any[] = [];

  // Route to agents
  if (route.target_agents && route.target_agents.length > 0) {
    for (const agentSlug of route.target_agents) {
      // Create delivery record
      const { data: delivery } = await supabaseServer
        .from("jarvis_event_deliveries")
        .insert({
          user_id: userId,
          event_id: eventId,
          subscriber_type: "AGENT",
          subscriber_id: agentSlug,
          delivery_status: "PENDING",
        } as any)
        .select("id")
        .single();

      if (delivery) {
        deliveries.push({ id: (delivery as any).id, type: "AGENT", subscriber: agentSlug });
      }

      // Trigger agent action (if auto-route is enabled)
      if (route.auto_route !== false) {
        try {
          await triggerAgentAction(userId, agentSlug, payload);
          // Mark delivery as delivered
          if (delivery) {
            await (supabaseServer as any)
              .from("jarvis_event_deliveries")
              .update({ delivery_status: "DELIVERED", delivered_at: new Date().toISOString() } as any)
              .eq("id", (delivery as any).id);
          }
        } catch (error: any) {
          // Mark delivery as failed
          if (delivery) {
            await (supabaseServer as any)
              .from("jarvis_event_deliveries")
              .update({ delivery_status: "FAILED", error: error.message } as any)
              .eq("id", (delivery as any).id);
          }
        }
      }
    }
  }

  // Route to situation rooms
  if (route.target_situation_rooms && route.target_situation_rooms.length > 0) {
    for (const roomType of route.target_situation_rooms) {
      // Create delivery record
      const { data: delivery } = await supabaseServer
        .from("jarvis_event_deliveries")
        .insert({
          user_id: userId,
          event_id: eventId,
          subscriber_type: "SITUATION_ROOM",
          subscriber_id: roomType,
          delivery_status: "PENDING",
        } as any)
        .select("id")
        .single();

      if (delivery) {
        deliveries.push({ id: (delivery as any).id, type: "SITUATION_ROOM", subscriber: roomType });
      }

      // Trigger situation room update (async, non-blocking)
      generateSituationRoom(userId, roomType as any).catch((error) => {
        console.error(`Failed to update situation room ${roomType}:`, error);
      });

      // Mark delivery as delivered
      if (delivery) {
        await (supabaseServer as any)
          .from("jarvis_event_deliveries")
          .update({ delivery_status: "DELIVERED", delivered_at: new Date().toISOString() } as any)
          .eq("id", (delivery as any).id);
      }
    }
  }

  // Trigger simulation if needed
  if (route.triggers_simulation && route.simulation_type) {
    runSimulation(
      userId,
      route.simulation_type as SimulationType,
      `Event-triggered: ${eventId}`,
      payload,
      `Simulation triggered by event: ${eventId}`
    ).catch((error) => {
      console.error(`Failed to trigger simulation:`, error);
    });
  }

  // Update event with routing decision
  await (supabaseServer as any)
    .from("jarvis_event_mesh_events")
    .update({
      status: "ROUTED",
      routing_decision: {
        target_agents: route.target_agents,
        target_situation_rooms: route.target_situation_rooms,
        triggers_simulation: route.triggers_simulation,
        deliveries,
      },
    } as any)
    .eq("id", eventId);
}

async function triggerAgentAction(
  userId: string,
  agentSlug: string,
  payload: Record<string, any>
): Promise<void> {
  // Determine action type based on agent and payload
  // This is simplified - in production, this would use agent-specific logic
  const actionType = determineActionType(agentSlug, payload);
  const domain = determineDomain(agentSlug);

  if (!actionType || !domain) {
    return; // No action needed
  }

  const actionRequest: ActionRequest = {
    action_type: actionType as any,
    domain: domain as any,
    input: payload,
    urgency: "NORMAL",
  };

  // Process action through broker
  await processAction(userId, actionRequest, agentSlug);
}

function determineActionType(agentSlug: string, payload: Record<string, any>): string | null {
  // Map agent to action type
  const agentActionMap: Record<string, string> = {
    triage_agent: "clinical.task.create",
    chartprep_agent: "clinical.task.create",
    scheduler_agent: "clinical.appointment.schedule",
    glp_monitor_agent: "clinical.task.create",
    financial_agent: "financial.transaction.categorize",
    categorization_agent: "financial.transaction.categorize",
  };

  return agentActionMap[agentSlug] || null;
}

function determineDomain(agentSlug: string): string | null {
  if (agentSlug.includes("clinical") || agentSlug.includes("triage") || agentSlug.includes("chart") || agentSlug.includes("glp")) {
    return "clinical";
  }
  if (agentSlug.includes("financial") || agentSlug.includes("tax") || agentSlug.includes("categorization")) {
    return "financial";
  }
  if (agentSlug.includes("scheduler") || agentSlug.includes("intake") || agentSlug.includes("ops")) {
    return "operations";
  }
  return null;
}

