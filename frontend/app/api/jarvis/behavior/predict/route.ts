import { NextRequest, NextResponse } from "next/server";
import { predictDecision } from "@/lib/jarvis/behavior/interpreter";
import type { ContextType } from "@/lib/jarvis/behavior/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { user_id, context } = body;

    if (!user_id || !context) {
      return NextResponse.json(
        { error: "Missing required fields: user_id, context" },
        { status: 400 }
      );
    }

    const prediction = await predictDecision(user_id, {
      type: context.type as ContextType,
      data: context.data || {},
    });

    return NextResponse.json(prediction);
  } catch (error: any) {
    console.error("Predict decision error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

