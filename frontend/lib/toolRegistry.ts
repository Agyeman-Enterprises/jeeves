// lib/toolRegistry.ts

/**
 * Registry of available tools/systems that Jarvis can interact with.
 * Used by JarvisToolsPanel and other components to display connected systems.
 */

export type ToolId = "nexus" | "accessmd" | "purrkoin" | "election-empire" | "medrx";

export type Tool = {
  id: ToolId;
  name: string;
  description: string;
  status: "connected" | "disconnected" | "error";
  category?: "business" | "game" | "healthcare" | "crypto";
};

export const TOOLS: Tool[] = [
  {
    id: "nexus",
    name: "Nexus",
    description: "Business + clinic analytics engine.",
    status: "connected",
    category: "business",
  },
  {
    id: "accessmd",
    name: "AccessMD",
    description: "Telehealth + GLP operations.",
    status: "connected",
    category: "healthcare",
  },
  {
    id: "purrkoin",
    name: "Purrkoin",
    description: "Crypto + economy control panel.",
    status: "connected",
    category: "crypto",
  },
  {
    id: "election-empire",
    name: "Election Empire",
    description: "Game-world orchestration layer.",
    status: "connected",
    category: "game",
  },
  {
    id: "medrx",
    name: "MedRx",
    description: "Medical practice management system.",
    status: "connected",
    category: "healthcare",
  },
];

/**
 * Get a tool by its ID.
 */
export function getTool(id: ToolId): Tool | undefined {
  return TOOLS.find((tool) => tool.id === id);
}

/**
 * Get all tools in a specific category.
 */
export function getToolsByCategory(category: Tool["category"]): Tool[] {
  return TOOLS.filter((tool) => tool.category === category);
}

/**
 * Get all connected tools.
 */
export function getConnectedTools(): Tool[] {
  return TOOLS.filter((tool) => tool.status === "connected");
}

