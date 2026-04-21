import { supabaseServer } from "@/lib/supabase/server";
import type { RefactoringProposal, RefactoringLevel } from "./types";
import { checkSafetyConstraints } from "./safety";

export async function createRefactoringProposal(
  userId: string,
  proposal: Omit<RefactoringProposal, "id" | "user_id" | "created_at" | "updated_at" | "status">
): Promise<string> {
  // Check safety constraints
  const safetyCheck = await checkSafetyConstraints(userId, proposal.refactoring_level, proposal.target_component);
  if (!safetyCheck.allowed) {
    throw new Error(`Refactoring proposal violates safety constraints: ${safetyCheck.reason}`);
  }

  // Generate risk assessment
  const riskAssessment = generateRiskAssessment(proposal);

  // Generate implementation steps
  const implementationSteps = generateImplementationSteps(proposal);

  // Generate estimated impact
  const estimatedImpact = generateEstimatedImpact(proposal);

  const { data, error } = await supabaseServer
    .from("jarvis_refactoring_proposals")
    .insert({
      ...proposal,
      user_id: userId,
      risk_assessment: riskAssessment,
      implementation_steps: implementationSteps,
      estimated_impact: estimatedImpact,
      status: "PROPOSED",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create refactoring proposal: ${error?.message}`);
  }

  return (data as any).id;
}

function generateRiskAssessment(proposal: Partial<RefactoringProposal>): Record<string, any> {
  // Simplified risk assessment
  const riskLevel = proposal.refactoring_level === "FULL_BRAIN_SCHEMA" ? "HIGH" : 
                    proposal.refactoring_level === "MODULAR" ? "MEDIUM" : "LOW";

  return {
    risk_level: riskLevel,
    potential_issues: [],
    mitigation_strategies: [],
    rollback_plan: proposal.rollback_plan || {},
  };
}

function generateImplementationSteps(proposal: Partial<RefactoringProposal>): Record<string, any> {
  return {
    steps: [
      { step: 1, description: "Backup current state", estimated_time: "5 minutes" },
      { step: 2, description: "Implement changes", estimated_time: "varies" },
      { step: 3, description: "Test changes", estimated_time: "10 minutes" },
      { step: 4, description: "Monitor performance", estimated_time: "ongoing" },
    ],
  };
}

function generateEstimatedImpact(proposal: Partial<RefactoringProposal>): Record<string, any> {
  return {
    performance_improvement: "TBD",
    complexity_change: "TBD",
    maintenance_impact: "TBD",
  };
}

export async function getRefactoringProposals(
  userId: string,
  status?: RefactoringProposal["status"],
  level?: RefactoringLevel
): Promise<RefactoringProposal[]> {
  let query = supabaseServer
    .from("jarvis_refactoring_proposals")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (status) {
    query = query.eq("status", status);
  }

  if (level) {
    query = query.eq("refactoring_level", level);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get refactoring proposals: ${error.message}`);
  }

  return (data || []) as RefactoringProposal[];
}

export async function approveRefactoringProposal(
  userId: string,
  proposalId: string
): Promise<void> {
  await (supabaseServer as any)
    .from("jarvis_refactoring_proposals")
    .update({
      status: "APPROVED",
      approved_by_user: true,
      approved_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    } as any)
    .eq("id", proposalId)
    .eq("user_id", userId);
}

export async function rejectRefactoringProposal(
  userId: string,
  proposalId: string
): Promise<void> {
  await (supabaseServer as any)
    .from("jarvis_refactoring_proposals")
    .update({
      status: "REJECTED",
      updated_at: new Date().toISOString(),
    } as any)
    .eq("id", proposalId)
    .eq("user_id", userId);
}

