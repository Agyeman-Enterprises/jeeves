// lib/api/jarvisTypes.ts

export type JarvisCommandPayload = {
  command: string;          // e.g. "daily-summary", "route-query"
  message?: string;         // raw natural language from you
  workspace?: string;       // "ops" | "system" | "creative" | "financial" | "playground"
  metadata?: Record<string, any>;
};

export type JarvisSignal = {
  id?: string;
  time: string;
  source: string;
  level: "info" | "warning" | "error";
  text: string;
  data?: any;
};

export type JarvisTask = {
  id?: string;
  title: string;
  status: "pending" | "active" | "done" | "blocked";
  priority?: number;
  type?: string;
  due_at?: string | null;
};

export type JarvisJournalEntry = {
  id?: string;
  title: string;
  body: string;
  tags?: string[];
  mood?: string | null;
  created_at?: string;
};

export type JarvisMemoryOp = {
  op: "add" | "update" | "delete";
  id?: string;
  text?: string;
  importance?: "low" | "normal" | "high";
  scope?: "short" | "long";
};

export type JarvisBackendResponse = {
  reply: string;
  tasks?: JarvisTask[];
  signals?: JarvisSignal[];
  journal_entry?: JarvisJournalEntry | null;
  memory_ops?: JarvisMemoryOp[];
  meta?: Record<string, any>;
};

