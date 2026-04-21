// Memory service - store and retrieve memory chunks
import { createJarvisDb } from "@/lib/db/jarvis";
import type { Database } from "@/lib/supabase/types";
import { emitEvent } from "@/lib/jarvis/events/gem/bus";

type MemoryRow = Database["public"]["Tables"]["jarvis_memory_chunks"]["Row"];
type MemoryInsert = Database["public"]["Tables"]["jarvis_memory_chunks"]["Insert"];

/**
 * Create a new memory chunk for a user/workspace.
 */
export async function storeMemoryChunk(input: {
  userId: string;
  workspaceId: string;
  content: string;
  source?: string;
  tags?: string[];
}): Promise<MemoryRow> {
  const db = createJarvisDb();
  const payload: Partial<MemoryInsert> = {
    user_id: input.userId,
    workspace_id: input.workspaceId,
    // content-like field (call it "body" or "content" if present later)
    // For now, assume a "content" text column will exist in future migrations.
    // @ts-expect-error - content column will exist once expanded
    content: input.content,
    // optional metadata columns can be added later (source, tags, etc.)
  };

  const memory = await db.insert("jarvis_memory_chunks" as any, payload as any);

  // Emit memory created event
  try {
    await emitEvent({
      type: 'jarvis.memory.item.created',
      source: 'jarvis.memory',
      workspaceId: input.workspaceId,
      userId: input.userId,
      subjectId: memory.id,
      payload: {
        workspaceId: input.workspaceId,
        userId: input.userId,
        memoryId: memory.id,
        memoryType: input.source || 'generic',
        summary: input.content.substring(0, 100),
      },
    });
  } catch (error) {
    console.error('[MemoryService] Failed to emit memory.created event:', error);
  }

  return memory;
}

/**
 * Simple text search over memory chunks for a user/workspace.
 * For now, use ILIKE on content; can be upgraded to embeddings later.
 */
export async function searchMemoryChunks(input: {
  userId: string;
  workspaceId: string;
  query: string;
  limit?: number;
}): Promise<MemoryRow[]> {
  const db = createJarvisDb();
  const { userId, workspaceId, query, limit = 20 } = input;

  // Use the generic list() and then let Supabase do simple filtering
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;

  const result = await client
    .from("jarvis_memory_chunks")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId)
    .ilike("content" as any, `%${query}%`)
    .limit(limit);
  
  const { data, error } = result as { data: any; error: any };

  if (error) throw error;
  return (data || []) as MemoryRow[];
}

/**
 * Fetch the most recent memory chunks for a user/workspace.
 */
export async function getRecentMemories(input: {
  userId: string;
  workspaceId: string;
  limit?: number;
}): Promise<MemoryRow[]> {
  const db = createJarvisDb();
  const client = (db as any)["client"] as import("@supabase/supabase-js").SupabaseClient<Database>;
  const { userId, workspaceId, limit = 20 } = input;

  const { data, error } = await client
    .from("jarvis_memory_chunks")
    .select("*")
    .eq("user_id", userId)
    .eq("workspace_id", workspaceId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return (data || []) as MemoryRow[];
}

