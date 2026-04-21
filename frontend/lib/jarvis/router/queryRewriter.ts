// Query rewriting layer - refines user queries for better execution
import { llm } from "../utils/llm";
import type { TaskClassification } from "../classifier/taskClassifier";

export interface RewrittenQuery {
  original: string;
  rewritten: string;
  context?: Record<string, any>;
}

/**
 * Rewrite a user query to be more specific and actionable
 */
export async function rewriteQuery(
  input: string,
  classification: TaskClassification
): Promise<RewrittenQuery> {
  if (!input || !input.trim()) {
    return {
      original: input,
      rewritten: input,
    };
  }

  // For simple intents, no rewriting needed
  if (classification.intent === "unknown" || classification.confidence < 0.5) {
    return {
      original: input,
      rewritten: input,
    };
  }

  const rewritePrompt = `You are Jarvis, an AI assistant query rewriter. Your job is to rewrite user queries to be more specific, actionable, and clear while preserving the original intent.

Original query: "${input}"
Classified intent: "${classification.intent}"
Confidence: ${classification.confidence}

Rewrite the query to:
1. Be more specific and actionable
2. Include any missing context that would help execution
3. Preserve the original intent and meaning
4. Make it clear what action should be taken

Respond with ONLY a valid JSON object:
{
  "rewritten": "the rewritten query",
  "context": {
    "key": "value"
  }
}

The rewritten query should be a single, clear instruction. The context object should contain any extracted parameters or additional information.

JSON response:`;

  try {
    const response = await llm(rewritePrompt);
    
    // Extract JSON from response
    let jsonStr = response.trim();
    jsonStr = jsonStr.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
    
    const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      jsonStr = jsonMatch[0];
    }

    const parsed = JSON.parse(jsonStr) as Partial<RewrittenQuery>;

    return {
      original: input,
      rewritten: parsed.rewritten || input,
      context: {
        ...classification.parameters,
        ...parsed.context,
      },
    };
  } catch (error) {
    console.error("[QueryRewriter] Error rewriting query:", error);
    
    // Fallback: return original with classification context
    return {
      original: input,
      rewritten: input,
      context: classification.parameters,
    };
  }
}

/**
 * Simple query rewriting without LLM (for fast path)
 */
export function rewriteQuerySimple(
  input: string,
  classification: TaskClassification
): RewrittenQuery {
  // For high-confidence classifications, minimal rewriting
  if (classification.confidence >= 0.8) {
    return {
      original: input,
      rewritten: input,
      context: classification.parameters,
    };
  }

  // For lower confidence, add intent context
  const rewritten = classification.intent !== "unknown"
    ? `[Intent: ${classification.intent}] ${input}`
    : input;

  return {
    original: input,
    rewritten,
    context: classification.parameters,
  };
}

