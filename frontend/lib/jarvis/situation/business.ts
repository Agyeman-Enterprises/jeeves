import { supabaseServer } from "@/lib/supabase/server";
import type { SituationRoomSnapshot, SituationRoomAlert, SituationRoomRecommendation } from "./types";
import { simulateAgentLoad } from "../simulation/agent";
import { getQueueStatus } from "../social/queue";

export async function generateBusinessOpsSituationRoom(
  userId: string
): Promise<SituationRoomSnapshot> {
  // A. Agent Workforce Telemetry
  const { data: agentRuns } = await supabaseServer
    .from("jarvis_agent_runs")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(100);

  const pendingTasks = (agentRuns || []).filter((r) => r.status === "PENDING" || r.status === "RUNNING").length;
  const failedTasks = (agentRuns || []).filter((r) => r.status === "FAILED").length;

  // Get queue status for each agent
  const { data: agents } = await supabaseServer
    .from("jarvis_agents")
    .select("slug")
    .eq("is_active", true);

  const agentStatus: Record<string, any> = {};
  for (const agent of agents || []) {
    try {
      const queueStatus = await getQueueStatus(agent.slug);
      agentStatus[agent.slug] = queueStatus;
    } catch (error) {
      // Agent may not have queue
      agentStatus[agent.slug] = { queued: 0, processing: 0, completed: 0, failed: 0 };
    }
  }

  // B. Workflow Monitoring
  const { data: plans } = await supabaseServer
    .from("jarvis_plans")
    .select("*")
    .eq("user_id", userId)
    .in("status", ["PENDING", "RUNNING"])
    .order("created_at", { ascending: false })
    .limit(50);

  // C. Operational Risk Panel
  const { data: operationalPredictions } = await supabaseServer
    .from("jarvis_operational_predictions")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(10);

  // D. Automation Heatmap
  const automationHeatmap = {
    fully_automated: ["file_organization", "transaction_categorization"],
    partly_automated: ["patient_scheduling", "email_triage"],
    manual_bottlenecks: ["clinical_notes", "medication_orders"],
  };

  // Generate alerts
  const alerts: SituationRoomAlert[] = [];

  if (failedTasks > 10) {
    alerts.push({
      user_id: userId,
      room_type: "BUSINESS_OPS",
      alert_type: "RISK",
      severity: "MEDIUM",
      title: "High Agent Failure Rate",
      description: `${failedTasks} agent tasks have failed recently`,
      recommended_actions: {
        actions: ["Review failed tasks", "Check agent health", "Investigate root causes"],
      },
    });
  }

  // Generate recommendations
  const recommendations: SituationRoomRecommendation[] = [];

  // Check for overloaded agents
  for (const [agentSlug, status] of Object.entries(agentStatus)) {
    const statusObj = status as { queued: number; processing: number };
    if (statusObj.queued > 20 || statusObj.processing > 10) {
      recommendations.push({
        user_id: userId,
        room_type: "BUSINESS_OPS",
        recommendation_type: "OPTIMIZATION",
        title: `Agent Overload: ${agentSlug}`,
        description: `${agentSlug} has ${statusObj.queued} queued tasks. Consider redistributing to other agents.`,
        priority: 2,
      });
    }
  }

  // Create snapshot
  const snapshot: SituationRoomSnapshot = {
    user_id: userId,
    room_type: "BUSINESS_OPS",
    snapshot_data: {
      agent_workforce: {
        total_tasks_pending: pendingTasks,
        total_tasks_failed: failedTasks,
        agent_status: agentStatus,
        bottlenecks: Object.entries(agentStatus).filter(([_, s]) => (s as any).queued > 10).map(([slug]) => slug),
        idle_agents: Object.entries(agentStatus).filter(([_, s]) => (s as any).queued === 0 && (s as any).processing === 0).map(([slug]) => slug),
      },
      workflow_monitoring: {
        active_plans: (plans || []).length,
        delayed_processes: (plans || []).filter((p) => {
          const created = new Date(p.created_at);
          const hoursSince = (Date.now() - created.getTime()) / (1000 * 60 * 60);
          return hoursSince > 24;
        }).length,
        sla_violations: 0,
      },
      operational_risk: {
        appointment_mismatch: (operationalPredictions || []).find((p) => p.prediction_type === "SCHEDULING_BOTTLENECK")?.risk_level || "LOW",
        staff_burnout_risk: (operationalPredictions || []).find((p) => p.prediction_type === "MA_WORKLOAD")?.risk_level || "LOW",
        project_overload: 0,
      },
      automation_heatmap: automationHeatmap,
    },
    alerts: alerts.map((a) => ({
      id: a.id,
      type: a.alert_type,
      severity: a.severity,
      title: a.title,
      description: a.description,
    })),
    recommendations: recommendations.map((r) => ({
      id: r.id,
      type: r.recommendation_type,
      title: r.title,
      description: r.description,
      priority: r.priority,
    })),
    agent_status: agentStatus,
  };

  return snapshot;
}

