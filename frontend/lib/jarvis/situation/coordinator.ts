import type { SituationRoomSnapshot, SituationRoomType } from "./types";
import { generateClinicSituationRoom } from "./clinic";
import { generateFinancialSituationRoom } from "./financial";
import { generateBusinessOpsSituationRoom } from "./business";
import { generateLifeSituationRoom } from "./life";
import { supabaseServer } from "@/lib/supabase/server";

export async function generateSituationRoom(
  userId: string,
  roomType: SituationRoomType
): Promise<SituationRoomSnapshot> {
  let snapshot: SituationRoomSnapshot;

  switch (roomType) {
    case "CLINIC":
      snapshot = await generateClinicSituationRoom(userId);
      break;
    case "FINANCIAL":
      snapshot = await generateFinancialSituationRoom(userId);
      break;
    case "BUSINESS_OPS":
      snapshot = await generateBusinessOpsSituationRoom(userId);
      break;
    case "LIFE":
      snapshot = await generateLifeSituationRoom(userId);
      break;
    default:
      throw new Error(`Unknown room type: ${roomType}`);
  }

  // Store snapshot
  await storeSnapshot(userId, snapshot);

  return snapshot;
}

export async function generateAllSituationRooms(
  userId: string
): Promise<Record<SituationRoomType, SituationRoomSnapshot>> {
  const [clinic, financial, businessOps, life] = await Promise.all([
    generateClinicSituationRoom(userId),
    generateFinancialSituationRoom(userId),
    generateBusinessOpsSituationRoom(userId),
    generateLifeSituationRoom(userId),
  ]);

  // Store all snapshots
  await Promise.all([
    storeSnapshot(userId, clinic),
    storeSnapshot(userId, financial),
    storeSnapshot(userId, businessOps),
    storeSnapshot(userId, life),
  ]);

  return {
    CLINIC: clinic,
    FINANCIAL: financial,
    BUSINESS_OPS: businessOps,
    LIFE: life,
  };
}

async function storeSnapshot(userId: string, snapshot: SituationRoomSnapshot): Promise<void> {
  // Delete old snapshot for this room
  await (supabaseServer as any)
    .from("jarvis_situation_room_snapshots")
    .delete()
    .eq("user_id", userId)
    .eq("room_type", snapshot.room_type);

  // Insert new snapshot
  await supabaseServer
    .from("jarvis_situation_room_snapshots")
    .insert({
      user_id: userId,
      room_type: snapshot.room_type,
      snapshot_data: snapshot.snapshot_data,
      alerts: snapshot.alerts,
      recommendations: snapshot.recommendations,
      anomalies: snapshot.anomalies,
      agent_status: snapshot.agent_status,
      last_updated: new Date().toISOString(),
    } as any);
}

export async function getLatestSnapshot(
  userId: string,
  roomType: SituationRoomType
): Promise<SituationRoomSnapshot | null> {
  const { data } = await supabaseServer
    .from("jarvis_situation_room_snapshots")
    .select("*")
    .eq("user_id", userId)
    .eq("room_type", roomType)
    .order("last_updated", { ascending: false })
    .limit(1)
    .single();

  if (data) {
    return {
      id: (data as any).id,
      user_id: userId,
      room_type: roomType,
      snapshot_data: (data as any).snapshot_data,
      alerts: (data as any).alerts,
      recommendations: (data as any).recommendations,
      anomalies: (data as any).anomalies,
      agent_status: (data as any).agent_status,
      last_updated: (data as any).last_updated,
      created_at: (data as any).created_at,
    };
  }

  return null;
}

