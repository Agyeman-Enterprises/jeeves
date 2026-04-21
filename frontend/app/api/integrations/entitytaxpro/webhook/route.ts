import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // TODO: Validate webhook signature

    // Insert into financial_transactions if it's a transaction
    if (body.type === "TXN_RECORDED" || body.type === "EXPENSE_RECORDED" || body.type === "INCOME_RECORDED") {
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
            source: "entitytaxpro",
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

    // Insert into financial_snapshots if it's a period close
    if (body.type === "PERIOD_CLOSE" || body.type === "ENTITY_BALANCE_UPDATED") {
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
          .from("nexus_financial_snapshots")
          .insert({
            entity_id: entityId,
            as_of_date: body.as_of_date || new Date().toISOString().split("T")[0],
            revenue: body.revenue,
            expenses: body.expenses,
            profit: body.profit,
            cash_balance: body.cash_balance,
            tax_estimate: body.tax_estimate,
            meta: body.meta || {},
          } as any);
      }
    }

    // Insert into system_events
    const { data, error } = await supabaseServer
      .from("jarvis_system_events")
      .insert({
        source: "entitytaxpro",
        type: body.event_type || body.type,
        entity_id: body.entity_id || null,
        user_id: body.user_id,
        payload: body,
        status: "NEW",
      } as any)
      .select()
      .single();

    if (error) {
      console.error("EntityTaxPro webhook error:", error);
      return NextResponse.json({ error: "Failed to process webhook" }, { status: 500 });
    }

    return NextResponse.json({ ok: true, event_id: (data as any)?.id });
  } catch (error: any) {
    console.error("EntityTaxPro webhook error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

