// app/jarvis/widget/page.tsx
// Compact floating chat overlay — used by the tray app pywebview window
"use client"

import { useState, useRef, useEffect } from "react"
import { Send, X, Minus, Loader2 } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  agent?: string
  ts: number
}

export default function JarvisWidget() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "0",
      role: "assistant",
      content: "Hey — what do you need?",
      ts: Date.now(),
    },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => `widget_${Date.now()}`)
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (nearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Escape key hides the window
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close()
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput("")
    const userMsg: Message = { id: `u${Date.now()}`, role: "user", content: text, ts: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    try {
      const res = await fetch("/api/jarvis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: text, session_id: sessionId }),
      })
      const data = await res.json()
      const reply = data.reply ?? data.content ?? data.error ?? "No response."
      setMessages(prev => [
        ...prev,
        { id: `a${Date.now()}`, role: "assistant", content: reply, agent: data.agent, ts: Date.now() },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        { id: `e${Date.now()}`, role: "assistant", content: "Connection error — is JARVIS running?", ts: Date.now() },
      ])
    }
    setLoading(false)
  }

  const close = () => {
    // pywebview: hide window. Edge app mode: close tab.
    try { (window as any).pywebview?.api?.hide_window() } catch {}
    try { window.close() } catch {}
  }

  const minimize = () => {
    try { (window as any).pywebview?.api?.minimize_window() } catch {}
  }

  return (
    <div
      className="flex flex-col h-screen bg-[#0a0a0f] text-white select-none"
      style={{ fontFamily: "'Inter', sans-serif" }}
    >
      {/* Drag handle / title bar */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-black/40 border-b border-white/[0.06] cursor-move shrink-0"
        style={{ WebkitAppRegion: "drag" } as React.CSSProperties}
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
          <span className="text-sm font-semibold tracking-wide text-amber-400">JARVIS</span>
        </div>
        <div
          className="flex items-center gap-1"
          style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}
        >
          <button
            onClick={minimize}
            className="p-1 rounded hover:bg-white/10 transition-colors text-slate-500 hover:text-slate-300"
          >
            <Minus className="w-3 h-3" />
          </button>
          <button
            onClick={close}
            className="p-1 rounded hover:bg-red-500/20 transition-colors text-slate-500 hover:text-red-400"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-4 space-y-3 scrollbar-thin scrollbar-thumb-white/10">
        {messages.map(m => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-amber-500/20 text-amber-50 rounded-br-md"
                  : "bg-white/[0.06] text-slate-200 rounded-bl-md"
              }`}
            >
              {m.content}
              {m.agent && m.role === "assistant" && (
                <div className="text-[10px] text-slate-600 mt-1">{m.agent}</div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white/[0.06] rounded-2xl rounded-bl-md px-3 py-2">
              <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 px-3 pb-4 pt-2 border-t border-white/[0.06]">
        <div className="flex items-center gap-2 bg-white/[0.05] rounded-2xl px-3 py-2 border border-white/[0.08] focus-within:border-amber-500/40 transition-colors">
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Ask JARVIS anything..."
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none"
            disabled={loading}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="p-1 rounded-xl text-amber-500 hover:text-amber-400 disabled:opacity-30 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center text-[10px] text-slate-700 mt-2">Enter to send · Esc to hide</p>
      </div>
    </div>
  )
}
