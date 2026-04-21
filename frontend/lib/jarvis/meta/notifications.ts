import { supabaseServer } from "@/lib/supabase/server";
import type { NotificationEffectiveness, SuppressionLevel } from "./types";

export async function recordNotificationInteraction(
  userId: string,
  notificationType: string,
  notificationId: string,
  wasAcknowledged: boolean,
  wasActedUpon: boolean,
  wasIgnored: boolean,
  timeToAcknowledgeSeconds?: number,
  timeToActionSeconds?: number
): Promise<string> {
  // Calculate value score
  const valueScore = calculateValueScore(wasAcknowledged, wasActedUpon, wasIgnored, timeToActionSeconds);

  // Determine suppression level
  const suppressionLevel = determineSuppressionLevel(valueScore, wasIgnored);

  const { data, error } = await supabaseServer
    .from("jarvis_notification_effectiveness")
    .insert({
      user_id: userId,
      notification_type: notificationType,
      notification_id: notificationId,
      was_acknowledged: wasAcknowledged,
      was_acted_upon: wasActedUpon,
      was_ignored: wasIgnored,
      time_to_acknowledge_seconds: timeToAcknowledgeSeconds,
      time_to_action_seconds: timeToActionSeconds,
      value_score: valueScore,
      suppression_level: suppressionLevel,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to record notification interaction: ${error?.message}`);
  }

  return (data as any).id;
}

function calculateValueScore(
  wasAcknowledged: boolean,
  wasActedUpon: boolean,
  wasIgnored: boolean,
  timeToActionSeconds?: number
): number {
  let score = 0;

  if (wasActedUpon) {
    score = 0.8; // High value - user acted on it
    // Bonus for quick action
    if (timeToActionSeconds && timeToActionSeconds < 300) {
      score = 1.0; // Very high value
    }
  } else if (wasAcknowledged) {
    score = 0.3; // Medium value - user saw it
  } else if (wasIgnored) {
    score = -0.5; // Negative value - user ignored it
  }

  return Math.max(-1, Math.min(1, score));
}

function determineSuppressionLevel(valueScore: number, wasIgnored: boolean): SuppressionLevel {
  if (wasIgnored && valueScore < -0.3) {
    return "SUPPRESSED";
  }
  if (valueScore < -0.2) {
    return "HIGH";
  }
  if (valueScore < 0) {
    return "MEDIUM";
  }
  if (valueScore < 0.3) {
    return "LOW";
  }
  return "NONE";
}

export async function getNotificationEffectiveness(
  userId: string,
  notificationType: string,
  limit: number = 50
): Promise<NotificationEffectiveness[]> {
  const { data, error } = await supabaseServer
    .from("jarvis_notification_effectiveness")
    .select("*")
    .eq("user_id", userId)
    .eq("notification_type", notificationType)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    throw new Error(`Failed to get notification effectiveness: ${error.message}`);
  }

  return (data || []) as NotificationEffectiveness[];
}

export async function getNotificationSuppressionLevel(
  userId: string,
  notificationType: string
): Promise<SuppressionLevel> {
  // Get recent notifications of this type
  const recent = await getNotificationEffectiveness(userId, notificationType, 20);

  if (recent.length === 0) {
    return "NONE"; // Default - no suppression
  }

  // Calculate average value score
  const scores = recent.filter((n) => n.value_score !== undefined).map((n) => n.value_score!);
  const averageScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;

  // Count ignored
  const ignoredCount = recent.filter((n) => n.was_ignored).length;
  const ignoredRatio = ignoredCount / recent.length;

  // Determine suppression level
  if (ignoredRatio > 0.7 && averageScore < -0.3) {
    return "SUPPRESSED";
  }
  if (averageScore < -0.2) {
    return "HIGH";
  }
  if (averageScore < 0) {
    return "MEDIUM";
  }
  if (averageScore < 0.3) {
    return "LOW";
  }
  return "NONE";
}

