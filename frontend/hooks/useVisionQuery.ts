import { useState, useCallback } from "react"

const API_BASE = "/api/proxy"

interface VisionQueryResult {
  answer: string
  query?: string
}

export function useVisionQuery() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const queryImage = useCallback(
    async (base64Image: string, query?: string): Promise<string | null> => {
      setIsProcessing(true)
      setError(null)

      try {
        const response = await fetch(`${API_BASE}/api/vision/query/base64`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image: base64Image,
            query: query || "What is in this image?",
          }),
        })

        if (!response.ok) {
          throw new Error(await response.text())
        }

        const data: VisionQueryResult = await response.json()
        return data.answer
      } catch (err) {
        const message = err instanceof Error ? err.message : "Vision query failed"
        setError(message)
        return null
      } finally {
        setIsProcessing(false)
      }
    },
    [],
  )

  return {
    queryImage,
    isProcessing,
    error,
  }
}

