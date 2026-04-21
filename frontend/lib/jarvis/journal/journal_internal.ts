import type { JarvisUserIdentity } from "../types";
import { supabaseServer } from "@/lib/supabase/server";

// Internal helper used by tools

interface AppendJournalInternalArgs {
  user: JarvisUserIdentity;
  query: string;
  payload?: any;
}

export async function appendJournalInternal(
  args: AppendJournalInternalArgs
): Promise<any> {
  const { user, query, payload } = args;

  const { data, error } = await supabaseServer
    .from("jarvis_journal_entries")
    .insert({
      user_id: user.userId,
      workspace_id: user.workspaceId ?? null,
      query,
      classification: null,
      routed_task: null,
      tool_result: null,
      meta: payload ?? {},
    } as any)
    .select("*")
    .single();

  if (error) {
    console.error("appendJournalInternal error:", error);
    throw error;
  }

  return data;
}

