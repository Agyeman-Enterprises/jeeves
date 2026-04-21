// Agents repository - typed wrappers for jarvis_agents table
import { createJarvisDb } from "./index";

export async function createAgent(input: {
  userId: string;
  workspaceId: string;
  name?: string;
  type?: string;
  config?: Record<string, any>;
}) {
  const db = createJarvisDb();
  return db.insert("jarvis_agents", {
    user_id: input.userId,
    workspace_id: input.workspaceId,
  } as any);
}

export async function getAgentById(id: string) {
  const db = createJarvisDb();
  return db.getById("jarvis_agents", id);
}

export async function updateAgentStatus(id: string, status: string) {
  const db = createJarvisDb();
  return db.updateById("jarvis_agents", id, { status } as any);
}

export async function listAgentsForUser(userId: string) {
  const db = createJarvisDb();
  return db.list("jarvis_agents", [{ column: "user_id", value: userId }]);
}

