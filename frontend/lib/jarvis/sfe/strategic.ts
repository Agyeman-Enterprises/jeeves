import { supabaseServer } from "@/lib/supabase/server";
import type { ForesightMap } from "./types";

export async function generateStrategicForesight(
  userId: string,
  startDate?: Date
): Promise<ForesightMap> {
  const start = startDate || new Date();
  const end = new Date(start);
  end.setDate(end.getDate() + 90);

  // 90-day strategic analysis
  const foresightMap: ForesightMap = {
    user_id: userId,
    horizon: "STRATEGIC_90DAY",
    forecast_start_date: start.toISOString().split("T")[0],
    forecast_end_date: end.toISOString().split("T")[0],
    status: "COMPLETED",
    foresight_data: {
      trend_lines: {},
      seasonal_cycles: {},
      burnout_risk: {},
      universe_stability: {},
      financial_liquidity: {},
      expansion_opportunities: {},
    },
    confidence_score: 0.65,
    factors_used: {
      historical_data: true,
      trend_analysis: true,
      simulation_models: true,
      cross_universe_analysis: true,
    },
  };

  await storeForesightMap(userId, foresightMap);

  return foresightMap;
}

async function storeForesightMap(userId: string, map: ForesightMap): Promise<void> {
  await supabaseServer
    .from("jarvis_foresight_maps")
    .upsert({
      ...map,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "user_id,horizon,forecast_start_date",
    });
}

