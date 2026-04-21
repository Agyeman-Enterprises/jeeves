import { NextRequest, NextResponse } from "next/server";
import { getCurrentMode, transitionMode, determineOptimalMode } from "@/lib/jarvis/copilot/modes";
import type { AutonomyMode, ModeTransitionTrigger } from "@/lib/jarvis/copilot/types";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const currentMode = await getCurrentMode(userId);
    const optimalMode = await determineOptimalMode(userId);

    return NextResponse.json({
      current_mode: currentMode,
      optimal_mode: optimalMode,
      should_transition: currentMode !== optimalMode,
    });
  } catch (error: any) {
    console.error("Get mode error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { mode, reason, triggered_by, context } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId || !mode) {
      return NextResponse.json(
        { error: "Missing user_id or mode" },
        { status: 400 }
      );
    }

    await transitionMode(
      userId,
      mode as AutonomyMode,
      reason || "Manual mode transition",
      (triggered_by as ModeTransitionTrigger) || "USER",
      context
    );

    return NextResponse.json({ ok: true, mode });
  } catch (error: any) {
    console.error("Mode transition error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

