import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database, JarvisTable } from "@/lib/supabase/types";
import { getSupabaseClient } from "@/lib/supabase/client";

type JarvisRow<T extends JarvisTable> = Database["public"]["Tables"][T]["Row"];
type JarvisInsert<T extends JarvisTable> = Database["public"]["Tables"][T]["Insert"];
type JarvisUpdate<T extends JarvisTable> = Database["public"]["Tables"][T]["Update"];

export class JarvisDb {
  private client: SupabaseClient<Database>;

  constructor(client: SupabaseClient<Database>) {
    this.client = client;
  }

  async getById<T extends JarvisTable>(table: T, id: string): Promise<JarvisRow<T> | null> {
    const client = this.client as any;
    const { data, error } = await client
      .from(table)
      .select("*")
      .eq("id", id)
      .maybeSingle();

    if (error) throw error;
    return (data ?? null) as JarvisRow<T> | null;
  }

  async insert<T extends JarvisTable>(table: T, payload: JarvisInsert<T>): Promise<JarvisRow<T>> {
    const client = this.client as any;
    const { data, error } = await client
      .from(table)
      .insert(payload)
      .select()
      .single();

    if (error) throw error;
    if (!data) throw new Error("Insert returned no data");
    return data as JarvisRow<T>;
  }

  async updateById<T extends JarvisTable>(
    table: T,
    id: string,
    patch: JarvisUpdate<T>
  ): Promise<JarvisRow<T> | null> {
    const client = this.client as any;
    const { data, error } = await client
      .from(table)
      .update(patch)
      .eq("id", id)
      .select()
      .maybeSingle();

    if (error) throw error;
    return (data ?? null) as JarvisRow<T> | null;
  }

  async list<T extends JarvisTable>(
    table: T,
    filters?: { column: string; value: string | number | boolean }[],
    limit = 100
  ): Promise<JarvisRow<T>[]> {
    const client = this.client as any;
    let query = client.from(table).select("*").limit(limit);

    if (filters) {
      for (const f of filters) {
        query = query.eq(f.column, f.value);
      }
    }

    const { data, error } = await query;
    if (error) throw error;
    return (data ?? []) as JarvisRow<T>[];
  }
}

export function createJarvisDb() {
  const client = getSupabaseClient();
  return new JarvisDb(client);
}
