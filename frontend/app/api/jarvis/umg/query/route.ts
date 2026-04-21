import { NextRequest, NextResponse } from "next/server";
import { queryGraph } from "@/lib/jarvis/umg/traversal";
import type { QueryType } from "@/lib/jarvis/umg/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { query_pattern, query_type } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId || !query_pattern || !query_type) {
      return NextResponse.json(
        { error: "Missing required fields: user_id, query_pattern, query_type" },
        { status: 400 }
      );
    }

    const result = await queryGraph(userId, query_pattern, query_type as QueryType);

    return NextResponse.json({ ok: true, result });
  } catch (error: any) {
    console.error("UMG query error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

