import { supabaseServer } from "@/lib/supabase/server";
import type { Simulation, SimulationType } from "./types";
import { simulateClinical } from "./clinical";
import { simulateFinancial } from "./financial";
import { simulateOperational } from "./operational";
import { simulateRisk } from "./risk";
import { simulateAgentLoad } from "./agent";
import { simulateStrategic } from "./strategic";

export async function runSimulation(
  userId: string,
  simulationType: SimulationType,
  simulationName: string,
  inputParameters: Record<string, any>,
  scenarioDescription?: string
): Promise<Simulation> {
  // Create simulation record
  const { data: simData, error: simError } = await supabaseServer
    .from("jarvis_simulations")
    .insert({
      user_id: userId,
      simulation_type: simulationType,
      simulation_name: simulationName,
      scenario_description: scenarioDescription,
      input_parameters: inputParameters,
      status: "RUNNING",
      started_at: new Date().toISOString(),
    } as any)
    .select("id")
    .single();

  if (simError || !simData) {
    throw new Error(`Failed to create simulation: ${simError?.message}`);
  }

  const simulationId = (simData as any).id;

  try {
    // Route to appropriate simulator
    let outputResults: Record<string, any>;

    switch (simulationType) {
      case "CLINICAL":
        outputResults = await simulateClinical(userId, inputParameters);
        break;
      case "FINANCIAL":
        outputResults = await simulateFinancial(userId, inputParameters);
        break;
      case "OPERATIONAL":
        outputResults = await simulateOperational(userId, inputParameters);
        break;
      case "RISK":
        outputResults = await simulateRisk(userId, inputParameters);
        break;
      case "AGENT":
        outputResults = await simulateAgentLoad(userId, inputParameters);
        break;
      case "STRATEGIC":
        outputResults = await simulateStrategic(userId, inputParameters);
        break;
      default:
        throw new Error(`Unknown simulation type: ${simulationType}`);
    }

    // Update simulation with results
    const updateData: Record<string, any> = {
      output_results: outputResults,
      status: "COMPLETED",
      completed_at: new Date().toISOString(),
    };
    await (supabaseServer as any)
      .from("jarvis_simulations")
      .update(updateData)
      .eq("id", simulationId);

    return {
      id: simulationId,
      user_id: userId,
      simulation_type: simulationType,
      simulation_name: simulationName,
      scenario_description: scenarioDescription,
      input_parameters: inputParameters,
      output_results: outputResults,
      status: "COMPLETED",
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    };
  } catch (error: any) {
    // Mark simulation as failed
    const updateData: Record<string, any> = {
      status: "FAILED",
      output_results: { error: error.message },
      completed_at: new Date().toISOString(),
    };
    await (supabaseServer as any)
      .from("jarvis_simulations")
      .update(updateData)
      .eq("id", simulationId);

    throw error;
  }
}

export async function getSimulation(simulationId: string): Promise<Simulation | null> {
  const { data, error } = await supabaseServer
    .from("jarvis_simulations")
    .select("*")
    .eq("id", simulationId)
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      return null;
    }
    throw new Error(`Failed to get simulation: ${error.message}`);
  }

  return data as Simulation;
}

export async function getSimulations(
  userId: string,
  simulationType?: SimulationType,
  limit: number = 50
): Promise<Simulation[]> {
  let query = supabaseServer
    .from("jarvis_simulations")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (simulationType) {
    query = query.eq("simulation_type", simulationType);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to get simulations: ${error.message}`);
  }

  return (data || []) as Simulation[];
}

