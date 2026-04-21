import { supabaseServer } from "@/lib/supabase/server";
import type { StrategicPriorityMap } from "./types";
import { getNodesByDomain } from "../cuil/graph";

export async function generateStrategicPriorityMap(
  userId: string,
  weekStartDate?: string
): Promise<StrategicPriorityMap> {
  const weekStart = weekStartDate ? new Date(weekStartDate) : getWeekStart(new Date());
  const weekStartStr = weekStart.toISOString().split("T")[0];

  // Get active projects/businesses from universe graph
  const businessUnits = await getNodesByDomain(userId, "OPERATIONS", "BUSINESS_UNIT");
  const projects = await getNodesByDomain(userId, "OPERATIONS", "PROJECT");

  // Categorize priorities
  const mustHappen: any[] = [];
  const shouldHappen: any[] = [];
  const canHappen: any[] = [];
  const mustNotHappen: any[] = [];

  const businessUnitPriorities: Record<string, any> = {};

  // Evaluate each business unit
  for (const unit of businessUnits) {
    const priorities = await evaluateBusinessUnitPriorities(userId, unit);
    businessUnitPriorities[unit.label || unit.id || ""] = priorities;

    // Categorize based on importance and urgency
    if (priorities.critical) {
      mustHappen.push(...priorities.critical);
    }
    if (priorities.important) {
      shouldHappen.push(...priorities.important);
    }
    if (priorities.optional) {
      canHappen.push(...priorities.optional);
    }
    if (priorities.blocked) {
      mustNotHappen.push(...priorities.blocked);
    }
  }

  // Generate resource allocation summary
  const resourceAllocationSummary = {
    cognitive: {
      allocated_hours: 0,
      available_hours: 40, // Simplified
    },
    temporal: {
      allocated_hours: 0,
      available_hours: 50, // Simplified
    },
    operational: {
      allocated_tasks: 0,
      available_capacity: 100, // Simplified
    },
    financial: {
      allocated_amount: 0,
      available_amount: 0, // Would come from Nexus
    },
  };

  const priorityMap: StrategicPriorityMap = {
    user_id: userId,
    week_start_date: weekStartStr,
    priority_map: {
      must_happen: mustHappen,
      should_happen: shouldHappen,
      can_happen: canHappen,
      must_not_happen: mustNotHappen,
    },
    must_happen: { items: mustHappen },
    should_happen: { items: shouldHappen },
    can_happen: { items: canHappen },
    must_not_happen: { items: mustNotHappen },
    business_unit_priorities: businessUnitPriorities,
    resource_allocation_summary: resourceAllocationSummary,
  };

  // Store priority map
  await storeStrategicPriorityMap(userId, priorityMap);

  return priorityMap;
}

async function evaluateBusinessUnitPriorities(
  userId: string,
  businessUnit: any
): Promise<{
  critical: any[];
  important: any[];
  optional: any[];
  blocked: any[];
}> {
  // Simplified - in production, this would evaluate based on:
  // - Deadlines
  // - Dependencies
  // - Resource availability
  // - Business impact
  // - Risk factors

  return {
    critical: [],
    important: [],
    optional: [],
    blocked: [],
  };
}

function getWeekStart(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
  return new Date(d.setDate(diff));
}

async function storeStrategicPriorityMap(userId: string, map: StrategicPriorityMap): Promise<void> {
  await supabaseServer
    .from("jarvis_strategic_priority_maps")
    .upsert({
      ...map,
    } as any, {
      onConflict: "user_id,week_start_date",
    });
}

export async function getStrategicPriorityMap(
  userId: string,
  weekStartDate?: string
): Promise<StrategicPriorityMap | null> {
  const weekStart = weekStartDate ? new Date(weekStartDate) : getWeekStart(new Date());
  const weekStartStr = weekStart.toISOString().split("T")[0];

  const { data } = await supabaseServer
    .from("jarvis_strategic_priority_maps")
    .select("*")
    .eq("user_id", userId)
    .eq("week_start_date", weekStartStr)
    .single();

  if (data) {
    return data as StrategicPriorityMap;
  }

  return null;
}

