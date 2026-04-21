import { supabaseServer } from "@/lib/supabase/server";
import type { MetaInsight, InsightType, LearningDomain } from "./types";
import { analyzeDecisionPatterns } from "./decisions";
import { getAgentPerformance, evaluateAgentPerformance } from "./agents";
import { getAverageForecastAccuracy } from "./forecasts";
import { getNotificationSuppressionLevel } from "./notifications";

export async function runMetaLearningCycle(userId: string): Promise<MetaInsight[]> {
  const insights: MetaInsight[] = [];

  // 1. Decision Loop
  const decisionInsights = await analyzeDecisions(userId);
  insights.push(...decisionInsights);

  // 2. Agent Performance Loop
  const agentInsights = await analyzeAgents(userId);
  insights.push(...agentInsights);

  // 3. Forecasting Loop
  const forecastInsights = await analyzeForecasts(userId);
  insights.push(...forecastInsights);

  // 4. Notification Loop
  const notificationInsights = await analyzeNotifications(userId);
  insights.push(...notificationInsights);

  // Store insights
  for (const insight of insights) {
    await storeMetaInsight(userId, insight);
  }

  return insights;
}

async function analyzeDecisions(userId: string): Promise<MetaInsight[]> {
  const insights: MetaInsight[] = [];

  const decisionTypes = ["ACTION", "RECOMMENDATION", "ROUTING", "AUTONOMY", "SCHEDULING"] as const;

  for (const decisionType of decisionTypes) {
    const patterns = await analyzeDecisionPatterns(userId, decisionType, 30);

    if (patterns.averageScore < 0.3) {
      insights.push({
        user_id: userId,
        insight_type: "DECISION",
        insight_category: decisionType,
        insight_summary: `Decision quality is below optimal for ${decisionType.toLowerCase()} decisions`,
        insight_details: patterns,
        confidence: 0.7,
        action_taken: {
          recommendation: "Review and adjust decision-making rules for this type",
        },
        impact_score: patterns.averageScore,
      });
    }

    if (patterns.feedbackDistribution.REJECTED + patterns.feedbackDistribution.OVERRIDDEN > 0.2) {
      insights.push({
        user_id: userId,
        insight_type: "DECISION",
        insight_category: decisionType,
        insight_summary: `High rejection rate for ${decisionType.toLowerCase()} decisions`,
        insight_details: patterns,
        confidence: 0.8,
        action_taken: {
          recommendation: "Adjust approach to better align with user preferences",
        },
        impact_score: -0.3,
      });
    }
  }

  return insights;
}

async function analyzeAgents(userId: string): Promise<MetaInsight[]> {
  const insights: MetaInsight[] = [];

  // Get all active agents
  const { data: agents } = await supabaseServer
    .from("jarvis_agents")
    .select("slug")
    .eq("is_active", true);

  if (!agents) return insights;

  const periodEnd = new Date();
  const periodStart = new Date();
  periodStart.setDate(periodStart.getDate() - 7); // Last week

  for (const agent of agents) {
    try {
      // Evaluate performance
      await evaluateAgentPerformance(userId, (agent as any).slug, periodStart, periodEnd);

      // Get latest performance
      const performance = await getAgentPerformance(userId, (agent as any).slug, 1);
      if (performance.length > 0) {
        const perf = performance[0];
        if (perf.performance_score !== undefined && perf.performance_score < 0.3) {
          insights.push({
            user_id: userId,
            insight_type: "AGENT",
            insight_category: (agent as any).slug,
            insight_summary: `Agent ${(agent as any).slug} is underperforming`,
            insight_details: perf,
            confidence: 0.8,
            action_taken: {
              recommendation: "Reduce critical task assignment or increase supervision",
              trust_level: perf.trust_level,
              autonomy_adjustment: perf.autonomy_adjustment,
            },
            impact_score: perf.performance_score,
          });
        }
      }
    } catch (error) {
      // Agent may not have runs in this period
      continue;
    }
  }

  return insights;
}

async function analyzeForecasts(userId: string): Promise<MetaInsight[]> {
  const insights: MetaInsight[] = [];

  const forecastTypes = ["CLINIC_LOAD", "FINANCIAL", "BURNOUT_RISK", "GLP_OUTCOMES", "OPS_BOTTLENECK"] as const;

  for (const forecastType of forecastTypes) {
    const avgAccuracy = await getAverageForecastAccuracy(userId, forecastType, 30);

    if (avgAccuracy < 0.6) {
      insights.push({
        user_id: userId,
        insight_type: "FORECAST",
        insight_category: forecastType,
        insight_summary: `Forecast accuracy is below optimal for ${forecastType.toLowerCase()}`,
        insight_details: { average_accuracy: avgAccuracy },
        confidence: 0.7,
        action_taken: {
          recommendation: "Review and adjust forecasting model parameters",
        },
        impact_score: avgAccuracy - 0.6, // Negative if below threshold
      });
    }
  }

  return insights;
}

async function analyzeNotifications(userId: string): Promise<MetaInsight[]> {
  const insights: MetaInsight[] = [];

  // Get notification types from recent notifications
  const { data: notifications } = await supabaseServer
    .from("jarvis_notification_effectiveness")
    .select("notification_type")
    .eq("user_id", userId)
    .gte("created_at", new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString());

  if (!notifications) return insights;

  const notificationTypes = [...new Set(notifications.map((n: any) => n.notification_type))];

  for (const notificationType of notificationTypes) {
    const suppressionLevel = await getNotificationSuppressionLevel(userId, notificationType);

    if (suppressionLevel === "SUPPRESSED" || suppressionLevel === "HIGH") {
      insights.push({
        user_id: userId,
        insight_type: "NOTIFICATION",
        insight_category: notificationType,
        insight_summary: `Notification type ${notificationType} is being suppressed due to low value`,
        insight_details: { suppression_level: suppressionLevel },
        confidence: 0.8,
        action_taken: {
          recommendation: "Reduce or suppress this notification type",
          suppression_level: suppressionLevel,
        },
        impact_score: -0.5,
      });
    }
  }

  return insights;
}

async function storeMetaInsight(userId: string, insight: Omit<MetaInsight, "id" | "created_at">): Promise<string> {
  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + 30); // Expire after 30 days

  const { data, error } = await supabaseServer
    .from("jarvis_meta_insights")
    .insert({
      ...insight,
      expires_at: expiresAt.toISOString(),
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to store meta insight: ${error?.message}`);
  }

  return (data as any).id;
}

