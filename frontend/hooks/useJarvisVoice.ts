import { useCallback, useEffect, useRef, useState } from "react"
import type { UseJarvisChatResult } from "./useJarvisChat"

export type VoiceState = "idle" | "listening" | "thinking" | "speaking"

interface VoiceLogger {
  info?: (message: string) => void
  warn?: (message: string) => void
  error?: (message: string) => void
}

interface UseJarvisVoiceOptions {
  chat: Pick<UseJarvisChatResult, "sendUserMessage">
  logger?: VoiceLogger
  notify?: (variant: "info" | "error", message: string) => void
  sttPath?: string
  ttsPath?: string
}

export interface UseJarvisVoiceResult {
  state: VoiceState
  lastUserText: string | null
  lastAssistantText: string | null
  startListening: () => Promise<void>
  stopListening: () => Promise<void>
  speakText: (text: string) => Promise<void>
  stopSpeaking: () => void
}

const API_BASE = ""  // use relative paths through Next.js proxy

const defaultSttPath = "/api/proxy/api/voice/transcribe"
const defaultTtsPath = "/api/proxy/api/voice/speak"

export function useJarvisVoice(options: UseJarvisVoiceOptions): UseJarvisVoiceResult {
  const { chat, logger, notify, sttPath = defaultSttPath, ttsPath = defaultTtsPath } = options

  const [state, setState] = useState<VoiceState>("idle")
  const [lastUserText, setLastUserText] = useState<string | null>(null)
  const [lastAssistantText, setLastAssistantText] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const pendingStopResolve = useRef<(() => void) | null>(null)
  const playbackRef = useRef<HTMLAudioElement | null>(null)
  const isMountedRef = useRef(true)

  const logInfo = useCallback((message: string) => logger?.info?.(message), [logger])
  const logWarn = useCallback((message: string) => logger?.warn?.(message), [logger])
  const logError = useCallback((message: string) => logger?.error?.(message), [logger])

  const cleanupRecorder = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (recorder) {
      try {
        recorder.stream.getTracks().forEach((track) => track.stop())
      } catch (err) {
        console.warn("Failed to stop tracks", err)
      }
    }
    mediaRecorderRef.current = null
  }, [])

  useEffect(() => {
    return () => {
      isMountedRef.current = false
      cleanupRecorder()
      playbackRef.current?.pause()
      playbackRef.current = null
    }
  }, [cleanupRecorder])

  const speakText = useCallback(
    async (text: string) => {
      const trimmed = text?.trim()
      if (!trimmed) return

      logInfo(`Speaking ${trimmed.slice(0, 60)}...`)
      setLastAssistantText(trimmed)
      setState("speaking")

      try {
        const response = await fetch(`${API_BASE}${ttsPath}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: trimmed }),
        })

        if (!response.ok) {
          throw new Error(await response.text())
        }

        const arrayBuffer = await response.arrayBuffer()
        const audioBlob = new Blob([arrayBuffer], { type: "audio/wav" })
        const audioUrl = URL.createObjectURL(audioBlob)
        const audio = new Audio()
        audio.src = audioUrl
        audio.autoplay = true
        audio.preload = "auto"
        audio.crossOrigin = "anonymous"
        playbackRef.current = audio

        await new Promise<void>((resolve, reject) => {
          audio.onended = () => {
            URL.revokeObjectURL(audioUrl)
            resolve()
          }
          audio.onerror = () => {
            URL.revokeObjectURL(audioUrl)
            reject(new Error("Audio playback failed"))
          }
          audio.play().catch(reject)
        })
      } catch (error) {
        const message = error instanceof Error ? error.message : "TTS playback failed"
        logError(message)
        notify?.("error", "Audio response unavailable")
      } finally {
        if (isMountedRef.current) {
          setState("idle")
        }
      }
    },
    [logError, logInfo, notify, ttsPath],
  )

  const processAudioBlob = useCallback(
    async (audioBlob: Blob) => {
      if (!audioBlob.size) {
        logWarn("Captured audio blob is empty.")
        setState("idle")
        return
      }

      setState("thinking")
      logInfo("Sending audio to Whisper transcription service.")

      const formData = new FormData()
      formData.append("file", audioBlob, "audio.webm")

      try {
        const response = await fetch(`${API_BASE}${sttPath}`, {
          method: "POST",
          body: formData,
        })

        if (!response.ok) {
          throw new Error(await response.text())
        }

        const data = await response.json()
        const transcript = (data?.text ?? "").trim()
        if (!transcript) {
          throw new Error("No transcription text returned.")
        }

        setLastUserText(transcript)
        logInfo(`Transcription complete: ${transcript}`)

        const assistantText = await chat.sendUserMessage(transcript)
        if (assistantText) {
          setLastAssistantText(assistantText)
          await speakText(assistantText)
        } else {
          notify?.("error", "Jarvis could not respond")
          setState("idle")
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "Transcription failed"
        logError(message)
        notify?.("error", "Could not understand audio")
        setState("idle")
      }
    },
    [chat, logError, logInfo, notify, speakText, sttPath],
  )

  const startListening = useCallback(async () => {
    if (state === "listening") {
      logWarn("Voice capture already in progress.")
      return
    }
    if (typeof window === "undefined" || !navigator?.mediaDevices) {
      logWarn("Media devices unavailable in this environment.")
      notify?.("error", "Microphone unavailable")
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" })
        chunksRef.current = []
        await processAudioBlob(blob)
        pendingStopResolve.current?.()
        pendingStopResolve.current = null
      }
      recorder.onerror = (event) => {
        logError(`MediaRecorder error: ${event.error?.message ?? "unknown error"}`)
        setState("idle")
      }

      recorder.start()
      setState("listening")
      logInfo("Voice capture started.")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to access microphone"
      logError(message)
      notify?.("error", "Microphone permission denied")
      setState("idle")
    }
  }, [logError, logInfo, notify, processAudioBlob, state])

  const stopListening = useCallback(async () => {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state === "inactive") {
      setState((prev) => (prev === "listening" ? "idle" : prev))
      cleanupRecorder()
      return
    }

    setState("thinking")
    logInfo("Stopping voice capture.")

    const stopPromise = new Promise<void>((resolve) => {
      pendingStopResolve.current = resolve
    })

    try {
      recorder.stop()
    } catch (err) {
      logWarn(`Error stopping recorder: ${err}`)
    }
    cleanupRecorder()

    await stopPromise
  }, [cleanupRecorder, logInfo, logWarn])

  const stopSpeaking = useCallback(() => {
    const audio = playbackRef.current
    if (audio) {
      try {
        const srcUrl = audio.src
        audio.pause()
        audio.currentTime = 0
        audio.src = ""
        audio.load()
        if (srcUrl && srcUrl.startsWith("blob:")) {
          URL.revokeObjectURL(srcUrl)
        }
      } catch (err) {
        logWarn(`Error stopping audio: ${err}`)
      }
      playbackRef.current = null
    }
    if (isMountedRef.current) {
      setState("idle")
    }
    logInfo("Speech playback stopped by user.")
  }, [logInfo, logWarn])

  return {
    state,
    lastUserText,
    lastAssistantText,
    startListening,
    stopListening,
    speakText,
    stopSpeaking,
  }
}


