// Journal service - write and list journal entries
import { createJarvisDb } from "@/lib/db/jarvis";
import type { Database } from "@/lib/supabase/types";
import { emitEvent } from "@/lib/jarvis/events/gem/bus";

type JournalRow = Database["public"]["Tables"]["jarvis_journal_entries"]["Row"];
type JournalInsert = Database["public"]["Tables"]["jarvis_journal_entries"]["Insert"];

export async function writeJournalEntry(input: {
  userId: string;
  workspaceId: string;
  type?: string;
  content: string;
  metadata?: Record<string, any>;
}): Promise<JournalRow> {
  const db = createJarvisDb();
  const payload: Partial<JournalInsert> = {
    user_id: input.userId,
    workspace_id: input.workspaceId,
    // Assume "type" and "content" text columns will exist in later migrations.
    type: input.type ?? "generic",
    content: input.content,
    // Optionally later: metadata JSONB column
  } as any;

  const journal = await db.insert("jarvis_journal_entries" as any, payload as any);

  // Emit journal entry created event
  try {
    await emitEvent({
      type: 'jarvis.journal.entry.created',
      source: 'jarvis.journal',
      workspaceId: input.workspaceId,
      userId: input.userId,
      subjectId: journal.id,
      payload: {
        workspaceId: input.workspaceId,
        userId: input.userId,
        journalEntryId: journal.id,
        title: (journal as any).title || undefined,
      },
    });
  } catch (error) {
    console.error('[JournalService] Failed to emit journal.created event:', error);
  }

  return journal;
}

export async function listJournalEntries(input: {
  userId: string;
  workspaceId: string;
  limit?: number;
}): Promise<JournalRow[]> {
  const db = createJarvisDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;
  const { userId, workspaceId, limit = 50 } = input;

  const { data, error } = await client
    .from("jarvis_journal_entries")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return (data || []) as JournalRow[];
}

