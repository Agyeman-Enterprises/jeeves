// Seed default situation rooms for new workspaces
// 
// USAGE:
// - Call this function when a new workspace is created
// - Or use the API endpoint: POST /api/nexus/situations/seed?workspaceId=...&userId=...
// - This creates a default room with Event Feed, Error List, and Metric Card widgets
//
import { getSupabaseClient } from "@/lib/supabase/client";

export async function createDefaultSituationRoom(workspaceId: string, userId: string) {
  const client = getSupabaseClient();
  const now = new Date().toISOString();

  const { data: room, error: roomError } = await client
    .from('nexus_situation_rooms')
    .insert({
      workspace_id: workspaceId,
      user_id: userId,
      slug: 'default',
      name: 'Default Situation Room',
      is_default: true,
      config: {},
      created_at: now,
      updated_at: now
    } as any)
    .select('*')
    .single() as any;

  if (roomError || !room) {
    throw new Error(`Failed to create default situation room: ${roomError?.message || 'Unknown error'}`);
  }

  const widgetResult = await (client.from('nexus_situation_widgets').insert([
    {
      room_id: room.id,
      workspace_id: workspaceId,
      user_id: userId,
      kind: 'event_feed',
      title: 'Live Event Feed',
      position: { x: 0, y: 0, w: 6, h: 6 },
      config: { types: ['jarvis.command.received', 'jarvis.command.completed', 'jarvis.command.failed', 'jarvis.error.logged'], limit: 50 },
      created_at: now,
      updated_at: now
    },
    {
      room_id: room.id,
      workspace_id: workspaceId,
      user_id: userId,
      kind: 'error_list',
      title: 'Recent Errors',
      position: { x: 6, y: 0, w: 6, h: 6 },
      config: { types: ['jarvis.error.logged'], limit: 20 },
      created_at: now,
      updated_at: now
    },
    {
      room_id: room.id,
      workspace_id: workspaceId,
      user_id: userId,
      kind: 'metric_card',
      title: 'Command Volume (24h)',
      position: { x: 0, y: 6, w: 3, h: 3 },
      config: { metric: 'commands_last_24h' },
      created_at: now,
      updated_at: now
    },
  ] as any) as any);

  const widgetError = (widgetResult as any).error;

  if (widgetError) {
    throw new Error(`Failed to create default widgets: ${widgetError.message}`);
  }

  return room;
}

