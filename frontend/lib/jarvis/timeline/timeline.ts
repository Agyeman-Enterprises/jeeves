import type {
  JarvisUserIdentity,
  JarvisTaskClassification,
  JarvisRoutedTask,
} from "../types";
import { supabaseServer } from "@/lib/supabase/server";

interface LogTimelineArgs {
  user: JarvisUserIdentity;
  query: string;
  classification: JarvisTaskClassification;
  routedTask?: JarvisRoutedTask;
}

interface TimelineEvent {
  id?: string;
}

export async function logTimelineEvent(
  args: LogTimelineArgs
): Promise<TimelineEvent | null> {
  const { user, query, classification, routedTask } = args;

  const { data, error } = await supabaseServer
    .from("jarvis_timeline_events")
    .insert({
      user_id: user.userId,
      workspace_id: user.workspaceId ?? null,
      event_type: "JARVIS_INTERACTION",
      label: classification.kind,
      description: query,
      related_resource: null,
      payload: {
        classification,
        routedTask,
      } as any,
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    console.error("logTimelineEvent error:", error);
    return null;
  }

  return { id: (data as any).id };
}

