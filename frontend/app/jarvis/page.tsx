"use client";

import { useState } from "react";

interface Message {
  role: string;
  content: string;
}

export default function JarvisPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  async function send() {
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    const userInput = input;
    setInput("");

    // Add user message immediately
    setMessages((m) => [...m, { role: "user", content: userInput }]);

    try {
      const res = await fetch("/api/jarvis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: userInput }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();

      setMessages((m) => [
        ...m,
        { role: "jarvis", content: data.output || "No response" },
      ]);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((m) => [
        ...m,
        {
          role: "jarvis",
          content: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="p-10 bg-gray-950 min-h-screen">
      <h1 className="text-3xl font-bold text-white mb-5">Jarvis v10 Runtime</h1>

      <div className="bg-gray-900 p-4 h-[400px] overflow-y-auto rounded mb-4 border border-gray-700">
        {messages.length === 0 ? (
          <div className="text-gray-400 text-center mt-20">
            Start a conversation with Jarvis...
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className="mb-4">
              <strong className="text-blue-400">{m.role}:</strong>{" "}
              <span className="text-gray-200">{m.content}</span>
            </div>
          ))
        )}
        {isLoading && (
          <div className="text-gray-400 italic">Jarvis is thinking...</div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && send()}
          disabled={isLoading}
          className="flex-1 p-3 rounded bg-gray-800 text-white border border-gray-700 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          placeholder="Ask me anything..."
        />
        <button
          onClick={send}
          disabled={isLoading || !input.trim()}
          className="px-6 py-3 bg-blue-600 rounded text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
