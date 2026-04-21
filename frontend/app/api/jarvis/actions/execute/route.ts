import { NextRequest, NextResponse } from "next/server";
import { processAction } from "@/lib/jarvis/actions/broker";
import type { ActionRequest } from "@/lib/jarvis/actions/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const request: ActionRequest = {
      action_type: body.action_type,
      domain: body.domain,
      input: body.input,
      plan_id: body.plan_id,
      agent_run_id: body.agent_run_id,
      urgency: body.urgency,
      context: body.context,
    };

    const agentSlug = body.agent_slug;
    const result = await processAction(userId, request, agentSlug);

    return NextResponse.json(result);
  } catch (error: any) {
    console.error("Action execution error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

