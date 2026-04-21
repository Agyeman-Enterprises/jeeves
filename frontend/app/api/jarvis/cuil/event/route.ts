import { NextRequest, NextResponse } from "next/server";
import { ingestCrossUniverseEvent } from "@/lib/jarvis/cuil/events";
import type { UniverseDomain } from "@/lib/jarvis/cuil/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { event_type, source_domain, payload, source_node_id } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId || !event_type || !source_domain || !payload) {
      return NextResponse.json(
        { error: "Missing required fields: user_id, event_type, source_domain, payload" },
        { status: 400 }
      );
    }

    const eventId = await ingestCrossUniverseEvent(
      userId,
      event_type,
      source_domain as UniverseDomain,
      payload,
      source_node_id
    );

    return NextResponse.json({ ok: true, event_id: eventId });
  } catch (error: any) {
    console.error("Cross-universe event error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

