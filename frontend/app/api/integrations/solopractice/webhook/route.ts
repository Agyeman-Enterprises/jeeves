import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // TODO: Validate webhook signature
    // const signature = req.headers.get("x-solopractice-signature");

    const { data, error } = await supabaseServer
      .from("jarvis_system_events")
      .insert({
        source: "solopractice",
        type: body.event_type,
        patient_id: body.patient_id || null,
        user_id: body.user_id,
        payload: body,
        status: "NEW",
      } as any)
      .select()
      .single();

    if (error || !data) {
      console.error("Solopractice webhook error:", error);
      return NextResponse.json({ error: "Failed to process webhook" }, { status: 500 });
    }

    return NextResponse.json({ ok: true, event_id: (data as any).id });
  } catch (error: any) {
    console.error("Solopractice webhook error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

