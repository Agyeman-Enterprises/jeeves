// Journal repository - typed wrappers for jarvis_journal_entries table
import { createJarvisDb } from "./index";

export async function createJournalEntry(input: {
  userId: string;
  workspaceId?: string;
  entryType?: string;
  entryData?: Record<string, any>;
}) {
  const db = createJarvisDb();
  return db.insert("jarvis_journal_entries", {
    user_id: input.userId,
    workspace_id: input.workspaceId || null,
  } as any);
}

export async function getJournalEntryById(id: string) {
  const db = createJarvisDb();
  return db.getById("jarvis_journal_entries", id);
}

export async function listJournalEntriesForUser(userId: string, limit = 100) {
  const db = createJarvisDb();
  return db.list("jarvis_journal_entries", [{ column: "user_id", value: userId }], limit);
}

