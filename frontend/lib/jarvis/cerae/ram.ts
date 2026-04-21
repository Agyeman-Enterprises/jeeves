import { supabaseServer } from "@/lib/supabase/server";
import type { ResourceAllocation, ResourceType, CapabilityFit } from "./types";
import { getCognitiveBudget } from "./cognitive";
import { getCurrentMentalState } from "../emotional/state";

export interface RAMEvaluation {
  importance: number; // 0-1
  urgency: number; // 0-1
  effort_level: number; // 0-1
  output_multiplier: number; // 0-1
  energy_match: number; // 0-1
  opportunity_cost: number;
  capability_fit: CapabilityFit;
  overall_score: number; // 0-1
}

export async function evaluateResourceAllocation(
  userId: string,
  resourceType: ResourceType,
  allocationTarget: string,
  targetId?: string,
  context?: Record<string, any>
): Promise<RAMEvaluation> {
  // Get current cognitive budget
  const budget = await getCognitiveBudget(userId);
  const mentalState = await getCurrentMentalState(userId);

  // Evaluate importance (will this matter in 1 week, 1 month, 1 year?)
  const importance = evaluateImportance(allocationTarget, context);

  // Evaluate urgency (deadline-driven? time-sensitive?)
  const urgency = evaluateUrgency(allocationTarget, context);

  // Evaluate effort level (how much cognitive load does it require?)
  const effortLevel = evaluateEffortLevel(allocationTarget, resourceType, context);

  // Evaluate output multiplier (does this create more leverage later?)
  const outputMultiplier = evaluateOutputMultiplier(allocationTarget, context);

  // Evaluate energy matching (is this good for your current state?)
  const energyMatch = evaluateEnergyMatch(
    allocationTarget,
    resourceType,
    budget,
    mentalState,
    effortLevel
  );

  // Evaluate opportunity cost (what are you not doing if you do this?)
  const opportunityCost = evaluateOpportunityCost(allocationTarget, resourceType, context);

  // Evaluate capability fit (does it require you, or can someone/agent else do it?)
  const capabilityFit = evaluateCapabilityFit(allocationTarget, resourceType, context);

  // Calculate overall score (weighted combination)
  const overallScore =
    importance * 0.25 +
    urgency * 0.2 +
    outputMultiplier * 0.2 +
    energyMatch * 0.15 +
    (1 - effortLevel) * 0.1 +
    (1 - opportunityCost / 100) * 0.1;

  return {
    importance,
    urgency,
    effort_level: effortLevel,
    output_multiplier: outputMultiplier,
    energy_match: energyMatch,
    opportunity_cost: opportunityCost,
    capability_fit: capabilityFit,
    overall_score: Math.max(0, Math.min(1, overallScore)),
  };
}

function evaluateImportance(target: string, context?: Record<string, any>): number {
  // Simplified - in production, this would use historical data, project importance, etc.
  if (target.includes("CRITICAL") || target.includes("URGENT") || target.includes("PATIENT")) {
    return 0.9;
  }
  if (target.includes("FINANCIAL") || target.includes("TAX") || target.includes("REVENUE")) {
    return 0.8;
  }
  if (target.includes("STRATEGIC") || target.includes("HIGH_IMPACT")) {
    return 0.7;
  }
  return 0.5; // Default medium importance
}

function evaluateUrgency(target: string, context?: Record<string, any>): number {
  // Check for deadlines, time-sensitive indicators
  if (context?.deadline) {
    const deadline = new Date(context.deadline);
    const daysUntil = (deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24);
    if (daysUntil < 1) return 1.0;
    if (daysUntil < 3) return 0.8;
    if (daysUntil < 7) return 0.6;
  }
  if (target.includes("URGENT") || target.includes("IMMEDIATE")) {
    return 0.9;
  }
  return 0.3; // Default low urgency
}

function evaluateEffortLevel(target: string, resourceType: ResourceType, context?: Record<string, any>): number {
  // Higher effort = more cognitive load required
  if (resourceType === "COGNITIVE" || resourceType === "CREATIVE_STRATEGIC") {
    if (target.includes("DEEP_WORK") || target.includes("STRATEGIC") || target.includes("ENGINEERING")) {
      return 0.9; // Very high effort
    }
    return 0.6; // Medium-high effort
  }
  if (resourceType === "OPERATIONAL" || resourceType === "TEMPORAL") {
    return 0.4; // Medium effort
  }
  return 0.3; // Lower effort
}

function evaluateOutputMultiplier(target: string, context?: Record<string, any>): number {
  // Does this create more leverage later?
  if (target.includes("AUTOMATION") || target.includes("SYSTEM") || target.includes("INFRASTRUCTURE")) {
    return 0.9; // High multiplier
  }
  if (target.includes("STRATEGIC") || target.includes("LEVERAGE") || target.includes("SCALE")) {
    return 0.8; // High multiplier
  }
  if (target.includes("ROUTINE") || target.includes("MAINTENANCE")) {
    return 0.3; // Low multiplier
  }
  return 0.5; // Default medium multiplier
}

function evaluateEnergyMatch(
  target: string,
  resourceType: ResourceType,
  budget: any,
  mentalState: any,
  effortLevel: number
): number {
  if (!budget || !mentalState) return 0.5; // Default neutral

  const totalEnergy = budget.total_energy_percentage || 50;
  const fatigueLevel = mentalState.fatigue_level || 0;

  // High energy tasks match well when energy is high
  if (effortLevel > 0.7 && totalEnergy > 70 && fatigueLevel < 30) {
    return 0.9; // Great match
  }

  // Low energy tasks match well when energy is low
  if (effortLevel < 0.4 && totalEnergy < 50) {
    return 0.8; // Good match
  }

  // Mismatch: high effort task when energy is low
  if (effortLevel > 0.7 && totalEnergy < 50) {
    return 0.2; // Poor match
  }

  return 0.5; // Neutral match
}

function evaluateOpportunityCost(target: string, resourceType: ResourceType, context?: Record<string, any>): number {
  // What are you not doing if you do this?
  // Simplified - in production, this would compare against other potential allocations
  if (resourceType === "COGNITIVE" || resourceType === "CREATIVE_STRATEGIC") {
    return 50; // Higher opportunity cost for cognitive resources
  }
  return 30; // Lower opportunity cost for other resources
}

function evaluateCapabilityFit(target: string, resourceType: ResourceType, context?: Record<string, any>): CapabilityFit {
  // Does it require Dr. A, or can someone/agent else do it?
  if (target.includes("CLINICAL_DECISION") || target.includes("STRATEGIC") || target.includes("CREATIVE")) {
    return "DR_A_REQUIRED";
  }
  if (target.includes("ADMIN") || target.includes("ROUTINE") || target.includes("DATA_ENTRY")) {
    return "STAFF_CAN_DO";
  }
  if (target.includes("AUTOMATION") || target.includes("ROUTINE_TASK") || target.includes("CATEGORIZATION")) {
    return "AGENT_CAN_DO";
  }
  if (target.includes("AUTOMATED") || target.includes("SYSTEM")) {
    return "AUTOMATED";
  }
  return "DR_A_REQUIRED"; // Default to requiring Dr. A
}

export async function createResourceAllocation(
  userId: string,
  allocation: Omit<ResourceAllocation, "id" | "created_at" | "updated_at">,
  evaluation: RAMEvaluation
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_resource_allocations")
    .insert({
      ...allocation,
      importance_score: evaluation.importance,
      urgency_score: evaluation.urgency,
      effort_level: evaluation.effort_level,
      output_multiplier: evaluation.output_multiplier,
      energy_match_score: evaluation.energy_match,
      opportunity_cost: evaluation.opportunity_cost,
      capability_fit: evaluation.capability_fit,
      priority: Math.floor((1 - evaluation.overall_score) * 10) + 1, // Lower score = higher priority
      status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create resource allocation: ${error?.message}`);
  }

  return (data as any).id;
}

