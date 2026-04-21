import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database, NexusTable } from "@/lib/supabase/types";
import { getSupabaseClient } from "@/lib/supabase/client";

type NexusRow<T extends NexusTable> = Database["public"]["Tables"][T]["Row"];
type NexusInsert<T extends NexusTable> = Database["public"]["Tables"][T]["Insert"];
type NexusUpdate<T extends NexusTable> = Database["public"]["Tables"][T]["Update"];

export class NexusDb {
  private client: SupabaseClient<Database>;

  constructor(client: SupabaseClient<Database>) {
    this.client = client;
  }

  async getById<T extends NexusTable>(table: T, id: string): Promise<NexusRow<T> | null> {
    const client = this.client as any;
    const { data, error } = await client
      .from(table)
      .select("*")
      .eq("id", id)
      .maybeSingle();

    if (error) throw error;
    return (data ?? null) as NexusRow<T> | null;
  }

  async insert<T extends NexusTable>(table: T, payload: NexusInsert<T>): Promise<NexusRow<T>> {
    const client = this.client as any;
    const { data, error } = await client
      .from(table)
      .insert(payload)
      .select()
      .single();

    if (error) throw error;
    if (!data) throw new Error("Insert returned no data");
    return data as NexusRow<T>;
  }

  async updateById<T extends NexusTable>(
    table: T,
    id: string,
    patch: NexusUpdate<T>
  ): Promise<NexusRow<T> | null> {
    const client = this.client as any;
    const { data, error } = await client
      .from(table)
      .update(patch)
      .eq("id", id)
      .select()
      .maybeSingle();

    if (error) throw error;
    return (data ?? null) as NexusRow<T> | null;
  }

  async list<T extends NexusTable>(
    table: T,
    filters?: { column: string; value: string | number | boolean }[],
    limit = 100
  ): Promise<NexusRow<T>[]> {
    const client = this.client as any;
    let query = client.from(table).select("*").limit(limit);

    if (filters) {
      for (const f of filters) {
        query = query.eq(f.column, f.value);
      }
    }

    const { data, error } = await query;
    if (error) throw error;
    return (data ?? []) as NexusRow<T>[];
  }
}

export function createNexusDb() {
  const client = getSupabaseClient();
  return new NexusDb(client);
}
