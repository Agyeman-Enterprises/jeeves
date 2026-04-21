import { supabaseServer } from "@/lib/supabase/server";
import type { CrossUniverseEvent, UniverseDomain } from "./types";
import { ingestEvent } from "../gem/router";
import { analyzeCrossDomainImpact } from "./analytics";

export async function ingestCrossUniverseEvent(
  userId: string,
  eventType: string,
  sourceDomain: UniverseDomain,
  payload: Record<string, any>,
  sourceNodeId?: string
): Promise<string> {
  // Analyze cross-domain impact
  const impactAnalysis = await analyzeCrossDomainImpact(userId, sourceDomain, eventType, payload);

  // Determine target domains
  const targetDomains = impactAnalysis.affected_domains || [];

  // Create cross-universe event
  const { data, error } = await supabaseServer
    .from("jarvis_cross_universe_events")
    .insert({
      user_id: userId,
      event_type: eventType,
      source_domain: sourceDomain,
      target_domains: targetDomains,
      source_node_id: sourceNodeId,
      affected_node_ids: impactAnalysis.affected_node_ids,
      payload,
      impact_analysis: impactAnalysis,
      status: "PENDING",
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to ingest cross-universe event: ${error?.message}`);
  }

  const eventId = (data as any).id;

  // Route to GEM for each target domain
  for (const targetDomain of targetDomains) {
    try {
      await ingestEvent(userId, eventType, sourceDomain.toLowerCase(), {
        ...payload,
        cross_universe_event_id: eventId,
        source_domain: sourceDomain,
        target_domain: targetDomain,
      });
    } catch (error) {
      console.error(`Failed to route event to domain ${targetDomain}:`, error);
    }
  }

  // Update event status
  await (supabaseServer as any)
    .from("jarvis_cross_universe_events")
    .update({
      status: "ROUTED",
      routing_decision: {
        target_domains: targetDomains,
        routed_at: new Date().toISOString(),
      },
    } as any)
    .eq("id", eventId);

  return eventId;
}

export async function getCrossUniverseEvents(
  userId: string,
  sourceDomain?: UniverseDomain,
  limit: number = 50
): Promise<CrossUniverseEvent[]> {
  let query = supabaseServer
    .from("jarvis_cross_universe_events")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (sourceDomain) {
    query = query.eq("source_domain", sourceDomain);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get cross-universe events: ${error.message}`);
  }

  return (data || []) as CrossUniverseEvent[];
}

