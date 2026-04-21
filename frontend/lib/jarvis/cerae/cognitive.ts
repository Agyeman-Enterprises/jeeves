import { supabaseServer } from "@/lib/supabase/server";
import type { CognitiveBudget, EmotionalLoad, RiskTolerance } from "./types";
import { getCurrentMentalState } from "../emotional/state";
import { getLongitudinalIdentity } from "../longitudinal/identity";

export async function generateCognitiveBudget(
  userId: string,
  budgetDate?: string
): Promise<CognitiveBudget> {
  const date = budgetDate ? new Date(budgetDate) : new Date();
  const dateStr = date.toISOString().split("T")[0];

  // Get current mental state
  const mentalState = await getCurrentMentalState(userId);

  // Get longitudinal identity for energy patterns
  const energyIdentity = await getLongitudinalIdentity(userId, "energy");
  const fatigueIdentity = await getLongitudinalIdentity(userId, "fatigue_pattern");

  // Calculate total energy percentage
  const cognitiveBandwidth = mentalState?.cognitive_bandwidth || 100;
  const fatigueLevel = mentalState?.fatigue_level || 0;
  const totalEnergy = Math.max(0, Math.min(100, cognitiveBandwidth - fatigueLevel * 0.5));

  // Calculate deep work capacity (hours)
  // Based on energy and fatigue
  const deepWorkCapacity = totalEnergy > 70 ? 3.0 : totalEnergy > 50 ? 2.0 : totalEnergy > 30 ? 1.0 : 0.5;

  // Calculate decision capacity
  // Higher energy = more decisions, but fatigue reduces it
  const decisionCapacity = Math.floor((totalEnergy / 100) * 25); // Max ~25 decisions per day

  // Determine emotional load
  const emotionalLoad: EmotionalLoad =
    mentalState?.emotional_state === "stressed" || mentalState?.emotional_state === "overwhelmed"
      ? "HIGH"
      : mentalState?.emotional_state === "tired" || mentalState?.emotional_state === "frustrated"
      ? "MEDIUM"
      : "LOW";

  // Determine risk tolerance
  const riskTolerance: RiskTolerance =
    totalEnergy > 70 && emotionalLoad === "LOW" ? "HIGH" : totalEnergy > 50 ? "MODERATE" : "LOW";

  // Generate recommended tasks based on energy and state
  const recommendedTasks = generateRecommendedTasks(totalEnergy, emotionalLoad, mentalState);
  const tasksToAvoid = generateTasksToAvoid(totalEnergy, emotionalLoad, mentalState);

  // Generate optimal focus zones
  const optimalFocusZones = generateOptimalFocusZones(energyIdentity, fatigueIdentity);

  const budget: CognitiveBudget = {
    user_id: userId,
    budget_date: dateStr,
    total_energy_percentage: totalEnergy,
    deep_work_capacity_hours: deepWorkCapacity,
    decision_capacity_count: decisionCapacity,
    emotional_load: emotionalLoad,
    risk_tolerance: riskTolerance,
    cognitive_state: {
      cognitive_bandwidth: cognitiveBandwidth,
      fatigue_level: fatigueLevel,
      emotional_state: mentalState?.emotional_state,
      decision_load: mentalState?.decision_load || 0,
    },
    recommended_tasks: recommendedTasks,
    tasks_to_avoid: tasksToAvoid,
    optimal_focus_zones: optimalFocusZones,
  };

  // Store budget
  await storeCognitiveBudget(userId, budget);

  return budget;
}

function generateRecommendedTasks(
  totalEnergy: number,
  emotionalLoad: EmotionalLoad,
  mentalState: any
): Record<string, any> {
  const tasks: any = {
    high_impact_creative: [],
    clinical_admin: [],
    glp_planning: [],
    financial_review: [],
    strategic_thinking: [],
  };

  if (totalEnergy > 70) {
    tasks.high_impact_creative.push({
      description: "2 high-impact creative blocks",
      duration: "2-3 hours",
      priority: "HIGH",
    });
    tasks.strategic_thinking.push({
      description: "Strategic planning session",
      duration: "1 hour",
      priority: "MEDIUM",
    });
  } else if (totalEnergy > 50) {
    tasks.clinical_admin.push({
      description: "1 clinical admin block",
      duration: "1-2 hours",
      priority: "MEDIUM",
    });
    tasks.glp_planning.push({
      description: "1 short GLP planning block",
      duration: "30-45 minutes",
      priority: "MEDIUM",
    });
  } else {
    tasks.clinical_admin.push({
      description: "Light clinical admin",
      duration: "30-60 minutes",
      priority: "LOW",
    });
  }

  return tasks;
}

function generateTasksToAvoid(
  totalEnergy: number,
  emotionalLoad: EmotionalLoad,
  mentalState: any
): Record<string, any> {
  const avoid: string[] = [];

  if (totalEnergy < 50) {
    avoid.push("Complex engineering work");
    avoid.push("High-intensity financial reviews");
    avoid.push("Deep strategic planning");
  }

  if (emotionalLoad === "HIGH") {
    avoid.push("High-stakes decisions");
    avoid.push("Conflict resolution");
    avoid.push("Complex problem-solving");
  }

  if (mentalState?.fatigue_level > 60) {
    avoid.push("Long meetings");
    avoid.push("Context switching");
    avoid.push("Multi-tasking");
  }

  return { tasks: avoid };
}

function generateOptimalFocusZones(energyIdentity: any[], fatigueIdentity: any[]): Record<string, any> {
  // Simplified - in production, this would use actual energy patterns
  return {
    morning: {
      best_for: ["Deep work", "Creative tasks", "Strategic thinking"],
      energy_level: "HIGH",
    },
    afternoon: {
      best_for: ["Administrative tasks", "Meetings", "Collaboration"],
      energy_level: "MEDIUM",
    },
    evening: {
      best_for: ["Light tasks", "Review", "Planning"],
      energy_level: "LOW",
    },
  };
}

async function storeCognitiveBudget(userId: string, budget: CognitiveBudget): Promise<void> {
  await supabaseServer
    .from("jarvis_cognitive_budgets")
    .upsert({
      ...budget,
    } as any, {
      onConflict: "user_id,budget_date",
    });
}

export async function getCognitiveBudget(
  userId: string,
  budgetDate?: string
): Promise<CognitiveBudget | null> {
  const date = budgetDate ? new Date(budgetDate) : new Date();
  const dateStr = date.toISOString().split("T")[0];

  const { data } = await supabaseServer
    .from("jarvis_cognitive_budgets")
    .select("*")
    .eq("user_id", userId)
    .eq("budget_date", dateStr)
    .single();

  if (data) {
    return data as CognitiveBudget;
  }

  return null;
}

