import { NextRequest, NextResponse } from "next/server";
import { logDecision } from "@/lib/jarvis/behavior/observer";
import type { DecisionLog } from "@/lib/jarvis/behavior/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      user_id,
      decision_type,
      context_type,
      context_id,
      original_input,
      user_action,
      user_feedback,
      model_affected,
    } = body;

    if (!user_id || !decision_type || !context_type) {
      return NextResponse.json(
        { error: "Missing required fields: user_id, decision_type, context_type" },
        { status: 400 }
      );
    }

    const log: DecisionLog = {
      user_id,
      decision_type,
      context_type,
      context_id,
      original_input,
      user_action,
      user_feedback,
      model_affected,
    };

    await logDecision(log);

    return NextResponse.json({ ok: true, message: "Decision logged" });
  } catch (error: any) {
    console.error("Log decision error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

