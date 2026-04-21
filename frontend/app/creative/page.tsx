"use client";

import { useState } from "react";
import Shell from "@/components/layout/Shell";
import JarvisConsole from "@/components/jarvis/JarvisConsole";

const PROJECTS = [
  { name: "IMHO Radio", type: "Content Station", status: "live" },
  { name: "Struth Radio", type: "SaaS Platform", status: "live" },
  { name: "DesignOS", type: "Design Tool", status: "building" },
  { name: "DesignAI", type: "AI Product Studio", status: "building" },
  { name: "OmniOffice", type: "Document Suite", status: "building" },
];

export default function CreativePage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  return (
    <Shell>
      <div className="flex h-full gap-4 p-4 min-h-0">
        {/* Left: projects + scratchpad */}
        <div className="w-80 shrink-0 flex flex-col gap-3 overflow-y-auto">
          <div>
            <h2 className="text-sm font-semibold text-white mb-0.5">Creative Studio</h2>
            <p className="text-xs text-slate-400">Scripts, ideas, and design discussions</p>
          </div>

          {/* Project list */}
          <div className="rounded-lg border border-slate-800 bg-slate-900 overflow-hidden">
            <div className="px-3 py-2 border-b border-slate-800">
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-widest">Creative Projects</p>
            </div>
            <div className="divide-y divide-slate-800">
              {PROJECTS.map((p) => (
                <button
                  key={p.name}
                  onClick={() => setSelected(selected === p.name ? null : p.name)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-slate-800 transition-colors ${selected === p.name ? "bg-slate-800" : ""}`}
                >
                  <div>
                    <p className="text-xs font-medium text-slate-200">{p.name}</p>
                    <p className="text-xs text-slate-500">{p.type}</p>
                  </div>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${p.status === "live" ? "bg-emerald-900/50 text-emerald-400" : "bg-amber-900/50 text-amber-400"}`}>
                    {p.status}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Scratchpad */}
          <div className="flex-1 flex flex-col rounded-lg border border-slate-800 bg-slate-900 overflow-hidden min-h-[160px]">
            <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between">
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-widest">Scratchpad</p>
              <p className="text-xs text-slate-500">ideas / context for JARVIS</p>
            </div>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Jot ideas here — paste context, outlines, or briefs before asking JARVIS…"
              className="flex-1 bg-transparent text-xs text-slate-300 placeholder-slate-600 p-3 resize-none outline-none"
              spellCheck={false}
            />
          </div>

          {/* Quick prompts */}
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p className="text-xs font-semibold text-slate-400 mb-2">Quick questions</p>
            <div className="space-y-1 text-xs text-slate-400">
              {selected
                ? [`→ "Write a launch script for ${selected}"`, `→ "Content calendar for ${selected}"`, `→ "Marketing angles for ${selected}"`].map((q) => <p key={q}>{q}</p>)
                : [<p key="1">→ Select a project above to focus</p>, <p key="2">→ "Generate a content brief"</p>, <p key="3">→ "Write a product description"</p>]}
            </div>
          </div>
        </div>

        {/* Right: JARVIS chat */}
        <div className="flex-1 min-w-0 flex flex-col">
          <JarvisConsole
            label="Creative Console"
            initialMessage={
              selected
                ? `Creative mode — focused on ${selected}. What do you need? Scripts, copy, content calendar, positioning, anything.`
                : "Creative Studio active. Select a project on the left, or just start talking. I can write scripts, brainstorm campaigns, draft copy, or think through product positioning with you."
            }
          />
        </div>
      </div>
    </Shell>
  );
}
