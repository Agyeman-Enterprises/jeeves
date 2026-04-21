import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import { getEntityFinancials } from "@/lib/nexus/financial/aggregate";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    const { slug } = await params;

    // Get entity by slug
    const { data: entity } = await supabaseServer
      .from("nexus_financial_entities")
      .select("id")
      .eq("slug", slug)
      .single();

    if (!entity) {
      return NextResponse.json({ error: "Entity not found" }, { status: 404 });
    }

    const financials = await getEntityFinancials((entity as any).id);

    if (!financials) {
      return NextResponse.json({ error: "Failed to get entity financials" }, { status: 500 });
    }

    return NextResponse.json(financials);
  } catch (error: any) {
    console.error("Entity financials error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

