"use client";

import { useState, useCallback } from "react";

const API_BASE = "/api/proxy";

export function useJarvisStream() {
  const [output, setOutput] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState(false);

  const run = useCallback(async (command: string) => {
    setOutput("");
    setIsStreaming(true);

    try {
      const response = await fetch(`/api/jarvis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: command }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      // Check if response is streaming
      const contentType = response.headers.get("content-type");
      if (contentType?.includes("text/stream") || contentType?.includes("text/event-stream")) {
        // Handle streaming response
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          let buffer = "";
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const data = line.slice(6);
                if (data === "[DONE]") {
                  setIsStreaming(false);
                  return;
                }
                try {
                  const parsed = JSON.parse(data);
                  setOutput((prev) => prev + (parsed.token || parsed.text || ""));
                } catch {
                  // Not JSON, append as-is
                  setOutput((prev) => prev + data);
                }
              }
            }
          }
        }
      } else {
        // Regular JSON response
        const data = await response.json();
        setOutput(data.response || data.content || "");
      }
    } catch (error) {
      setOutput(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsStreaming(false);
    }
  }, []);

  return { output, run, isStreaming };
}

