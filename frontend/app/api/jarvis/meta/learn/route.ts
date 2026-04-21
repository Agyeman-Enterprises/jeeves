import { NextRequest, NextResponse } from "next/server";
import { runMetaLearningCycle } from "@/lib/jarvis/meta/engine";

export async function POST(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const insights = await runMetaLearningCycle(userId);

    return NextResponse.json({ ok: true, insights, count: insights.length });
  } catch (error: any) {
    console.error("Meta-learning error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

