import { useCallback, useMemo, useRef, useState } from "react"

const API_BASE = ""  // relative paths go through Next.js proxy

export type Sender = "user" | "assistant" | "system"

export interface ChatMessage {
  id: string
  sender: Sender
  text: string
  createdAt: string
}

interface SendMessageOptions {
  context?: Record<string, unknown>
  signal?: AbortSignal
  onToken?: (token: string) => void
}

interface UseJarvisChatOptions {
  onLog?: (level: "info" | "warn" | "error", source: string, message: string) => void
}

export interface UseJarvisChatResult {
  messages: ChatMessage[]
  isStreaming: boolean
  sendUserMessage: (text: string, options?: SendMessageOptions) => Promise<string | null>
  appendAssistantToken: (token: string) => void
  finalizeAssistantMessage: () => void
}

const createMessage = (sender: Sender, text: string): ChatMessage => ({
  id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  sender,
  text,
  createdAt: new Date().toISOString(),
})

export function useJarvisChat(options: UseJarvisChatOptions = {}): UseJarvisChatResult {
  const { onLog } = options
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const assistantBufferRef = useRef<ChatMessage | null>(null)

  const log = useCallback(
    (level: "info" | "warn" | "error", source: string, message: string) => {
      onLog?.(level, source, message)
    },
    [onLog],
  )

  const sendUserMessage = useCallback(
    async (text: string, options?: SendMessageOptions): Promise<string | null> => {
      const userMsg = createMessage("user", text)
      setMessages((prev) => [...prev, userMsg])
      setIsStreaming(true)

      try {
        const response = await fetch(`/api/jarvis`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ input: text, context: options?.context }),
          signal: options?.signal,
        })

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }

        const data = await response.json()
        const assistantText = data.response || data.content || "No response"
        const assistantMsg = createMessage("assistant", assistantText)
        
        setMessages((prev) => [...prev, assistantMsg])
        setIsStreaming(false)
        return assistantMsg.id
      } catch (error) {
        log("error", "useJarvisChat", `Failed to send message: ${error}`)
        const errorMsg = createMessage("system", `Error: ${error instanceof Error ? error.message : "Unknown error"}`)
        setMessages((prev) => [...prev, errorMsg])
        setIsStreaming(false)
        return null
      }
    },
    [log],
  )

  const appendAssistantToken = useCallback((token: string) => {
    if (!assistantBufferRef.current) {
      assistantBufferRef.current = createMessage("assistant", token)
    } else {
      assistantBufferRef.current.text += token
    }
    setMessages((prev) => {
      const withoutLast = prev.slice(0, -1)
      return [...withoutLast, assistantBufferRef.current!]
    })
  }, [])

  const finalizeAssistantMessage = useCallback(() => {
    assistantBufferRef.current = null
    setIsStreaming(false)
  }, [])

  return {
    messages,
    isStreaming,
    sendUserMessage,
    appendAssistantToken,
    finalizeAssistantMessage,
  }
}
