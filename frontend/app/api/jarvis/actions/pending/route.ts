import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    // Get pending approvals
    const { data: approvals } = await supabaseServer
      .from("jarvis_action_approvals")
      .select("*")
      .eq("user_id", userId)
      .eq("status", "PENDING")
      .gt("expires_at", new Date().toISOString())
      .order("urgency", { ascending: false })
      .order("created_at", { ascending: true });

    return NextResponse.json({ approvals: approvals || [] });
  } catch (error: any) {
    console.error("Get pending approvals error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

