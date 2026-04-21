import { supabaseServer } from "@/lib/supabase/server";
import type { UMGEmbedding } from "./types";
import { getNode } from "../cuil/graph";
import type { UniverseNode } from "../cuil/types";

export async function createEmbedding(
  userId: string,
  nodeId: string,
  textContent: string,
  embeddingModel: string = "text-embedding-3-small"
): Promise<string> {
  // Generate embedding using OpenAI (or local model)
  const embedding = await generateEmbedding(textContent, embeddingModel);

  const { data, error } = await supabaseServer
    .from("jarvis_universe_embeddings")
    .upsert({
      user_id: userId,
      node_id: nodeId,
      embedding_model: embeddingModel,
      embedding: embedding,
      text_content: textContent,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "node_id,embedding_model",
    })
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create embedding: ${error?.message}`);
  }

  return (data as any).id;
}

async function generateEmbedding(text: string, model: string): Promise<number[]> {
  // In production, this would call OpenAI API or local embedding model
  // For now, return a placeholder
  // TODO: Implement actual embedding generation
  const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
  
  if (!OPENAI_API_KEY) {
    console.warn("OPENAI_API_KEY not set, returning placeholder embedding");
    return new Array(1536).fill(0).map(() => Math.random());
  }

  try {
    const response = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: model,
        input: text,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.data[0].embedding;
  } catch (error) {
    console.error("Error generating embedding:", error);
    // Return placeholder on error
    return new Array(1536).fill(0).map(() => Math.random());
  }
}

export async function semanticSearch(
  userId: string,
  query: string,
  limit: number = 10,
  embeddingModel: string = "text-embedding-3-small"
): Promise<Array<{ node: UniverseNode; similarity: number; embedding: UMGEmbedding }>> {
  // Generate query embedding
  const queryEmbedding = await generateEmbedding(query, embeddingModel);

  // In production, this would use vector similarity search (pgvector)
  // For now, we'll do a simplified search
  // TODO: Implement proper vector similarity search using pgvector

  // Get all embeddings for this user
  const { data: embeddings } = await supabaseServer
    .from("jarvis_universe_embeddings")
    .select("*")
    .eq("user_id", userId)
    .eq("embedding_model", embeddingModel);

  if (!embeddings || embeddings.length === 0) {
    return [];
  }

  // Calculate cosine similarity (simplified - would use pgvector in production)
  const similarities = await Promise.all(
    embeddings.map(async (emb: any) => {
      const similarity = cosineSimilarity(queryEmbedding, emb.embedding || []);
      const node = await getNode(userId, "", ""); // Would get actual node
      return {
        node: node || ({} as UniverseNode),
        similarity,
        embedding: emb as UMGEmbedding,
      };
    })
  );

  // Sort by similarity and return top results
  return similarities
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit)
    .filter((s) => s.similarity > 0.5); // Filter low similarity results
}

function cosineSimilarity(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) return 0;

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  if (normA === 0 || normB === 0) return 0;

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

export async function getEmbedding(
  userId: string,
  nodeId: string,
  embeddingModel: string = "text-embedding-3-small"
): Promise<UMGEmbedding | null> {
  const { data } = await supabaseServer
    .from("jarvis_universe_embeddings")
    .select("*")
    .eq("user_id", userId)
    .eq("node_id", nodeId)
    .eq("embedding_model", embeddingModel)
    .single();

  if (data) {
    return data as UMGEmbedding;
  }

  return null;
}

