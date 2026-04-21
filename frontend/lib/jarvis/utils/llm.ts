// Unified LLM client with local-first fallback chain
// Tries: Local LLM (Ollama/LM Studio) → OpenAI → Anthropic Claude

const LOCAL_LLM_BASE_URL = process.env.LOCAL_LLM_BASE_URL || "http://localhost:11434";
const LOCAL_LLM_MODEL = process.env.LOCAL_LLM_MODEL || "llama3.2";
const LOCAL_LLM_API_KEY = process.env.LOCAL_LLM_API_KEY || "";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "";
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "";
const JARVIS_LLM_MODEL = process.env.JARVIS_LLM_MODEL || "gpt-4o-mini";

const LLM_TIMEOUT_MS = 30000; // 30 seconds timeout

interface LLMResponse {
  text: string;
  model: string;
}

/**
 * Try local LLM (Ollama or LM Studio)
 */
async function tryLocalLLM(prompt: string): Promise<LLMResponse | null> {
  try {
    const url = `${LOCAL_LLM_BASE_URL}/api/generate`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), LLM_TIMEOUT_MS);

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(LOCAL_LLM_API_KEY && { Authorization: `Bearer ${LOCAL_LLM_API_KEY}` }),
      },
      body: JSON.stringify({
        model: LOCAL_LLM_MODEL,
        prompt,
        stream: false,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const text = data.response || data.text || "";
    
    if (!text.trim()) {
      return null;
    }

    return { text: text.trim(), model: `local:${LOCAL_LLM_MODEL}` };
  } catch (error) {
    // Local LLM not available or timed out
    return null;
  }
}

/**
 * Try OpenAI
 */
async function tryOpenAI(prompt: string): Promise<LLMResponse | null> {
  if (!OPENAI_API_KEY) {
    return null;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), LLM_TIMEOUT_MS);

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: JARVIS_LLM_MODEL,
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const text = data.choices?.[0]?.message?.content || "";

    if (!text.trim()) {
      return null;
    }

    return { text: text.trim(), model: `openai:${JARVIS_LLM_MODEL}` };
  } catch (error) {
    return null;
  }
}

/**
 * Try Anthropic Claude
 */
async function tryAnthropic(prompt: string): Promise<LLMResponse | null> {
  if (!ANTHROPIC_API_KEY) {
    return null;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), LLM_TIMEOUT_MS);

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-6",
        max_tokens: 2000,
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const text = data.content?.[0]?.text || "";

    if (!text.trim()) {
      return null;
    }

    return { text: text.trim(), model: "claude-sonnet-4-6" };
  } catch (error) {
    return null;
  }
}

/**
 * Unified LLM call function with fallback chain
 * Tries: Local → OpenAI → Anthropic
 * Returns plain text only
 * Does not throw unless all models fail
 */
export async function llm(prompt: string): Promise<string> {
  // Try local LLM first
  const localResult = await tryLocalLLM(prompt);
  if (localResult) {
    return localResult.text;
  }

  // Fallback to OpenAI
  const openaiResult = await tryOpenAI(prompt);
  if (openaiResult) {
    return openaiResult.text;
  }

  // Fallback to Anthropic
  const anthropicResult = await tryAnthropic(prompt);
  if (anthropicResult) {
    return anthropicResult.text;
  }

  // All models failed
  throw new Error("All LLM providers failed. Please check your API keys and network connection.");
}

/**
 * Get LLM response with model information
 */
export async function llmWithModel(prompt: string): Promise<LLMResponse> {
  const localResult = await tryLocalLLM(prompt);
  if (localResult) {
    return localResult;
  }

  const openaiResult = await tryOpenAI(prompt);
  if (openaiResult) {
    return openaiResult;
  }

  const anthropicResult = await tryAnthropic(prompt);
  if (anthropicResult) {
    return anthropicResult;
  }

  throw new Error("All LLM providers failed. Please check your API keys and network connection.");
}

