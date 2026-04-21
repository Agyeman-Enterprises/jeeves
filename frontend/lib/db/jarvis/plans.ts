// Plans repository - typed wrappers for jarvis_plans and jarvis_plan_steps tables
import { createJarvisDb } from "./index";

export async function createPlan(input: {
  userId: string;
  workspaceId?: string;
  source?: string;
  sourceRef?: string;
  title?: string;
  status?: string;
}) {
  const db = createJarvisDb();
  return db.insert("jarvis_plans", {
    user_id: input.userId,
    workspace_id: input.workspaceId || null,
  } as any);
}

export async function getPlanById(id: string) {
  const db = createJarvisDb();
  return db.getById("jarvis_plans", id);
}

export async function listPlansForUser(userId: string) {
  const db = createJarvisDb();
  return db.list("jarvis_plans", [{ column: "user_id", value: userId }]);
}

export async function createPlanStep(input: {
  planId: string;
  userId: string;
  workspaceId?: string;
  orderIndex: number;
  type: string;
  tool?: string;
  agentSlug?: string;
  status?: string;
}) {
  const db = createJarvisDb();
  return db.insert("jarvis_plan_steps", {
    user_id: input.userId,
    workspace_id: input.workspaceId || null,
  } as any);
}

export async function getPlanStepById(id: string) {
  const db = createJarvisDb();
  return db.getById("jarvis_plan_steps", id);
}

