"use client";

import { useState } from "react";
import Shell from "@/components/layout/Shell";
import JarvisConsole from "@/components/jarvis/JarvisConsole";

const EXPERIMENTS = [
  { label: "Web search", prompt: "Search the web for: " },
  { label: "Screenshot a URL", prompt: "Screenshot https://" },
  { label: "Analyze image", prompt: "Analyze this image: " },
  { label: "Draft email", prompt: "Draft a professional email about: " },
  { label: "Browse & extract", prompt: "Go to and extract data from: " },
  { label: "Run a workflow", prompt: "Run the workflow: " },
];

export default function LabPage() {
  const [active, setActive] = useState<string | null>(null);

  return (
    <Shell>
      <div className="flex h-full gap-4 p-4 min-h-0">
        {/* Left: experiment launcher */}
        <div className="w-72 shrink-0 flex flex-col gap-3 overflow-y-auto">
          <div>
            <h2 className="text-sm font-semibold text-white mb-0.5">Lab</h2>
            <p className="text-xs text-slate-400">Sandbox — test agents, commands, weird ideas</p>
          </div>

          {/* Quick starters */}
          <div className="rounded-lg border border-slate-800 bg-slate-900 overflow-hidden">
            <div className="px-3 py-2 border-b border-slate-800">
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-widest">Quick starters</p>
            </div>
            <div className="divide-y divide-slate-800">
              {EXPERIMENTS.map((e) => (
                <button
                  key={e.label}
                  onClick={() => setActive(active === e.label ? null : e.label)}
                  className={`w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-slate-800 transition-colors ${active === e.label ? "bg-slate-800" : ""}`}
                >
                  <span className="text-emerald-500 text-xs">›</span>
                  <span className="text-xs text-slate-300">{e.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Active agents */}
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p className="text-xs font-semibold text-slate-300 mb-2">Available agents</p>
            <div className="space-y-1">
              {["Browser", "Vision", "System", "Search", "File", "Calendar", "Email", "Finance"].map((a) => (
                <div key={a} className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  <span className="text-xs text-slate-400">{a}Agent</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
            <p className="text-xs text-slate-400">
              This is your sandbox. Nothing here has real consequences unless you explicitly ask JARVIS to save, send, or publish.
            </p>
          </div>
        </div>

        {/* Right: JARVIS chat */}
        <div className="flex-1 min-w-0 flex flex-col">
          <JarvisConsole
            label="Lab Console"
            initialMessage={
              active
                ? `Lab mode — ${active} loaded. Type the rest of your command and I'll handle it.`
                : "Lab active. This is your sandbox — try anything. I can browse the web, screenshot URLs, analyze images, run workflows, search files, or just think through an idea with you. Nothing commits until you say so."
            }
          />
        </div>
      </div>
    </Shell>
  );
}
