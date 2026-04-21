import { supabaseServer } from "@/lib/supabase/server";

export type EmotionalContextType = "BURNOUT" | "LATE_NIGHT" | "OVERLOAD" | "STRESS" | "NORMAL";

export interface EmotionalContext {
  user_id: string;
  context_type: EmotionalContextType;
  signals: Record<string, any>;
  tone_adjustment: Record<string, any>;
  expires_at: string;
}

export async function detectEmotionalContext(userId: string): Promise<EmotionalContextType> {
  const now = new Date();
  const hour = now.getHours();

  // Late night detection (after 10 PM or before 6 AM)
  if (hour >= 22 || hour < 6) {
    await setEmotionalContext(userId, "LATE_NIGHT", {
      hour,
      time_of_day: hour >= 22 ? "late_night" : "early_morning",
    }, {
      softer: true,
      more_concise: true,
    });
    return "LATE_NIGHT";
  }

  // Check for existing active context
  const { data: activeContexts } = await supabaseServer
    .from("jarvis_emotional_context")
    .select("*")
    .eq("user_id", userId)
    .gt("expires_at", now.toISOString())
    .order("detected_at", { ascending: false })
    .limit(1);

  if (activeContexts && activeContexts.length > 0) {
    return (activeContexts[0] as any).context_type;
  }

  // TODO: Add more sophisticated detection based on:
  // - Task completion rates
  // - Response times
  // - Decision patterns
  // - Calendar density
  // - Message volume

  return "NORMAL";
}

export async function setEmotionalContext(
  userId: string,
  contextType: EmotionalContextType,
  signals: Record<string, any>,
  toneAdjustment: Record<string, any>,
  durationHours: number = 2
): Promise<void> {
  const expiresAt = new Date();
  expiresAt.setHours(expiresAt.getHours() + durationHours);

  await supabaseServer
    .from("jarvis_emotional_context")
    .insert({
      user_id: userId,
      context_type: contextType,
      signals,
      tone_adjustment: toneAdjustment,
      expires_at: expiresAt.toISOString(),
    } as any);
}

export async function getToneAdjustments(userId: string): Promise<Record<string, any> | null> {
  const contextType = await detectEmotionalContext(userId);

  if (contextType === "LATE_NIGHT") {
    return { softer: true, more_concise: true };
  }

  if (contextType === "BURNOUT" || contextType === "OVERLOAD") {
    return { softer: true, encouraging: true, more_concise: true };
  }

  if (contextType === "STRESS") {
    return { firmer: true, clearer: true, action_oriented: true };
  }

  return null;
}

