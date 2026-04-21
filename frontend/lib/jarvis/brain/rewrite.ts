// lib/jarvis/brain/rewrite.ts

import OpenAI from "openai";

function getClient() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY is not set");
  }
  return new OpenAI({ apiKey });
}

export async function rewriteQuery(text: string): Promise<string> {
  if (!text.trim()) return text;

  try {
    const client = getClient();
    const res = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "Rewrite the user's request to be as explicit and actionable as possible for an AI assistant.",
        },
        { role: "user", content: text },
      ],
    });

    return res.choices[0].message.content?.trim() || text;
  } catch (err) {
    console.error("[rewriteQuery] error:", err);
    return text;
  }
}

