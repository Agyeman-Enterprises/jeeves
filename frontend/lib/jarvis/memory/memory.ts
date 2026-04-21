import type { JarvisUserIdentity } from "../types";
import { supabaseServer } from "@/lib/supabase/server";

interface MemoryReadArgs {
  user: JarvisUserIdentity;
  query: string;
}

interface MemoryWriteArgs {
  user: JarvisUserIdentity;
  query: string;
  payload?: any;
}

export async function readMemory(args: MemoryReadArgs): Promise<any[]> {
  const { user, query } = args;

  // Simple text search using ilike on title/content for now
  const { data, error } = await supabaseServer
    .from("jarvis_memory_chunks")
    .select("*")
    .eq("user_id", user.userId)
    .or(
      `title.ilike.%${query}%,content.ilike.%${query}%`
    )
    .order("created_at", { ascending: false })
    .limit(20);

  if (error) {
    console.error("readMemory error:", error);
    return [];
  }

  return data ?? [];
}

export async function writeMemory(args: MemoryWriteArgs): Promise<any> {
  const { user, query, payload } = args;

  const { data, error } = await supabaseServer
    .from("jarvis_memory_chunks")
    .insert({
      user_id: user.userId,
      workspace_id: user.workspaceId ?? null,
      title: payload?.title ?? null,
      content: payload?.content ?? query,
      tags: payload?.tags ?? [],
      source: payload?.source ?? "chat",
    } as any)
    .select("*")
    .single();

  if (error) {
    console.error("writeMemory error:", error);
    throw error;
  }

  return data;
}

