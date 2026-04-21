import { supabaseServer } from "@/lib/supabase/server";
import type { EventSubscription, SubscriberType, EventCategory } from "./types";

export async function subscribeToEvents(
  userId: string,
  subscriberType: SubscriberType,
  subscriberId: string,
  eventTypes?: string[],
  eventCategories?: EventCategory[],
  filters?: Record<string, any>
): Promise<string> {
  const { data, error } = await supabaseServer
    .from("jarvis_event_subscriptions")
    .upsert({
      user_id: userId,
      subscriber_type: subscriberType,
      subscriber_id: subscriberId,
      event_types: eventTypes,
      event_categories: eventCategories,
      filters,
      is_active: true,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "user_id,subscriber_type,subscriber_id",
    })
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(`Failed to create subscription: ${error?.message}`);
  }

  return (data as any).id;
}

export async function unsubscribeFromEvents(
  userId: string,
  subscriberType: SubscriberType,
  subscriberId: string
): Promise<void> {
  await (supabaseServer as any)
    .from("jarvis_event_subscriptions")
    .update({ is_active: false, updated_at: new Date().toISOString() } as any)
    .eq("user_id", userId)
    .eq("subscriber_type", subscriberType)
    .eq("subscriber_id", subscriberId);
}

export async function getSubscriptions(
  userId: string,
  subscriberType?: SubscriberType,
  subscriberId?: string
): Promise<EventSubscription[]> {
  let query = supabaseServer
    .from("jarvis_event_subscriptions")
    .select("*")
    .eq("user_id", userId)
    .eq("is_active", true);

  if (subscriberType) {
    query = query.eq("subscriber_type", subscriberType);
  }

  if (subscriberId) {
    query = query.eq("subscriber_id", subscriberId);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get subscriptions: ${error.message}`);
  }

  return (data || []) as EventSubscription[];
}

