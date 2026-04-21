"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { sendJarvisCommand } from "@/lib/api/jarvisClient";

type Message = { from: "user" | "jarvis" | "error"; text: string };
type VoiceState = "idle" | "recording" | "transcribing" | "speaking";

type Props = {
  label?: string;
  initialMessage?: string;
};

function speakText(text: string): void {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 1.05;
  utter.pitch = 1.0;
  // Prefer a natural English voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(
    (v) => v.lang.startsWith("en") && (v.name.includes("Samantha") || v.name.includes("Google") || v.name.includes("Natural"))
  );
  if (preferred) utter.voice = preferred;
  window.speechSynthesis.speak(utter);
}

export default function JarvisConsole({ label, initialMessage }: Props = {}) {
  const [messages, setMessages] = useState<Message[]>([
    { from: "jarvis", text: initialMessage ?? "System ready. Standing by, Doctor." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (nearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
    // Load voices on mount (Chrome needs this warm-up)
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.getVoices();
    }
  }, []);

  const processVoiceQuery = useCallback(async (query: string) => {
    if (!query.trim()) return;
    setMessages((m) => [...m, { from: "user", text: `🎙 ${query}` }]);
    setLoading(true);
    setVoiceState("speaking");
    try {
      const res = await sendJarvisCommand({ command: query });
      const reply = res.reply;
      setMessages((m) => [...m, { from: res.ok ? "jarvis" : "error", text: reply }]);
      if (res.ok) speakText(reply);
    } catch {
      setMessages((m) => [...m, { from: "error", text: "Could not reach JARVIS backend." }]);
    } finally {
      setLoading(false);
      setVoiceState("idle");
    }
  }, []);

  const startRecording = useCallback(async () => {
    if (voiceState !== "idle" || loading) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setVoiceState("transcribing");
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const form = new FormData();
        form.append("file", blob, "recording.webm");
        try {
          const r = await fetch("/api/proxy/api/voice/transcribe", { method: "POST", body: form });
          const data = await r.json();
          const text: string = data.text ?? "";
          if (text.trim()) {
            await processVoiceQuery(text);
          } else {
            setMessages((m) => [...m, { from: "error", text: "No speech detected." }]);
            setVoiceState("idle");
          }
        } catch {
          setMessages((m) => [...m, { from: "error", text: "Transcription failed." }]);
          setVoiceState("idle");
        }
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setVoiceState("recording");
    } catch {
      setMessages((m) => [...m, { from: "error", text: "Microphone access denied." }]);
    }
  }, [voiceState, loading, processVoiceQuery]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, [voiceState]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { from: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendJarvisCommand({ command: text });
      setMessages((m) => [
        ...m,
        { from: res.ok ? "jarvis" : "error", text: res.reply },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { from: "error", text: "Could not reach JARVIS backend." },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  return (
    <div
      className="flex flex-col rounded-xl border border-slate-700 bg-slate-900 overflow-hidden"
      style={{ minHeight: "420px" }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-slate-700 px-4 py-2 shrink-0">
        <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-xs font-semibold text-emerald-300 uppercase tracking-widest">
          {label ?? "Jarvis Command Console"}
        </span>
      </div>

      {/* Message log */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-3 space-y-2 font-mono text-xs"
        style={{ maxHeight: "340px" }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={
              msg.from === "user"
                ? "text-slate-300"
                : msg.from === "error"
                ? "text-red-400"
                : "text-emerald-300"
            }
          >
            <span className="opacity-50 mr-2">
              {msg.from === "user" ? "YOU›" : msg.from === "error" ? "ERR›" : "JAR›"}
            </span>
            <span className="whitespace-pre-wrap">{msg.text}</span>
          </div>
        ))}
        {loading && (
          <div className="text-emerald-500 animate-pulse">JAR› thinking…</div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-slate-700 bg-slate-950 px-3 py-2 shrink-0"
      >
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || voiceState !== "idle"}
          placeholder={
            voiceState === "recording" ? "Recording… tap mic to stop" :
            voiceState === "transcribing" ? "Transcribing…" :
            voiceState === "speaking" ? "JARVIS is speaking…" :
            "Issue a command to JARVIS…"
          }
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none disabled:opacity-50"
          autoComplete="off"
          spellCheck={false}
        />
        {/* Voice button */}
        <button
          type="button"
          onClick={voiceState === "recording" ? stopRecording : startRecording}
          disabled={loading || voiceState === "transcribing" || voiceState === "speaking"}
          title={voiceState === "recording" ? "Stop recording" : "Start voice input"}
          className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors shrink-0 ${
            voiceState === "recording"
              ? "bg-red-600 hover:bg-red-500 text-white animate-pulse"
              : "bg-slate-700 hover:bg-slate-600 text-slate-200 disabled:opacity-40"
          }`}
        >
          {voiceState === "recording" ? "■" : "🎙"}
        </button>
        <button
          type="submit"
          disabled={loading || !input.trim() || voiceState !== "idle"}
          className="rounded-md bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-40 transition-colors shrink-0"
        >
          {loading ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
