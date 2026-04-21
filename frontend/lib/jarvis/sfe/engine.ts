import type { ForesightMap, ForesightHorizon } from "./types";
import { generateTacticalForesight } from "./tactical";
import { generateOperationalForesight } from "./operational";
import { generateStrategicForesight } from "./strategic";
import { generateEnterpriseForesight } from "./enterprise";

export async function generateForesight(
  userId: string,
  horizon: ForesightHorizon,
  startDate?: Date
): Promise<ForesightMap> {
  switch (horizon) {
    case "TACTICAL_10DAY":
      return await generateTacticalForesight(userId, startDate);
    case "OPERATIONAL_30DAY":
      return await generateOperationalForesight(userId, startDate);
    case "STRATEGIC_90DAY":
      return await generateStrategicForesight(userId, startDate);
    case "ENTERPRISE_1YEAR":
      return await generateEnterpriseForesight(userId, startDate);
    default:
      throw new Error(`Unknown horizon: ${horizon}`);
  }
}

export async function generateAllForesight(userId: string): Promise<Record<ForesightHorizon, ForesightMap>> {
  const [tactical, operational, strategic, enterprise] = await Promise.all([
    generateTacticalForesight(userId),
    generateOperationalForesight(userId),
    generateStrategicForesight(userId),
    generateEnterpriseForesight(userId),
  ]);

  return {
    TACTICAL_10DAY: tactical,
    OPERATIONAL_30DAY: operational,
    STRATEGIC_90DAY: strategic,
    ENTERPRISE_1YEAR: enterprise,
  };
}

