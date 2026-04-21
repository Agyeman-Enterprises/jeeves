// Query rewriter - normalizes shorthand/broken English to clear structured English
import { llm } from "../utils/llm";

/**
 * Rewrite a user query to be clear and structured
 * Preserves meaning while normalizing to proper English
 */
export async function rewriteQuery(input: string): Promise<string> {
  if (!input || !input.trim()) {
    return input;
  }

  const rewritePrompt = `You are Jarvis, an AI assistant query rewriter. Your job is to rewrite user queries from shorthand, broken English, or partial commands into clear, structured English while preserving the exact meaning.

Examples:
- "email john draft pls" → "Draft an email to John."
- "remind me meeting tomorrow" → "Remind me about the meeting tomorrow."
- "what did I say about project" → "What did I say about the project?"

User query: "${input}"

Rewrite the query to be clear, structured English. Return ONLY the rewritten query, nothing else. No explanations, no JSON, just the rewritten text.`;

  try {
    const response = await llm(rewritePrompt);
    const rewritten = response.trim();
    
    // If the response is empty or seems invalid, return original
    if (!rewritten || rewritten.length < input.length * 0.5) {
      return input;
    }
    
    return rewritten;
  } catch (error) {
    console.error("[QueryRewriter] Error rewriting query:", error);
    // Fallback to original text if LLM fails
    return input;
  }
}

