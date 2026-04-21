import type {
  JarvisUserIdentity,
  JarvisTaskClassification,
  JarvisRoutedTask,
  JarvisToolResult,
} from "../types";
import { supabaseServer } from "@/lib/supabase/server";

interface CreateJournalArgs {
  user: JarvisUserIdentity;
  query: string;
  classification: JarvisTaskClassification;
  routedTask?: JarvisRoutedTask;
  toolResult?: JarvisToolResult;
}

interface JournalEntry {
  id?: string;
}

export async function createJournalEntry(
  args: CreateJournalArgs
): Promise<JournalEntry | null> {
  const { user, query, classification, routedTask, toolResult } = args;

  const { data, error } = await supabaseServer
    .from("jarvis_journal_entries")
    .insert({
      user_id: user.userId,
      workspace_id: user.workspaceId ?? null,
      query,
      classification: classification as any,
      routed_task: routedTask as any ?? null,
      tool_result: toolResult as any ?? null,
      meta: {},
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    console.error("createJournalEntry error:", error);
    return null;
  }

  return { id: (data as any).id };
}

