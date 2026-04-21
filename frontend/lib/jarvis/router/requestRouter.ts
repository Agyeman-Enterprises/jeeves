// Request router - routes classified tasks to appropriate handlers
import type { TaskClassification } from "../classifier/taskClassifier";
import type { RewrittenQuery } from "./queryRewriter";

export interface RoutedRequest {
  classification: TaskClassification;
  rewrittenQuery: RewrittenQuery;
  handler: string;
  priority: "low" | "medium" | "high" | "urgent";
}

/**
 * Route a classified and rewritten request to the appropriate handler
 */
export function routeRequest(
  classification: TaskClassification,
  rewrittenQuery: RewrittenQuery
): RoutedRequest {
  // Determine priority based on intent
  const priority = determinePriority(classification.intent);
  
  // Determine handler based on intent
  const handler = determineHandler(classification.intent, classification.suggestedAgent);

  return {
    classification,
    rewrittenQuery,
    handler,
    priority,
  };
}

/**
 * Determine priority based on intent
 */
function determinePriority(intent: string): RoutedRequest["priority"] {
  // Urgent intents
  if (intent.startsWith("clinical.") && intent.includes("action")) {
    return "urgent";
  }

  // High priority intents
  if (
    intent.startsWith("email.send") ||
    intent.startsWith("plan.execute") ||
    intent.startsWith("agent.run")
  ) {
    return "high";
  }

  // Medium priority intents
  if (
    intent.startsWith("memory.") ||
    intent.startsWith("journal.") ||
    intent.startsWith("timeline.") ||
    intent.startsWith("schedule.")
  ) {
    return "medium";
  }

  // Low priority intents
  return "low";
}

/**
 * Determine handler based on intent and suggested agent
 */
function determineHandler(intent: string, suggestedAgent?: string): string {
  // Use suggested agent if provided
  if (suggestedAgent) {
    return `agent:${suggestedAgent}`;
  }

  // Map intents to handlers
  const handlerMap: Record<string, string> = {
    "email.send": "tool:email_send",
    "email.summarize": "tool:email_summarize",
    "email.triage": "agent:email_agent",
    "analytics.query": "tool:analytics_query",
    "memory.add": "tool:memory_add",
    "memory.recall": "tool:memory_recall",
    "journal.create": "tool:journal_create",
    "timeline.add": "tool:timeline_add",
    "plan.create": "tool:plan_create",
    "plan.execute": "agent:planner_agent",
    "agent.run": "system:agent_runner",
    "agent.status": "system:agent_status",
    "clinical.action": "agent:clinical_agent",
    "clinical.query": "tool:clinical_query",
    "financial.action": "agent:nexus_agent",
    "financial.query": "tool:financial_query",
    "file.organize": "tool:file_organize",
    "file.search": "tool:file_search",
    "schedule.create": "tool:schedule_create",
    "schedule.query": "tool:schedule_query",
    "unknown": "system:fallback",
  };

  return handlerMap[intent] || "system:fallback";
}

