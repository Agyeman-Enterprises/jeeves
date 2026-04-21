// lib/jarvis/brain/journal.ts

import { createJournalEntry } from "@/lib/db/jarvis/journal";

export async function writeJournalEntry(text: string, type: string, userId?: string) {
  if (type !== "journal") return null;
  if (!text.trim()) return null;
  if (!userId) return null;

  try {
    return await createJournalEntry({
      userId,
      entryType: "journal",
      entryData: { text, type } as any,
    });
  } catch (error) {
    console.error("[JarvisJournal] insert error:", error);
    return null;
  }
}

