// JJ timeline — reads jeeves_signals from JJ Supabase (tzjygaxpzrtevlnganjs)
// Cloud is primary authority.
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const { supabaseServer: supabase } = await import("@/lib/supabase/server");
    const { data, error } = await supabase
      .from("jeeves_signals")
      .select("id,signal_type,source,content,metadata,created_at")
      .order("created_at", { ascending: false })
      .limit(30);
    if (error) throw error;
    return NextResponse.json(data ?? []);
  } catch (error) {
    console.error("[Timeline] error:", error);
    return NextResponse.json([]);
  }
}

