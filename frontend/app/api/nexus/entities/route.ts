// Nexus entities API (read-only)
import { NextResponse } from "next/server";
import { listFinancialEntities } from "@/lib/nexus/entities";

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

    const entities = await listFinancialEntities({ userId, workspaceId });
    return NextResponse.json({ entities });
  } catch (err) {
    console.error(err);
    return NextResponse.json(
      { error: "Internal error", details: String(err) },
      { status: 500 }
    );
  }
}

