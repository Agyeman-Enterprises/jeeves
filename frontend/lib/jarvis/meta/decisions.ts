import { supabaseServer } from "@/lib/supabase/server";
import type { DecisionOutcome, UserFeedback, DecisionType } from "./types";

export async function recordDecisionOutcome(
  userId: string,
  decisionId: string,
  decisionType: DecisionType,
  decisionContext: Record<string, any>,
  predictedOutcome?: Record<string, any>,
  actualOutcome?: Record<string, any>,
  userFeedback?: UserFeedback
): Promise<string> {
  // Calculate outcome score based on feedback and actual vs predicted
  const outcomeScore = calculateOutcomeScore(predictedOutcome, actualOutcome, userFeedback);

  // Generate learned insight
  const learnedInsight = generateInsight(decisionType, predictedOutcome, actualOutcome, userFeedback);

  const { data, error } = await supabaseServer
    .from("jarvis_decision_outcomes")
    .insert({
      user_id: userId,
      decision_id: decisionId,
      decision_type: decisionType,
      decision_context: decisionContext,
      predicted_outcome: predictedOutcome,
      actual_outcome: actualOutcome,
      user_feedback: userFeedback,
      outcome_score: outcomeScore,
      learned_insight: learnedInsight,
      outcome_recorded_at: new Date().toISOString(),
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to record decision outcome: ${error?.message}`);
  }

  return (data as any).id;
}

function calculateOutcomeScore(
  predicted?: Record<string, any>,
  actual?: Record<string, any>,
  feedback?: UserFeedback
): number {
  let score = 0;

  // Base score on user feedback
  if (feedback === "ACCEPTED") {
    score = 0.8;
  } else if (feedback === "EDITED") {
    score = 0.5;
  } else if (feedback === "REJECTED" || feedback === "OVERRIDDEN") {
    score = -0.5;
  } else if (feedback === "IGNORED") {
    score = -0.2;
  }

  // Adjust based on predicted vs actual (if both available)
  if (predicted && actual) {
    // Simple comparison - in production, this would be more sophisticated
    const predictedKeys = Object.keys(predicted);
    const actualKeys = Object.keys(actual);
    const matchCount = predictedKeys.filter((k) => actualKeys.includes(k) && predicted[k] === actual[k]).length;
    const totalKeys = Math.max(predictedKeys.length, actualKeys.length);
    const matchRatio = totalKeys > 0 ? matchCount / totalKeys : 0;
    score = (score + matchRatio) / 2; // Average of feedback and accuracy
  }

  return Math.max(-1, Math.min(1, score)); // Clamp to -1 to 1
}

function generateInsight(
  decisionType: DecisionType,
  predicted?: Record<string, any>,
  actual?: Record<string, any>,
  feedback?: UserFeedback
): string {
  if (feedback === "REJECTED" || feedback === "OVERRIDDEN") {
    return `Decision was ${feedback.toLowerCase()}. Consider alternative approaches for similar ${decisionType.toLowerCase()} decisions.`;
  }
  if (feedback === "ACCEPTED" && predicted && actual) {
    return `Decision was accepted and outcome matched prediction. Continue using similar approach for ${decisionType.toLowerCase()} decisions.`;
  }
  if (feedback === "EDITED") {
    return `Decision was edited. User preferences may differ from initial approach for ${decisionType.toLowerCase()} decisions.`;
  }
  return `Decision recorded. Monitor outcomes to refine ${decisionType.toLowerCase()} decision-making.`;
}

export async function analyzeDecisionPatterns(
  userId: string,
  decisionType?: DecisionType,
  days: number = 30
): Promise<{
  averageScore: number;
  feedbackDistribution: Record<UserFeedback, number>;
  insights: string[];
}> {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  let query = supabaseServer
    .from("jarvis_decision_outcomes")
    .select("*")
    .eq("user_id", userId)
    .gte("created_at", cutoffDate.toISOString());

  if (decisionType) {
    query = query.eq("decision_type", decisionType);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to analyze decision patterns: ${error.message}`);
  }

  const outcomes = (data || []) as DecisionOutcome[];

  // Calculate average score
  const scores = outcomes.filter((o) => o.outcome_score !== undefined).map((o) => o.outcome_score!);
  const averageScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;

  // Calculate feedback distribution
  const feedbackDistribution: Record<string, number> = {
    ACCEPTED: 0,
    EDITED: 0,
    REJECTED: 0,
    OVERRIDDEN: 0,
    IGNORED: 0,
  };

  outcomes.forEach((o) => {
    if (o.user_feedback) {
      feedbackDistribution[o.user_feedback] = (feedbackDistribution[o.user_feedback] || 0) + 1;
    }
  });

  // Generate insights
  const insights: string[] = [];
  if (averageScore < 0.3) {
    insights.push(`Decision quality is below optimal. Consider reviewing ${decisionType || "decision"} patterns.`);
  }
  if (feedbackDistribution.REJECTED + feedbackDistribution.OVERRIDDEN > outcomes.length * 0.2) {
    insights.push(`High rejection rate detected. User preferences may differ from current approach.`);
  }
  if (feedbackDistribution.ACCEPTED > outcomes.length * 0.7) {
    insights.push(`High acceptance rate. Current approach aligns well with user preferences.`);
  }

  return {
    averageScore,
    feedbackDistribution: feedbackDistribution as Record<UserFeedback, number>,
    insights,
  };
}

