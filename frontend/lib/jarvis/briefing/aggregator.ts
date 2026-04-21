import { supabaseServer } from "@/lib/supabase/server";
import type { SystemEvent } from "../events/types";

export interface AggregatedEvents {
  clinical: SystemEvent[];
  financial: SystemEvent[];
  operational: SystemEvent[];
  system: SystemEvent[];
  personal: SystemEvent[];
}

export async function aggregateEvents(
  userId: string,
  startDate: Date,
  endDate: Date
): Promise<AggregatedEvents> {
  const start = startDate.toISOString();
  const end = endDate.toISOString();

  // Get all system events in the period
  const { data: events } = await supabaseServer
    .from("jarvis_system_events")
    .select("*")
    .eq("user_id", userId)
    .gte("created_at", start)
    .lte("created_at", end)
    .order("created_at", { ascending: false });

  if (!events) {
    return {
      clinical: [],
      financial: [],
      operational: [],
      system: [],
      personal: [],
    };
  }

  // Categorize events
  const clinical: SystemEvent[] = [];
  const financial: SystemEvent[] = [];
  const operational: SystemEvent[] = [];
  const system: SystemEvent[] = [];
  const personal: SystemEvent[] = [];

  for (const event of events) {
    const evt = event as any;
    
    // Clinical events
    if (
      evt.type?.includes("PATIENT") ||
      evt.type?.includes("MED") ||
      evt.type?.includes("LAB") ||
      evt.type?.includes("APPOINTMENT") ||
      evt.type?.includes("DISCHARGE") ||
      evt.type?.includes("HOSPITAL") ||
      evt.type?.includes("INTAKE") ||
      evt.type?.includes("LEAD") ||
      evt.source === "solopractice" ||
      evt.source === "bookadoc" ||
      evt.source === "medrx" ||
      evt.source === "myhealthally"
    ) {
      clinical.push(evt);
    }
    // Financial events
    else if (
      evt.type?.includes("TXN") ||
      evt.type?.includes("INCOME") ||
      evt.type?.includes("EXPENSE") ||
      evt.type?.includes("TAX") ||
      evt.type?.includes("CASH") ||
      evt.type?.includes("PROFITABILITY") ||
      evt.source === "taxrx" ||
      evt.source === "entitytaxpro" ||
      evt.source === "nexus"
    ) {
      financial.push(evt);
    }
    // System events
    else if (
      evt.type?.includes("AGENT") ||
      evt.source === "system"
    ) {
      system.push(evt);
    }
    // Operational events
    else if (
      evt.type?.includes("TASK") ||
      evt.type?.includes("SCHEDULE") ||
      evt.source === "shopify"
    ) {
      operational.push(evt);
    }
    // Personal events
    else {
      personal.push(evt);
    }
  }

  return {
    clinical,
    financial,
    operational,
    system,
    personal,
  };
}

