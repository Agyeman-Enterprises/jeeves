// Memory repository — typed wrappers for jarvis_memory_chunks table
// Schema added in migration 041: session_id, role, content, agent, importance, source
import { getSupabaseClient } from "@/lib/supabase/client";

export interface MemoryChunk {
  id: string;
  user_id: string;
  workspace_id?: string | null;
  session_id?: string | null;
  role: "user" | "assistant" | "system";
  content: string;
  agent?: string | null;
  importance: number;
  source: string;
  created_at: string;
}

export interface SaveMessageInput {
  userId: string;
  sessionId: string;
  role: "user" | "assistant" | "system";
  content: string;
  agent?: string;
  importance?: number;
  workspaceId?: string;
}

/** Save a single conversation turn to persistent memory */
export async function saveMessage(input: SaveMessageInput): Promise<void> {
  const supabase = getSupabaseClient();
  const { error } = await (supabase as any)
    .from("jarvis_memory_chunks")
    .insert({
      user_id:      input.userId,
      session_id:   input.sessionId,
      role:         input.role,
      content:      input.content,
      agent:        input.agent ?? null,
      importance:   input.importance ?? 5,
      source:       "chat",
      workspace_id: input.workspaceId ?? null,
    });

  if (error) {
    console.error("[memory] Failed to save message:", error.message);
  }
}

/** Load recent conversation history for a session */
export async function getSessionHistory(
  sessionId: string,
  limit = 50
): Promise<MemoryChunk[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await (supabase as any)
    .from("jarvis_memory_chunks")
    .select("*")
    .eq("session_id", sessionId)
    .order("created_at", { ascending: true })
    .limit(limit);

  if (error) {
    console.error("[memory] Failed to load session:", error.message);
    return [];
  }
  return (data ?? []) as MemoryChunk[];
}

/** Load recent memory across all sessions for a user (for briefing/reflection) */
export async function getRecentMemory(
  userId: string,
  limit = 100
): Promise<MemoryChunk[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await (supabase as any)
    .from("jarvis_memory_chunks")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("[memory] Failed to load recent memory:", error.message);
    return [];
  }
  return (data ?? []) as MemoryChunk[];
}

/** Backward-compatible shim used by brain/memory.ts and router/route.ts */
export async function createMemoryChunk(input: {
  userId: string;
  workspaceId?: string;
  chunkType?: string;
  chunkData?: Record<string, any>;
}): Promise<{ id: string }> {
  const supabase = getSupabaseClient();
  const content = input.chunkData?.text ?? input.chunkData?.content ?? JSON.stringify(input.chunkData ?? {});
  const { data, error } = await (supabase as any)
    .from("jarvis_memory_chunks")
    .insert({
      user_id:      input.userId,
      workspace_id: input.workspaceId ?? null,
      session_id:   null,
      role:         "user" as const,
      content,
      agent:        input.chunkType ?? null,
      importance:   input.chunkData?.importance === "high" ? 8 : 5,
      source:       "memory.add",
    })
    .select("id")
    .single();

  if (error) throw new Error(error.message);
  return data as { id: string };
}

/** Get high-importance memories for reflection synthesis */
export async function getImportantMemory(
  userId: string,
  minImportance = 7,
  limit = 50
): Promise<MemoryChunk[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await (supabase as any)
    .from("jarvis_memory_chunks")
    .select("*")
    .eq("user_id", userId)
    .gte("importance", minImportance)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("[memory] Failed to load important memory:", error.message);
    return [];
  }
  return (data ?? []) as MemoryChunk[];
}
