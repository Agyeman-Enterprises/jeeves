import { NextRequest, NextResponse } from "next/server";
import { getFinancialOverview } from "@/lib/nexus/financial/aggregate";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    
    if (!userId) {
      return NextResponse.json({ error: "Missing user_id" }, { status: 400 });
    }

    const overview = await getFinancialOverview(userId);

    if (!overview) {
      return NextResponse.json({ error: "Failed to get financial overview" }, { status: 500 });
    }

    return NextResponse.json(overview);
  } catch (error: any) {
    console.error("Financial overview error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

