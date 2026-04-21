export type LLMRole = "system" | "user" | "assistant";

export interface LLMMessage {
  role: LLMRole;
  content: string;
}

export interface LLMCallArgs {
  messages: LLMMessage[];
  purpose?: string; // "classification" | "rewrite" | "answer" | ...
  temperature?: number;
  maxTokens?: number;
}

export interface LLMCallResult {
  provider: "local" | "openai";
  model: string;
  content: string;
  raw?: any;
}

