import { useCallback, useMemo, useState } from "react"

export type ConsoleLevel = "info" | "warn" | "error"
export type ConsoleSource = "voice" | "agent" | "network" | "ui"

export interface ConsoleEntry {
  id: string
  timestamp: string
  level: ConsoleLevel
  source: ConsoleSource
  message: string
}

interface UseJarvisConsoleOptions {
  maxEntries?: number
}

export interface UseJarvisConsoleResult {
  entries: ConsoleEntry[]
  clearEntries: () => void
  logInfo: (source: ConsoleSource, message: string) => void
  logWarn: (source: ConsoleSource, message: string) => void
  logError: (source: ConsoleSource, message: string) => void
}

const now = () => new Date().toISOString()

const buildEntry = (level: ConsoleLevel, source: ConsoleSource, message: string): ConsoleEntry => ({
  id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  timestamp: now(),
  level,
  source,
  message,
})

export function useJarvisConsole(options: UseJarvisConsoleOptions = {}): UseJarvisConsoleResult {
  const { maxEntries = 200 } = options
  const [entries, setEntries] = useState<ConsoleEntry[]>([])

  const push = useCallback(
    (entry: ConsoleEntry) => {
      setEntries((prev) => {
        const next = [...prev, entry]
        if (next.length > maxEntries) {
          return next.slice(next.length - maxEntries)
        }
        return next
      })
    },
    [maxEntries],
  )

  const logFactory = useCallback(
    (level: ConsoleLevel) => (source: ConsoleSource, message: string) => {
      push(buildEntry(level, source, message))
    },
    [push],
  )

  const clearEntries = useCallback(() => setEntries([]), [])

  const loggers = useMemo(
    () => ({
      logInfo: logFactory("info"),
      logWarn: logFactory("warn"),
      logError: logFactory("error"),
    }),
    [logFactory],
  )

  return {
    entries,
    clearEntries,
    ...loggers,
  }
}


