import { NextRequest, NextResponse } from "next/server";
import { createUniverseSnapshot, getLatestSnapshot } from "@/lib/jarvis/cuil/snapshots";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { snapshot_type } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const snapshotId = await createUniverseSnapshot(userId, snapshot_type || "ON_DEMAND");

    return NextResponse.json({ ok: true, snapshot_id: snapshotId });
  } catch (error: any) {
    console.error("Universe snapshot error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    const snapshotType = req.nextUrl.searchParams.get("snapshot_type") as any;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const snapshot = await getLatestSnapshot(userId, snapshotType);

    return NextResponse.json({ snapshot });
  } catch (error: any) {
    console.error("Universe snapshot error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

