import { runAllAudits } from "./audit";
import { createRefactoringProposal } from "./proposals";
import type { RefactoringProposal, RefactoringLevel } from "./types";
import { canAutoImplement } from "./safety";

export async function runSelfRefactoringCycle(userId: string): Promise<{
  audits: string[];
  proposals: string[];
}> {
  // Run all audits
  const auditIds = await runAllAudits(userId);

  // Analyze audit results and generate proposals
  const proposalIds = await generateProposalsFromAudits(userId, auditIds);

  return {
    audits: auditIds,
    proposals: proposalIds,
  };
}

async function generateProposalsFromAudits(
  userId: string,
  auditIds: string[]
): Promise<string[]> {
  const proposalIds: string[] = [];

  // Get audit results
  const { data: audits } = await supabaseServer
    .from("jarvis_self_audits")
    .select("*")
    .in("id", auditIds);

  if (!audits) {
    return proposalIds;
  }

  // Generate proposals based on audit findings
  for (const audit of audits) {
    const auditData = audit as any;
    const recommendations = auditData.recommendations?.recommendations || [];

    for (const recommendation of recommendations) {
      // Determine refactoring level based on recommendation type
      const level = determineRefactoringLevel(recommendation.type);

      // Create proposal
      try {
        const proposal: Partial<RefactoringProposal> = {
          proposal_name: recommendation.recommendation || "Refactoring proposal",
          proposal_description: `Generated from ${auditData.audit_type} audit`,
          refactoring_level: level,
          target_component: recommendation.agent || recommendation.forecast_type || "UNKNOWN",
          current_state: {},
          proposed_state: {},
          expected_benefits: {
            description: recommendation.recommendation,
          },
        };

        const proposalId = await createRefactoringProposal(userId, proposal as any);
        proposalIds.push(proposalId);
      } catch (error) {
        // Proposal may violate safety constraints - skip it
        console.warn("Failed to create proposal:", error);
      }
    }
  }

  return proposalIds;
}

function determineRefactoringLevel(recommendationType: string): RefactoringLevel {
  if (recommendationType.includes("AGENT_OPTIMIZATION") || recommendationType.includes("AGENT")) {
    return "MODULAR";
  }
  if (recommendationType.includes("FORECAST") || recommendationType.includes("MODEL")) {
    return "STRUCTURAL";
  }
  if (recommendationType.includes("GRAPH") || recommendationType.includes("SCHEMA")) {
    return "FULL_BRAIN_SCHEMA";
  }
  return "STRUCTURAL"; // Default
}

// Import supabaseServer
import { supabaseServer } from "@/lib/supabase/server";

