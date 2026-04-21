import { NextRequest, NextResponse } from "next/server";
import { generateGraphStatistics, getGraphStatistics } from "@/lib/jarvis/umg/statistics";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { snapshot_date } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const statistics = await generateGraphStatistics(userId, snapshot_date);

    return NextResponse.json({ ok: true, statistics });
  } catch (error: any) {
    console.error("UMG statistics error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    const snapshotDate = req.nextUrl.searchParams.get("snapshot_date");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const statistics = await getGraphStatistics(userId, snapshotDate || undefined);

    if (!statistics) {
      // Generate if doesn't exist
      const newStats = await generateGraphStatistics(userId, snapshotDate || undefined);
      return NextResponse.json({ statistics: newStats });
    }

    return NextResponse.json({ statistics });
  } catch (error: any) {
    console.error("UMG statistics error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

