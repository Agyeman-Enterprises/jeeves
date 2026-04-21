// lib/jarvis/llm/localLLM.ts

const BEAST_LLM_URL =
  process.env.BEAST_LLM_URL || "http://192.168.1.50:11434/api/generate";

export async function localLLM(prompt: string): Promise<string> {
  try {
    const res = await fetch(BEAST_LLM_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: "llama3", prompt }),
    });

    if (!res.ok) {
      throw new Error(`Local LLM returned ${res.status}`);
    }

    const json = await res.json();
    return json.response || "";
  } catch (err) {
    console.error("[localLLM] Error:", err);
    return "";
  }
}

