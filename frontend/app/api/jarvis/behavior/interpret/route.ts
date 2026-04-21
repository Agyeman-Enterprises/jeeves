import { NextRequest, NextResponse } from "next/server";
import { interpretBehavior } from "@/lib/jarvis/behavior/interpreter";

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

    const interpretation = await interpretBehavior(user_id, context);

    return NextResponse.json(interpretation);
  } catch (error: any) {
    console.error("Interpret behavior error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

