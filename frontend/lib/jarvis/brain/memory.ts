// lib/jarvis/brain/memory.ts

import { createMemoryChunk } from "@/lib/db/jarvis/memory";

export async function storeMemory(text: string, type: string, userId?: string) {
  if (!text.trim()) return null;
  if (!userId) return null;

  try {
    return await createMemoryChunk({
      userId,
      chunkType: type,
      chunkData: { text, importance: type === "journal" ? "high" : "normal", scope: "short" } as any,
    });
  } catch (error) {
    console.error("[JarvisMemory] insert error:", error);
    return null;
  }
}

