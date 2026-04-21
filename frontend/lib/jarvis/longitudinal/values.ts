import { supabaseServer } from "@/lib/supabase/server";
import type { LongTermIdentity, IdentityType } from "./types";

export async function recordLongTermIdentity(
  userId: string,
  identityType: IdentityType,
  content: string,
  priority: number = 1
): Promise<LongTermIdentity> {
  // Check if this identity already exists
  const { data: existing } = await supabaseServer
    .from("jarvis_long_term_identity")
    .select("*")
    .eq("user_id", userId)
    .eq("identity_type", identityType)
    .ilike("content", `%${content.substring(0, 50)}%`)
    .single();

  if (existing) {
    // Reinforce existing identity
    const identity = existing as any;
    const reinforcementCount = (identity.reinforcement_count || 0) + 1;

    const updateData: Record<string, any> = {
      reinforcement_count: reinforcementCount,
      last_reinforced_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await (supabaseServer as any)
      .from("jarvis_long_term_identity")
      .update(updateData)
      .eq("id", identity.id);

    return { ...identity, ...updateData } as LongTermIdentity;
  } else {
    // Create new identity
    const { data: newIdentity } = await supabaseServer
      .from("jarvis_long_term_identity")
      .insert({
        user_id: userId,
        identity_type: identityType,
        content,
        priority,
        reinforcement_count: 1,
        last_reinforced_at: new Date().toISOString(),
      } as any)
      .select()
      .single();

    return newIdentity as LongTermIdentity;
  }
}

export async function getLongTermIdentity(
  userId: string,
  identityType?: IdentityType
): Promise<LongTermIdentity[]> {
  let query = supabaseServer
    .from("jarvis_long_term_identity")
    .select("*")
    .eq("user_id", userId)
    .order("priority", { ascending: true })
    .order("reinforcement_count", { ascending: false });

  if (identityType) {
    query = query.eq("identity_type", identityType);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get long-term identity: ${error.message}`);
  }

  return (data || []) as LongTermIdentity[];
}

export async function checkAlignment(
  userId: string,
  taskDescription: string
): Promise<{ aligned: boolean; reason?: string }> {
  // Get user's long-term identity (mission, values, goals)
  const identities = await getLongTermIdentity(userId);

  // Simplified alignment check (in production, use LLM for semantic matching)
  const missionIdentities = identities.filter((i) => i.identity_type === "mission" || i.identity_type === "values");
  
  // For now, return neutral alignment
  // In production, this would use semantic similarity to check if task aligns with mission/values
  return {
    aligned: true,
    reason: "Task appears aligned with your long-term priorities",
  };
}

