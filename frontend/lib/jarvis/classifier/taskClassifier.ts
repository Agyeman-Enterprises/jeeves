// Task classifier - maps user queries to high-level intents
import { llm } from "../utils/llm";

export interface TaskClassification {
  intent: string;
  confidence: number;
  suggestedAgent?: string;
  parameters?: Record<string, any>;
}

const VALID_INTENTS = [
  "email.send",
  "email.summarize",
  "email.triage",
  "analytics.query",
  "memory.add",
  "memory.recall",
  "journal.create",
  "timeline.add",
  "plan.create",
  "plan.execute",
  "agent.run",
  "agent.status",
  "clinical.action",
  "clinical.query",
  "financial.action",
  "financial.query",
  "file.organize",
  "file.search",
  "schedule.create",
  "schedule.query",
  "unknown",
] as const;

export type TaskIntent = typeof VALID_INTENTS[number];

/**
 * Classify a user query into a high-level intent
 */
export async function classifyTask(input: string): Promise<TaskClassification> {
  if (!input || !input.trim()) {
    return {
      intent: "unknown",
      confidence: 0,
    };
  }

  const classificationPrompt = `You are Jarvis, an AI assistant classifier. Your job is to classify user queries into one of these intents:

${VALID_INTENTS.map((intent) => `- ${intent}`).join("\n")}

User query: "${input}"

Respond with ONLY a valid JSON object in this exact format:
{
  "intent": "one of the valid intents above",
  "confidence": 0.0 to 1.0,
  "suggestedAgent": "optional agent slug if applicable (e.g., 'triage_agent', 'scheduler_agent')",
  "parameters": {
    "key": "value"
  }
}

Rules:
- intent MUST be one of the valid intents listed above
- confidence should reflect how certain you are (0.0 = uncertain, 1.0 = very certain)
- suggestedAgent is optional and only if an agent should handle this
- parameters should extract any relevant information from the query
- If the query doesn't match any intent, use "unknown"

JSON response:`;

  try {
    const response = await llm(classificationPrompt);
    
    // Try to extract JSON from the response
    let jsonStr = response.trim();
    
    // Remove markdown code blocks if present
    jsonStr = jsonStr.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
    
    // Try to find JSON object in the response
    const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      jsonStr = jsonMatch[0];
    }

    const parsed = JSON.parse(jsonStr) as Partial<TaskClassification>;

    // Validate intent
    const intent = VALID_INTENTS.includes(parsed.intent as TaskIntent)
      ? (parsed.intent as TaskIntent)
      : "unknown";

    // Validate confidence
    const confidence = typeof parsed.confidence === "number"
      ? Math.max(0, Math.min(1, parsed.confidence))
      : 0.5;

    return {
      intent,
      confidence,
      suggestedAgent: parsed.suggestedAgent,
      parameters: parsed.parameters || {},
    };
  } catch (error) {
    console.error("[TaskClassifier] Error classifying task:", error);
    
    // If parse fails, return unknown with 0 confidence
    return {
      intent: "unknown",
      confidence: 0,
    };
  }
}

/**
 * Fallback classification using simple keyword matching
 */
function fallbackClassification(input: string): TaskClassification {
  const lower = input.toLowerCase();

  // Email intents
  if (lower.match(/\b(send|email|message|reply|respond)\b/)) {
    return {
      intent: "email.send",
      confidence: 0.6,
      suggestedAgent: "email_agent",
    };
  }

  if (lower.match(/\b(summarize|summary|summaries)\b.*\b(email|emails|messages)\b/)) {
    return {
      intent: "email.summarize",
      confidence: 0.6,
    };
  }

  // Memory intents
  if (lower.match(/\b(remember|save|store|memorize)\b/)) {
    return {
      intent: "memory.add",
      confidence: 0.6,
    };
  }

  if (lower.match(/\b(recall|remember|what did|tell me about)\b/)) {
    return {
      intent: "memory.recall",
      confidence: 0.6,
    };
  }

  // Journal intents
  if (lower.match(/\b(journal|log|note|entry)\b/)) {
    return {
      intent: "journal.create",
      confidence: 0.6,
    };
  }

  // Plan intents
  if (lower.match(/\b(plan|create plan|make a plan|schedule)\b/)) {
    return {
      intent: "plan.create",
      confidence: 0.6,
    };
  }

  // Clinical intents
  if (lower.match(/\b(patient|clinical|medical|appointment|visit)\b/)) {
    return {
      intent: "clinical.query",
      confidence: 0.6,
      suggestedAgent: "clinical_agent",
    };
  }

  // Financial intents
  if (lower.match(/\b(financial|money|expense|revenue|tax|nexus)\b/)) {
    return {
      intent: "financial.query",
      confidence: 0.6,
      suggestedAgent: "nexus_agent",
    };
  }

  // Default to unknown
  return {
    intent: "unknown",
    confidence: 0.3,
  };
}

