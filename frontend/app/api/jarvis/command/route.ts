// Jarvis command API endpoint
import { NextRequest, NextResponse } from "next/server";
import { routeJarvisCommand } from "@/lib/jarvis/router/route";
// Import handlers to register them
import "@/lib/jarvis/events/gem/handlers";

export interface JarvisCommandRequest {
  text: string;
  userId: string;
  workspaceId: string;
}

/**
 * POST /api/jarvis/command
 * Main entry point for Jarvis commands
 */
export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as JarvisCommandRequest;
    const { text, userId, workspaceId } = body;

    if (!text) {
      return NextResponse.json(
        { error: "Missing text" },
        { status: 400 }
      );
    }

    if (!userId) {
      return NextResponse.json(
        { error: "Missing userId" },
        { status: 400 }
      );
    }

    if (!workspaceId) {
      return NextResponse.json(
        { error: "Missing workspaceId" },
        { status: 400 }
      );
    }

    const result = await routeJarvisCommand({
      text,
      userId,
      workspaceId,
    });

    return NextResponse.json(result);
  } catch (err) {
    console.error("[JarvisCommand] Error:", err);
    return NextResponse.json(
      {
        error: "Internal error",
        details: err instanceof Error ? err.message : String(err),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/jarvis/command
 * Health check endpoint
 */
export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "jarvis-command",
    timestamp: new Date().toISOString(),
  });
}
