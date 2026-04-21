import { NextRequest, NextResponse } from "next/server";
import { generateAllSituationRooms } from "@/lib/jarvis/situation/coordinator";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    // Generate all situation rooms
    const rooms = await generateAllSituationRooms(userId);

    return NextResponse.json({ rooms });
  } catch (error: any) {
    console.error("Situation rooms error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

