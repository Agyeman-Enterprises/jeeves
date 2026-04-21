import { supabaseServer } from "@/lib/supabase/server";
import type { UMGEventMap } from "./types";
import { createNode, getNode } from "../cuil/graph";
import { createEdge } from "../cuil/graph";
import type { UniverseNode, UniverseEdge } from "../cuil/types";

export async function mapEventToGraph(
  userId: string,
  eventId: string,
  sourceNodeId?: string
): Promise<string> {
  // Get event details
  const { data: event } = await supabaseServer
    .from("jarvis_event_mesh_events")
    .select("*")
    .eq("id", eventId)
    .single();

  if (!event) {
    throw new Error(`Event not found: ${eventId}`);
  }

  const eventData = event as any;

  // Create or get source node if not provided
  let sourceNode: UniverseNode | null = null;
  if (sourceNodeId) {
    sourceNode = await getNode(userId, "", ""); // Would get actual node
  } else {
    // Create event node
    sourceNode = {
      user_id: userId,
      node_type: "EVENT",
      domain: eventData.event_category as any,
      external_id: eventId,
      source_system: eventData.source,
      label: `${eventData.event_type} - ${new Date(eventData.created_at).toLocaleDateString()}`,
      description: `Event: ${eventData.event_type}`,
      metadata: eventData.payload,
    };
    const nodeId = await createNode(sourceNode);
    sourceNode.id = nodeId;
  }

  // Determine affected nodes based on event payload
  const affectedNodeIds: string[] = [];
  const createdEdges: string[] = [];

  // Create edges based on event type and payload
  if (eventData.payload.patient_id) {
    // Link to patient node
    const patientNode = await getNode(userId, "solopractice", eventData.payload.patient_id);
    if (patientNode) {
      const edgeId = await createEdge({
        user_id: userId,
        source_node_id: sourceNode.id!,
        target_node_id: patientNode.id!,
        edge_type: "AFFECTED_BY" as any, // UMG extends edge types
        weight: 1.0,
      });
      createdEdges.push(edgeId);
      affectedNodeIds.push(patientNode.id!);
    }
  }

  if (eventData.payload.entity_id) {
    // Link to entity node
    const entityNode = await getNode(userId, "nexus", eventData.payload.entity_id);
    if (entityNode) {
      const edgeId = await createEdge({
        user_id: userId,
        source_node_id: sourceNode.id!,
        target_node_id: entityNode.id!,
        edge_type: "AFFECTED_BY" as any, // UMG extends edge types
        weight: 1.0,
      });
      createdEdges.push(edgeId);
      affectedNodeIds.push(entityNode.id!);
    }
  }

  // Create event map record
  const { data, error } = await supabaseServer
    .from("jarvis_universe_event_map")
    .insert({
      user_id: userId,
      event_id: eventId,
      source_node_id: sourceNode.id,
      affected_node_ids: affectedNodeIds,
      created_edges: createdEdges,
      graph_impact: {
        nodes_created: sourceNodeId ? 0 : 1,
        edges_created: createdEdges.length,
        nodes_affected: affectedNodeIds.length,
      },
    } as any)
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to map event to graph: ${error?.message}`);
  }

  return (data as any).id;
}

export async function getEventMap(
  userId: string,
  eventId: string
): Promise<UMGEventMap | null> {
  const { data } = await supabaseServer
    .from("jarvis_universe_event_map")
    .select("*")
    .eq("user_id", userId)
    .eq("event_id", eventId)
    .single();

  if (data) {
    return data as UMGEventMap;
  }

  return null;
}

