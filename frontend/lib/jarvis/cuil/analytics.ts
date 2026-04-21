import { supabaseServer } from "@/lib/supabase/server";
import type { UniverseDomain, CrossPrediction, CrossRecommendation } from "./types";
import { getNodeEdges, getRelatedNodes } from "./graph";
import { simulateFinancial } from "../simulation/financial";
import { simulateOperational } from "../simulation/operational";
import { simulateClinical } from "../simulation/clinical";

export async function analyzeCrossDomainImpact(
  userId: string,
  sourceDomain: UniverseDomain,
  eventType: string,
  payload: Record<string, any>
): Promise<{
  affected_domains: UniverseDomain[];
  affected_node_ids: string[];
  impact_severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  impact_details: Record<string, any>;
}> {
  const affectedDomains: UniverseDomain[] = [];
  const affectedNodeIds: string[] = [];
  const impactDetails: Record<string, any> = {};

  // Domain-specific impact analysis
  switch (sourceDomain) {
    case "CLINICAL":
      // Clinical events can affect financial, operations, personal
      if (eventType.includes("PATIENT") || eventType.includes("GLP")) {
        affectedDomains.push("FINANCIAL", "OPERATIONS");
        // Trigger financial projection
        try {
          const financialSim = await simulateFinancial(userId, {
            scenario: "CLINICAL_IMPACT",
            time_horizon: "1MONTH",
          });
          impactDetails.financial_impact = financialSim;
        } catch (error) {
          console.error("Failed to simulate financial impact:", error);
        }
      }
      if (eventType.includes("HOSPITALIZATION") || eventType.includes("CRITICAL")) {
        affectedDomains.push("PERSONAL");
        impactDetails.personal_impact = "High cognitive load expected";
      }
      break;

    case "FINANCIAL":
      // Financial events can affect operations, personal, clinical
      if (eventType.includes("REVENUE") || eventType.includes("CASHFLOW")) {
        affectedDomains.push("OPERATIONS", "CLINICAL");
        impactDetails.operational_impact = "Resource allocation may need adjustment";
      }
      if (eventType.includes("TAX") || eventType.includes("LIABILITY")) {
        affectedDomains.push("OPERATIONS");
      }
      break;

    case "EDUCATION":
      // Education events can affect media, operations
      if (eventType.includes("ENGAGEMENT") || eventType.includes("PERFORMANCE")) {
        affectedDomains.push("MEDIA", "OPERATIONS");
        impactDetails.media_impact = "Content strategy may need adjustment";
      }
      break;

    case "MEDIA":
      // Media events can affect crypto, gaming, education
      if (eventType.includes("CONTENT") || eventType.includes("PUBLISH")) {
        affectedDomains.push("CRYPTO", "GAMING");
        impactDetails.crypto_impact = "Token engagement may increase";
        impactDetails.gaming_impact = "Game content may need updates";
      }
      break;

    case "ENGINEERING":
      // Engineering events can affect manufacturing, operations, financial
      if (eventType.includes("PROTOTYPE") || eventType.includes("DEVELOPMENT")) {
        affectedDomains.push("MANUFACTURING", "OPERATIONS", "FINANCIAL");
        impactDetails.manufacturing_impact = "Production timeline may change";
        impactDetails.financial_impact = "CapEx projections may need update";
      }
      break;
  }

  // Determine impact severity
  let impactSeverity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" = "LOW";
  if (affectedDomains.length > 2) {
    impactSeverity = "HIGH";
  } else if (affectedDomains.length > 0) {
    impactSeverity = "MEDIUM";
  }
  if (eventType.includes("CRITICAL") || eventType.includes("URGENT")) {
    impactSeverity = "CRITICAL";
  }

  return {
    affected_domains: affectedDomains,
    affected_node_ids: affectedNodeIds,
    impact_severity: impactSeverity,
    impact_details: impactDetails,
  };
}

export async function createCrossPrediction(
  userId: string,
  predictionType: CrossPrediction["prediction_type"],
  sourceDomain: UniverseDomain,
  targetDomains: UniverseDomain[],
  predictionValue: Record<string, any>,
  factorsUsed?: Record<string, any>
): Promise<string> {
  // Build interdependency map
  const interdependencyMap: Record<string, any> = {};
  for (const targetDomain of targetDomains) {
    interdependencyMap[targetDomain] = {
      connection_strength: 0.7, // Simplified - would calculate from graph
      factors: factorsUsed || {},
    };
  }

  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + 30); // Expire after 30 days

  const { data, error } = await supabaseServer
    .from("jarvis_cross_predictions")
    .insert({
      user_id: userId,
      prediction_type: predictionType,
      source_domain: sourceDomain,
      target_domains: targetDomains,
      prediction_value: predictionValue,
      confidence_score: 0.7, // Simplified - would calculate from historical accuracy
      factors_used: factorsUsed,
      interdependency_map: interdependencyMap,
      expires_at: expiresAt.toISOString(),
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create cross prediction: ${error?.message}`);
  }

  return (data as any).id;
}

export async function createCrossRecommendation(
  userId: string,
  recommendationType: CrossRecommendation["recommendation_type"],
  affectedDomains: UniverseDomain[],
  recommendationSummary: string,
  recommendationDetails: Record<string, any>,
  interdependencyReasoning: Record<string, any>,
  priority: number = 1
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_cross_recommendations")
    .insert({
      user_id: userId,
      recommendation_type: recommendationType,
      affected_domains: affectedDomains,
      recommendation_summary: recommendationSummary,
      recommendation_details: recommendationDetails,
      interdependency_reasoning: interdependencyReasoning,
      priority,
      status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create cross recommendation: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getCrossRecommendations(
  userId: string,
  status?: "PENDING" | "ACCEPTED" | "REJECTED" | "IMPLEMENTED",
  limit: number = 20
): Promise<CrossRecommendation[]> {
  let query = supabaseServer
    .from("jarvis_cross_recommendations")
    .select("*")
    .eq("user_id", userId)
    .order("priority", { ascending: true })
    .order("created_at", { ascending: false })
    .limit(limit);

  if (status) {
    query = query.eq("status", status);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get cross recommendations: ${error.message}`);
  }

  return (data || []) as CrossRecommendation[];
}

