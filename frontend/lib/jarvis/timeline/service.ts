// Timeline service - log and list timeline events
import { createJarvisDb } from "@/lib/db/jarvis";
import type { Database } from "@/lib/supabase/types";
import { emitEvent } from "@/lib/jarvis/events/gem/bus";

type TimelineRow = Database["public"]["Tables"]["jarvis_timeline_events"]["Row"];
type TimelineInsert = Database["public"]["Tables"]["jarvis_timeline_events"]["Insert"];

export async function logTimelineEvent(input: {
  userId: string;
  workspaceId: string;
  category?: string;
  label: string;
  refType?: string;
  refId?: string;
  data?: Record<string, any>;
}): Promise<TimelineRow> {
  const db = createJarvisDb();
  const payload: Partial<TimelineInsert> = {
    user_id: input.userId,
    workspace_id: input.workspaceId,
    // Assume these columns will exist later:
    category: input.category ?? "generic",
    label: input.label,
    ref_type: input.refType ?? null,
    ref_id: input.refId ?? null,
    data: input.data ?? null,
  } as any;

  const timeline = await db.insert("jarvis_timeline_events" as any, payload as any);

  // Emit timeline event recorded
  try {
    await emitEvent({
      type: 'jarvis.timeline.event.recorded',
      source: 'jarvis.timeline',
      workspaceId: input.workspaceId,
      userId: input.userId,
      subjectId: timeline.id,
      payload: {
        workspaceId: input.workspaceId,
        userId: input.userId,
        timelineEventId: timeline.id,
        timelineType: input.category || 'generic',
        label: input.label,
      },
    });
  } catch (error) {
    console.error('[TimelineService] Failed to emit timeline.recorded event:', error);
  }

  return timeline;
}

export async function listTimelineEvents(input: {
  userId: string;
  workspaceId: string;
  limit?: number;
}): Promise<TimelineRow[]> {
  const db = createJarvisDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;
  const { userId, workspaceId, limit = 100 } = input;

  const { data, error } = await client
    .from("jarvis_timeline_events")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return (data || []) as TimelineRow[];
}

