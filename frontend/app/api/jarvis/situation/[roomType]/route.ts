import { NextRequest, NextResponse } from "next/server";
import { generateSituationRoom, getLatestSnapshot } from "@/lib/jarvis/situation/coordinator";
import type { SituationRoomType } from "@/lib/jarvis/situation/types";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ roomType: string }> }
) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    const { roomType: roomTypeParam } = await params;
    const roomType = roomTypeParam.toUpperCase() as SituationRoomType;
    const useCache = req.nextUrl.searchParams.get("cache") !== "false";

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    if (!["CLINIC", "FINANCIAL", "BUSINESS_OPS", "LIFE"].includes(roomType)) {
      return NextResponse.json(
        { error: "Invalid room type" },
        { status: 400 }
      );
    }

    // Check for cached snapshot if requested
    if (useCache) {
      const cached = await getLatestSnapshot(userId, roomType);
      if (cached) {
        const cacheAge = Date.now() - new Date(cached.last_updated || 0).getTime();
        // Use cache if less than 5 minutes old
        if (cacheAge < 5 * 60 * 1000) {
          return NextResponse.json({ snapshot: cached, cached: true });
        }
      }
    }

    // Generate fresh snapshot
    const snapshot = await generateSituationRoom(userId, roomType);

    return NextResponse.json({ snapshot, cached: false });
  } catch (error: any) {
    console.error("Situation room error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

