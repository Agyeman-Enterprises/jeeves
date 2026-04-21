// Core enums & types shared across the Jarvis brain

export type JarvisTaskKind =
  | "QUESTION"
  | "ACTION"
  | "SCHEDULE"
  | "FILE_OP"
  | "EMAIL"
  | "ANALYTICS"
  | "UNKNOWN";

export type JarvisChannel = "chat" | "system" | "tool";

export interface JarvisUserIdentity {
  userId: string;              // Supabase auth user id
  workspaceId?: string | null; // Optional: current workspace / org
}

export interface JarvisMessage {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  channel?: JarvisChannel;
  timestamp?: string; // ISO
  meta?: Record<string, any>;
}

export interface JarvisCommandInput {
  user: JarvisUserIdentity;
  query: string;
  messages?: JarvisMessage[];  // short conversation context
  workspaceContext?: {
    app: "jarvis" | "nexus" | "other";
    location?: string; // e.g. "dashboard", "analytics", "email"
    resourceId?: string; // e.g. file id, thread id
  } | null;
}

export interface JarvisTaskClassification {
  kind: JarvisTaskKind;
  confidence: number; // 0–1
  reason: string;
  tags: string[];
}

export type JarvisToolName =
  | "memory.read"
  | "memory.write"
  | "journal.append"
  | "timeline.log"
  | "analytics.summary"
  | "email.draft"
  | "schedule.create"
  | "file.list"
  | "file.read"
  | "file.write"
  | "summarize"
  | "none";

export interface JarvisRoutedTask {
  tool: JarvisToolName;
  classification: JarvisTaskClassification;
  // Optional payload the router passes to the tool
  payload?: Record<string, any>;
}

export interface JarvisToolResult {
  ok: boolean;
  tool: JarvisToolName;
  data?: any;
  error?: string;
}

export interface JarvisResponse {
  messages: JarvisMessage[];
  classification: JarvisTaskClassification;
  routedTask?: JarvisRoutedTask;
  toolResult?: JarvisToolResult;
  journalEntryId?: string | null;
  timelineEventId?: string | null;
}

export interface JarvisToolContext extends JarvisCommandInput {
  routedTask: JarvisRoutedTask;
}

export interface JarvisToolDefinition {
  name: JarvisToolName;
  description: string;
  run: (ctx: JarvisToolContext) => Promise<JarvisToolResult>;
}

