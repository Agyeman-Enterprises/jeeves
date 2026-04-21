// lib/jarvis/brain/timeline.ts

import { createJarvisDb } from "@/lib/db/jarvis";

type WriteSignalArgs = {
  text: string;
  type: string;
  workspace?: string;
  userId?: string;
};

export async function writeSignal({ text, type, workspace, userId }: WriteSignalArgs) {
  if (!userId) return null;

  try {
    const db = createJarvisDb();
    return await db.insert("jarvis_signals", {
      user_id: userId,
      workspace_id: workspace || null,
    } as any);
  } catch (error) {
    console.error("[JarvisTimeline] insert error:", error);
    return null;
  }
}

