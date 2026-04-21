// Timeline repository - typed wrappers for jarvis_timeline_events table
import { createJarvisDb } from "./index";

export async function createTimelineEvent(input: {
  userId: string;
  workspaceId?: string;
  eventType?: string;
  eventData?: Record<string, any>;
  timestamp?: string;
}) {
  const db = createJarvisDb();
  return db.insert("jarvis_timeline_events", {
    user_id: input.userId,
    workspace_id: input.workspaceId || null,
  } as any);
}

export async function getTimelineEventById(id: string) {
  const db = createJarvisDb();
  return db.getById("jarvis_timeline_events", id);
}

export async function listTimelineEventsForUser(userId: string, limit = 100) {
  const db = createJarvisDb();
  return db.list("jarvis_timeline_events", [{ column: "user_id", value: userId }], limit);
}

