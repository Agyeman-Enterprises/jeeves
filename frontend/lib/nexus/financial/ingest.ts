import { supabaseServer } from "@/lib/supabase/server";
import type { FinancialEvent } from "@/lib/jarvis/events/types";

export async function ingestFinancialTransaction(event: FinancialEvent) {
  // Normalize and insert into financial_transactions
  if (!event.entity_id) {
    console.warn("Financial event missing entity_id:", event);
    return null;
  }

  const { data, error } = await supabaseServer
    .from("nexus_financial_transactions")
    .insert({
      entity_id: event.entity_id,
      user_id: event.user_id,
      source: event.source,
      external_id: event.payload.external_id || event.payload.id,
      occurred_at: event.payload.occurred_at || new Date().toISOString(),
      amount: event.amount || event.payload.amount,
      currency: event.currency || event.payload.currency || "USD",
      direction: event.payload.direction || (event.amount && event.amount >= 0 ? "INCOME" : "EXPENSE"),
      category: event.category || event.payload.category,
      description: event.payload.description,
      meta: event.payload,
    } as any)
    .select()
    .single();

  if (error) {
    console.error("Failed to ingest financial transaction:", error);
    return null;
  }

  return data;
}

export async function ingestTaxPosition(event: FinancialEvent) {
  const { data, error } = await supabaseServer
    .from("nexus_tax_positions")
    .upsert({
      user_id: event.user_id,
      entity_id: event.entity_id || null,
      tax_year: event.payload.tax_year || new Date().getFullYear(),
      estimated_tax: event.payload.estimated_tax,
      paid_tax: event.payload.paid_tax || 0,
      due_tax: event.payload.due_tax || event.payload.estimated_tax,
      meta: event.payload,
    } as any, {
      onConflict: "user_id,entity_id,tax_year",
    })
    .select()
    .single();

  if (error) {
    console.error("Failed to ingest tax position:", error);
    return null;
  }

  return data;
}

export async function ingestFinancialSnapshot(event: FinancialEvent) {
  if (!event.entity_id) {
    console.warn("Financial snapshot missing entity_id:", event);
    return null;
  }

  const { data, error } = await supabaseServer
    .from("nexus_financial_snapshots")
    .insert({
      entity_id: event.entity_id,
      as_of_date: event.payload.as_of_date || new Date().toISOString().split("T")[0],
      revenue: event.payload.revenue,
      expenses: event.payload.expenses,
      profit: event.payload.profit,
      cash_balance: event.payload.cash_balance,
      tax_estimate: event.payload.tax_estimate,
      meta: event.payload,
    } as any)
    .select()
    .single();

  if (error) {
    console.error("Failed to ingest financial snapshot:", error);
    return null;
  }

  return data;
}

