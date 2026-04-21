import { NextRequest, NextResponse } from "next/server";
import { selectPersona } from "@/lib/jarvis/persona/selector";
import type { PersonaContext } from "@/lib/jarvis/persona/types";

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

    const selection = await selectPersona(user_id, context as PersonaContext);

    return NextResponse.json(selection);
  } catch (error: any) {
    console.error("Select persona error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

