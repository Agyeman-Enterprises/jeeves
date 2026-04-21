import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // TODO: Validate webhook signature

    // Insert into financial_transactions if it's a transaction
    if (body.type === "TXN_RECORDED" || body.type === "EXPENSE_RECORDED" || body.type === "INCOME_RECORDED") {
      // First, get or create entity
      let entityId = body.entity_id;
      if (body.entity_slug && !entityId) {
        const { data: entity } = await supabaseServer
          .from("nexus_financial_entities")
          .select("id")
          .eq("slug", body.entity_slug)
          .single();
        
        if (entity) {
          entityId = (entity as any).id;
        }
      }

      if (entityId) {
        await supabaseServer
          .from("nexus_financial_transactions")
          .insert({
            entity_id: entityId,
            user_id: body.user_id,
            source: "taxrx",
            external_id: body.external_id || body.id,
            occurred_at: body.occurred_at || new Date().toISOString(),
            amount: body.amount,
            currency: body.currency || "USD",
            direction: body.direction || (body.amount >= 0 ? "INCOME" : "EXPENSE"),
            category: body.category,
            description: body.description,
            meta: body.meta || {},
          } as any);
      }
    }

    // Insert into tax_positions if it's a tax update
    if (body.type === "TAX_ESTIMATE_UPDATED") {
      await supabaseServer
        .from("nexus_tax_positions")
        .upsert({
          user_id: body.user_id,
          entity_id: body.entity_id || null,
          tax_year: body.tax_year || new Date().getFullYear(),
          estimated_tax: body.estimated_tax,
          paid_tax: body.paid_tax || 0,
          due_tax: body.due_tax || body.estimated_tax,
          meta: body.meta || {},
        } as any, {
          onConflict: "user_id,entity_id,tax_year",
        });
    }

    // Insert into system_events
    const { data, error } = await supabaseServer
      .from("jarvis_system_events")
      .insert({
        source: "taxrx",
        type: body.event_type || body.type,
        entity_id: body.entity_id || null,
        user_id: body.user_id,
        payload: body,
        status: "NEW",
      } as any)
      .select()
      .single();

    if (error) {
      console.error("TaxRx webhook error:", error);
      return NextResponse.json({ error: "Failed to process webhook" }, { status: 500 });
    }

    return NextResponse.json({ ok: true, event_id: (data as any)?.id });
  } catch (error: any) {
    console.error("TaxRx webhook error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

