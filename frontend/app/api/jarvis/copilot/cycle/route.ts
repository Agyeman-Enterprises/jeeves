import { NextRequest, NextResponse } from "next/server";
import { executeCoPilotCycle } from "@/lib/jarvis/copilot/orchestrator";

export async function POST(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const result = await executeCoPilotCycle(userId);

    return NextResponse.json({ ok: true, ...result });
  } catch (error: any) {
    console.error("Co-pilot cycle error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

