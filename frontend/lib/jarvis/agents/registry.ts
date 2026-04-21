// Agent registry
import { JarvisAgent } from "./types";
import { basicAgents } from "./basicAgents";

const registry: JarvisAgent[] = [...basicAgents];

export function getRegisteredAgents(): JarvisAgent[] {
  return registry;
}

export function findAgentForIntent(intent: string): JarvisAgent | null {
  // Exact match first
  for (const agent of registry) {
    if (agent.supportedIntents.includes(intent)) {
      return agent;
    }
  }

  // Simple wildcard: "debug.*"
  for (const agent of registry) {
    for (const pattern of agent.supportedIntents) {
      if (pattern.endsWith(".*")) {
        const prefix = pattern.slice(0, -2);
        if (intent.startsWith(prefix)) {
          return agent;
        }
      }
    }
  }

  return null;
}
