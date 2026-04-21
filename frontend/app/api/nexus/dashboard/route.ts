// Nexus dashboard API (read-only)
import { NextResponse } from "next/server";
import { getNexusDashboardSummary } from "@/lib/nexus/financial/aggregate";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const userId = searchParams.get("userId");
    const workspaceId = searchParams.get("workspaceId");

    if (!userId || !workspaceId) {
      return NextResponse.json(
        { error: "Missing userId or workspaceId" },
        { status: 400 }
      );
    }

    const summary = await getNexusDashboardSummary({ userId, workspaceId });
    return NextResponse.json(summary);
  } catch (err) {
    console.error(err);
    return NextResponse.json(
      { error: "Internal error", details: String(err) },
      { status: 500 }
    );
  }
}

