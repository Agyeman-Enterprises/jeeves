// lib/jarvis/brain/classify.ts

import OpenAI from "openai";

function getClient() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY is not set");
  }
  return new OpenAI({ apiKey });
}

export async function classifyText(text: string): Promise<string> {
  if (!text.trim()) return "unknown";

  try {
    const client = getClient();
    const res = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "You are a classifier. Respond with exactly one of: summary, writing, analytics, schedule, journal, routing, unknown.",
        },
        { role: "user", content: text },
      ],
    });

    return res.choices[0].message.content?.trim().toLowerCase() || "unknown";
  } catch (err) {
    console.error("[classifyText] error:", err);
    return "unknown";
  }
}

