// src/lib/nexus/situations/service.ts
import { getSupabaseClient } from "@/lib/supabase/client";
import type { SituationRoom, SituationWidget } from './types';

export async function getSituationRoomBySlug(
  workspaceId: string,
  slug: string
): Promise<{ room: SituationRoom | null; widgets: SituationWidget[] }> {
  const client = getSupabaseClient();

  const { data: rooms, error: roomErr } = await client
    .from('nexus_situation_rooms')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('slug', slug)
    .limit(1) as any;

  if (roomErr) throw roomErr;
  const room = rooms?.[0] ?? null;
  if (!room) return { room: null, widgets: [] };

  const { data: widgets, error: widgetErr } = await client
    .from('nexus_situation_widgets')
    .select('*')
    .eq('room_id', room.id)
    .order('created_at', { ascending: true }) as any;

  if (widgetErr) throw widgetErr;

  return { room: room as SituationRoom, widgets: (widgets ?? []) as SituationWidget[] };
}

