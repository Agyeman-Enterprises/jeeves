"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const JARVIS_URL = "/api/proxy";

type PersonalityCore = {
  name?: string;
  persona?: string;
  voice?: string;
  model?: string;
};

export default function SettingsPage() {
  const [personality, setPersonality] = useState<PersonalityCore | null>(null);
  const [backendUrl, setBackendUrl]   = useState(JARVIS_URL);
  const [loading, setLoading]         = useState(true);

  useEffect(() => {
    fetch(`${JARVIS_URL}/api/personality/core`)
      .then((r) => r.json())
      .then(setPersonality)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const sections = [
    {
      title: "Backend",
      items: [
        { label: "API URL",      value: JARVIS_URL },
        { label: "Health",       value: "http://localhost:8001/health" },
        { label: "Docs",         value: "http://localhost:8001/docs" },
        { label: "Agents",       value: "http://localhost:8001/agents/status" },
      ],
    },
    {
      title: "AI Models",
      items: [
        { label: "Primary LLM",     value: personality?.model ?? "claude-sonnet-4-6" },
        { label: "Fast model",      value: "claude-haiku-4-5" },
        { label: "Vision",          value: "Claude Vision (built-in)" },
        { label: "TTS",             value: "ElevenLabs (Aria)" },
        { label: "STT",             value: "Fireworks Whisper-v3" },
      ],
    },
    {
      title: "Integrations",
      items: [
        { label: "Vector DB",      value: "Pinecone (JARVIS index)" },
        { label: "Agent chat",     value: "Supabase Realtime (rcyekqufeautozmiljoq)" },
        { label: "Calendar",       value: "Google Calendar (OAuth)" },
        { label: "Email",          value: "Gmail + Outlook" },
        { label: "Social",         value: "LinkedIn (OAuth)" },
        { label: "Dropbox",        value: "Dropbox (OAuth)" },
      ],
    },
    {
      title: "Infrastructure",
      items: [
        { label: "Desktop machine",  value: "aaa-srv (100.120.192.79)" },
        { label: "Laptop machine",   value: "aa-bkdc2 (100.77.186.86)" },
        { label: "Tailscale Funnel", value: "https://aaa-srv.taile7cd0a.ts.net" },
        { label: "Cloud migration",  value: "Hetzner CX22 — pending Henry" },
      ],
    },
  ];

  return (
    <Shell>
      <div className="flex h-full gap-6">
        <div className="flex-1 min-w-0">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-white">Settings</h1>
            <p className="text-sm text-slate-400 mt-0.5">System configuration and integration status</p>
          </div>

          {/* Personality */}
          {!loading && personality && (
            <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900/50 p-5">
              <h2 className="mb-3 text-sm font-semibold text-white">JARVIS Personality</h2>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {Object.entries(personality).map(([k, v]) => (
                  <div key={k} className="rounded-md bg-slate-800/50 px-3 py-2">
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">{k}</p>
                    <p className="text-xs text-white truncate">{String(v)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Config sections */}
          <div className="space-y-4">
            {sections.map((section) => (
              <div key={section.title} className="rounded-lg border border-slate-800 bg-slate-900/50 p-5">
                <h2 className="mb-3 text-sm font-semibold text-white">{section.title}</h2>
                <div className="space-y-2">
                  {section.items.map((item) => (
                    <div key={item.label} className="flex items-center gap-3">
                      <span className="w-36 shrink-0 text-xs text-slate-500">{item.label}</span>
                      <span className="text-xs text-slate-300 font-mono truncate">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel */}
        <div className="w-64 shrink-0 space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              System Status
            </h3>
            <div className="space-y-2">
              <StatusRow label="JARVIS Backend"  status="online" />
              <StatusRow label="Agent Chat"      status="online" note="Supabase" />
              <StatusRow label="Pinecone"        status="online" />
              <StatusRow label="Cloud VPS"       status="pending" />
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Backend URL
            </h3>
            <input
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-800 px-2 py-1.5 text-xs text-slate-300 font-mono focus:border-emerald-500/50 focus:outline-none"
            />
            <p className="mt-1 text-[10px] text-slate-600">Reload page to apply</p>
          </div>
        </div>
      </div>
    </Shell>
  );
}

function StatusRow({ label, status, note }: { label: string; status: "online" | "offline" | "pending"; note?: string }) {
  const cfg = {
    online:  { dot: "bg-emerald-400", text: "text-emerald-400", label: "Online" },
    offline: { dot: "bg-red-500",     text: "text-red-400",     label: "Offline" },
    pending: { dot: "bg-amber-400",   text: "text-amber-400",   label: "Pending" },
  }[status];

  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-400">{label}{note ? ` (${note})` : ""}</span>
      <span className={`flex items-center gap-1.5 text-[10px] font-medium ${cfg.text}`}>
        <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
        {cfg.label}
      </span>
    </div>
  );
}
