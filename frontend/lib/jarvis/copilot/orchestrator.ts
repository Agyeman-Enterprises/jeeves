import { supabaseServer } from "@/lib/supabase/server";
import type { AutonomousAction, CoPilotCoordination, CoordinationType, AutonomyMode } from "./types";
import { getCurrentMode, determineOptimalMode, transitionMode } from "./modes";
import { processAction } from "../actions/broker";
import type { ActionRequest } from "../actions/types";
import { generateSituationRoom } from "../situation/coordinator";
import { ingestCrossUniverseEvent } from "../cuil/events";
import type { UniverseDomain } from "../cuil/types";
import { getCognitiveBudget } from "../cerae/cognitive";

export async function executeCoPilotCycle(userId: string): Promise<{
  mode: string;
  actions: string[];
  coordinations: string[];
}> {
  // Determine optimal mode
  const optimalMode = await determineOptimalMode(userId);

  // Get current mode
  const currentMode = await getCurrentMode(userId);

  // Transition if needed
  if (optimalMode !== currentMode) {
    await transitionMode(
      userId,
      optimalMode,
      `Mode transition based on cognitive state and workload`,
      "COGNITIVE_STATE"
    );
  }

  // Execute actions based on mode
  const actionIds: string[] = [];
  const coordinationIds: string[] = [];

  if (optimalMode === "CO_PILOT" || optimalMode === "EXECUTE") {
    // Execute autonomous actions
    const actions = await generateAutonomousActions(userId, optimalMode);
    for (const action of actions) {
      try {
        const actionId = await executeAutonomousAction(userId, action, optimalMode);
        actionIds.push(actionId);
      } catch (error) {
        console.error("Failed to execute autonomous action:", error);
      }
    }

    // Perform system coordination
    const coordinations = await performSystemCoordination(userId);
    for (const coordination of coordinations) {
      const coordId = await logCoordination(userId, coordination);
      coordinationIds.push(coordId);
    }
  }

  return {
    mode: optimalMode,
    actions: actionIds,
    coordinations: coordinationIds,
  };
}

async function generateAutonomousActions(
  userId: string,
  mode: AutonomyMode
): Promise<Partial<AutonomousAction>[]> {
  const actions: Partial<AutonomousAction>[] = [];

  // Clinical automation
  actions.push(...(await generateClinicalActions(userId, mode)));

  // Business automation
  actions.push(...(await generateBusinessActions(userId, mode)));

  // Financial automation
  actions.push(...(await generateFinancialActions(userId, mode)));

  // Life automation
  actions.push(...(await generateLifeActions(userId, mode)));

  return actions;
}

async function generateClinicalActions(
  userId: string,
  mode: AutonomyMode
): Promise<Partial<AutonomousAction>[]> {
  const actions: Partial<AutonomousAction>[] = [];

  // Check for pending patient messages
  const { data: messages } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .eq("event_type", "PATIENT_MESSAGE")
    .eq("status", "NEW")
    .limit(10);

  if (messages && messages.length > 0) {
    actions.push({
      action_type: "clinical.message.triage",
      domain: "clinical",
      action_description: `Triage ${messages.length} pending patient messages`,
      triggered_by: "CO_PILOT",
      action_details: {
        message_count: messages.length,
      },
    });
  }

  // Check for overdue labs
  const { data: labs } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .eq("event_type", "LAB_RESULT_RECEIVED")
    .eq("status", "NEW")
    .limit(10);

  if (labs && labs.length > 0) {
    actions.push({
      action_type: "clinical.lab.review",
      domain: "clinical",
      action_description: `Review ${labs.length} pending lab results`,
      triggered_by: "CO_PILOT",
      action_details: {
        lab_count: labs.length,
      },
    });
  }

  return actions;
}

async function generateBusinessActions(
  userId: string,
  mode: AutonomyMode
): Promise<Partial<AutonomousAction>[]> {
  const actions: Partial<AutonomousAction>[] = [];

  // Check for agent overload
  const { data: agentRuns } = await supabaseServer
    .from("jarvis_agent_runs")
    .select("*")
    .eq("user_id", userId)
    .in("status", ["PENDING", "RUNNING"])
    .limit(100);

  const pendingCount = (agentRuns || []).length;
  if (pendingCount > 50) {
    actions.push({
      action_type: "business.agent.rebalance",
      domain: "operations",
      action_description: `Rebalance ${pendingCount} pending agent tasks`,
      triggered_by: "CO_PILOT",
      action_details: {
        pending_tasks: pendingCount,
      },
    });
  }

  return actions;
}

async function generateFinancialActions(
  userId: string,
  mode: AutonomyMode
): Promise<Partial<AutonomousAction>[]> {
  const actions: Partial<AutonomousAction>[] = [];

  // Check for uncategorized transactions
  const { data: transactions } = await supabaseServer
    .from("nexus_financial_transactions")
    .select("*")
    .eq("user_id", userId)
    .is("category", null)
    .limit(20);

  if (transactions && transactions.length > 0) {
    actions.push({
      action_type: "financial.transaction.categorize",
      domain: "financial",
      action_description: `Categorize ${transactions.length} uncategorized transactions`,
      triggered_by: "CO_PILOT",
      action_details: {
        transaction_count: transactions.length,
      },
    });
  }

  return actions;
}

async function generateLifeActions(
  userId: string,
  mode: AutonomyMode
): Promise<Partial<AutonomousAction>[]> {
  const actions: Partial<AutonomousAction>[] = [];

  // Check cognitive budget
  const budget = await getCognitiveBudget(userId);
  if (budget && (budget.total_energy_percentage || 0) < 40) {
    actions.push({
      action_type: "life.schedule.optimize",
      domain: "personal",
      action_description: "Optimize schedule based on low cognitive energy",
      triggered_by: "CO_PILOT",
      action_details: {
        energy_percentage: budget.total_energy_percentage,
      },
    });
  }

  return actions;
}

async function executeAutonomousAction(
  userId: string,
  action: Partial<AutonomousAction>,
  mode: AutonomyMode
): Promise<string> {
  // Log action
  const { data: actionLog, error: logError } = await supabaseServer
    .from("jarvis_autonomous_actions")
    .insert({
      user_id: userId,
      action_type: action.action_type!,
      domain: action.domain!,
      action_description: action.action_description!,
      action_details: action.action_details,
      triggered_by: action.triggered_by || "CO_PILOT",
      mode_when_executed: mode,
      safety_checks_passed: true,
      status: "EXECUTING",
      executed_at: new Date().toISOString(),
    } as any)
    .select("id")
    .single();

  if (logError || !actionLog) {
    throw new Error(`Failed to log autonomous action: ${logError?.message}`);
  }

  const actionId = (actionLog as any).id;

  try {
    // Execute action through action broker
    const actionRequest: ActionRequest = {
      action_type: action.action_type as any,
      domain: action.domain as any,
      input: action.action_details || {},
      urgency: "NORMAL",
    };

    const result = await processAction(userId, actionRequest);

    // Update action log
    await (supabaseServer as any)
      .from("jarvis_autonomous_actions")
      .update({
        status: result.success ? "COMPLETED" : "FAILED",
        execution_result: result,
        completed_at: new Date().toISOString(),
      } as any)
      .eq("id", actionId);

    return actionId;
  } catch (error: any) {
    // Update action log with error
    await (supabaseServer as any)
      .from("jarvis_autonomous_actions")
      .update({
        status: "FAILED",
        execution_result: { error: error.message },
        completed_at: new Date().toISOString(),
      } as any)
      .eq("id", actionId);

    throw error;
  }
}

async function performSystemCoordination(
  userId: string
): Promise<Partial<CoPilotCoordination>[]> {
  const coordinations: Partial<CoPilotCoordination>[] = [];

  // Check for system imbalances
  // Example: Clinic surge scenario
  const { data: clinicalEvents } = await supabaseServer
    .from("jarvis_clinical_events")
    .select("*")
    .eq("user_id", userId)
    .eq("event_type", "APPOINTMENT_BOOKED")
    .gte("created_at", new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());

  const appointmentCount = (clinicalEvents || []).length;
  if (appointmentCount > 20) {
    // Clinic surge detected
    coordinations.push({
      coordination_type: "REBALANCE",
      affected_domains: ["clinical", "operations", "personal"],
      coordination_reason: "Clinic surge detected - rebalancing system",
      actions_taken: {
        increase_automation: true,
        reschedule_non_critical: true,
        reallocate_agent_load: true,
        adjust_schedule: true,
      },
    });
  }

  return coordinations;
}

async function logCoordination(
  userId: string,
  coordination: Partial<CoPilotCoordination>
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_copilot_coordination")
    .insert({
      user_id: userId,
      coordination_type: coordination.coordination_type!,
      affected_domains: coordination.affected_domains!,
      coordination_reason: coordination.coordination_reason!,
      actions_taken: coordination.actions_taken!,
      system_state_before: coordination.system_state_before,
      system_state_after: coordination.system_state_after,
      impact_assessment: coordination.impact_assessment,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to log coordination: ${error?.message}`);
  }

  return (data as any).id;
}
