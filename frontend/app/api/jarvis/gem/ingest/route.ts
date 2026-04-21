import { NextRequest, NextResponse } from "next/server";
import { ingestEvent } from "@/lib/jarvis/gem/router";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { event_type, source, payload, source_id } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId || !event_type || !source || !payload) {
      return NextResponse.json(
        { error: "Missing required fields: user_id, event_type, source, payload" },
        { status: 400 }
      );
    }

    const eventId = await ingestEvent(userId, event_type, source, payload, source_id);

    return NextResponse.json({ ok: true, event_id: eventId });
  } catch (error: any) {
    console.error("GEM ingest error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

