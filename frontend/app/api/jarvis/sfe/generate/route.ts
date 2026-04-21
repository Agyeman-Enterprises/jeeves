import { NextRequest, NextResponse } from "next/server";
import { generateForesight, generateAllForesight } from "@/lib/jarvis/sfe/engine";
import type { ForesightHorizon } from "@/lib/jarvis/sfe/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { horizon, start_date, all } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    if (all) {
      // Generate all horizons
      const allForesight = await generateAllForesight(userId);
      return NextResponse.json({ ok: true, foresight: allForesight });
    }

    if (!horizon) {
      return NextResponse.json(
        { error: "Missing horizon (or set all=true)" },
        { status: 400 }
      );
    }

    const startDate = start_date ? new Date(start_date) : undefined;
    const foresight = await generateForesight(userId, horizon as ForesightHorizon, startDate);

    return NextResponse.json({ ok: true, foresight });
  } catch (error: any) {
    console.error("Foresight generation error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

