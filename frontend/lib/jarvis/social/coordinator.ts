import { supabaseServer } from "@/lib/supabase/server";
import type { ExecutiveCoordinator, CoordinatorType } from "./types";

export async function getCoordinator(
  userId: string,
  coordinatorType: CoordinatorType
): Promise<ExecutiveCoordinator | null> {
  const { data } = await supabaseServer
    .from("jarvis_executive_coordinators")
    .select("*")
    .eq("user_id", userId)
    .eq("coordinator_type", coordinatorType)
    .eq("is_active", true)
    .single();

  if (data) {
    return data as ExecutiveCoordinator;
  }

  // Return default coordinator if none exists
  return getDefaultCoordinator(userId, coordinatorType);
}

function getDefaultCoordinator(
  userId: string,
  coordinatorType: CoordinatorType
): ExecutiveCoordinator {
  const defaults: Record<CoordinatorType, Partial<ExecutiveCoordinator>> = {
    nexus: {
      name: "Nexus CFO/COO",
      description: "Financial and operational intelligence coordinator",
      managed_domains: ["financial", "operational"],
      managed_agents: ["financial_agent", "categorization_agent"],
    },
    clinic_director: {
      name: "Clinic Director AI",
      description: "Clinical pipeline and patient journey coordinator",
      managed_domains: ["clinical"],
      managed_agents: [
        "hospitalization_agent",
        "glp_monitor_agent",
        "chartprep_agent",
        "refill_agent",
        "triage_agent",
        "intake_agent",
        "discharge_agent",
        "carecontinuity_agent",
      ],
    },
    ops_director: {
      name: "Ops Director AI",
      description: "Scheduling, MA tasks, and admin workflow coordinator",
      managed_domains: ["ops", "scheduling"],
      managed_agents: ["scheduler_agent", "file_agent", "inbox_agent"],
    },
  };

  const defaultCoord = defaults[coordinatorType] || {
    name: "Executive Coordinator",
    description: "Multi-domain coordinator",
    managed_domains: [],
    managed_agents: [],
  };

  return {
    user_id: userId,
    coordinator_type: coordinatorType,
    ...defaultCoord,
  } as ExecutiveCoordinator;
}

export async function assignTaskToAgent(
  userId: string,
  task: {
    domain: string;
    actionType: string;
    priority: number;
    context: Record<string, any>;
  }
): Promise<string | null> {
  // Determine which coordinator manages this domain
  let coordinatorType: CoordinatorType | null = null;

  if (task.domain === "financial" || task.domain === "operational") {
    coordinatorType = "nexus";
  } else if (task.domain === "clinical") {
    coordinatorType = "clinic_director";
  } else if (task.domain === "ops" || task.domain === "scheduling") {
    coordinatorType = "ops_director";
  }

  if (!coordinatorType) {
    return null; // No coordinator for this domain
  }

  const coordinator = await getCoordinator(userId, coordinatorType);

  // Find the best agent from the coordinator's managed agents
  // This is simplified - in production, this would use load balancing, capability matching, etc.
  if (coordinator.managed_agents && coordinator.managed_agents.length > 0) {
    // For now, return the first matching agent
    // In production, this would use more sophisticated routing
    return coordinator.managed_agents[0];
  }

  return null;
}

export async function getCoordinatorLoad(
  userId: string,
  coordinatorType: CoordinatorType
): Promise<{
  total_tasks: number;
  pending_tasks: number;
  active_agents: number;
  avg_completion_time: number;
}> {
  const coordinator = await getCoordinator(userId, coordinatorType);

  if (!coordinator || !coordinator.managed_agents) {
    return {
      total_tasks: 0,
      pending_tasks: 0,
      active_agents: 0,
      avg_completion_time: 0,
    };
  }

  // Get task counts for managed agents
  const { data: tasks } = await supabaseServer
    .from("jarvis_agent_runs")
    .select("status, agent_slug")
    .in("agent_slug", coordinator.managed_agents);

  const totalTasks = (tasks || []).length;
  const pendingTasks = (tasks || []).filter((t) => t.status === "PENDING" || t.status === "RUNNING").length;
  const activeAgents = new Set((tasks || []).map((t) => t.agent_slug)).size;

  return {
    total_tasks: totalTasks,
    pending_tasks: pendingTasks,
    active_agents: activeAgents,
    avg_completion_time: 0, // Would calculate from historical data
  };
}

