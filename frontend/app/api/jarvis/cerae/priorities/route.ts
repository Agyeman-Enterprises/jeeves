import { NextRequest, NextResponse } from "next/server";
import { generateStrategicPriorityMap, getStrategicPriorityMap } from "@/lib/jarvis/cerae/priorities";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { week_start_date } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const priorityMap = await generateStrategicPriorityMap(userId, week_start_date);

    return NextResponse.json({ ok: true, priority_map: priorityMap });
  } catch (error: any) {
    console.error("Strategic priority map error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    const weekStartDate = req.nextUrl.searchParams.get("week_start_date");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const priorityMap = await getStrategicPriorityMap(userId, weekStartDate || undefined);

    if (!priorityMap) {
      // Generate if doesn't exist
      const newMap = await generateStrategicPriorityMap(userId, weekStartDate || undefined);
      return NextResponse.json({ priority_map: newMap });
    }

    return NextResponse.json({ priority_map: priorityMap });
  } catch (error: any) {
    console.error("Strategic priority map error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

