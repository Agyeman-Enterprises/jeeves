"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/layout/Shell";

const JARVIS_URL = "/api/proxy";
const SUPABASE_URL = "https://rcyekqufeautozmiljoq.supabase.co";

type Message = {
  id: string;
  from_agent: string;
  to_agent: string | null;
  message: string;
  created_at: string;
};

type GraphNode = {
  id: string;
  entities: { name: string; type: string }[];
};

const AGENT_COLORS: Record<string, string> = {
  "aaa-srv":  "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  "aa-bkdc2": "bg-blue-500/10 text-blue-400 border-blue-500/20",
  "cloud":    "bg-purple-500/10 text-purple-400 border-purple-500/20",
};

export default function MemoryPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [entities, setEntities] = useState<GraphNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      // Load agent chat history from JARVIS backend proxy
      try {
        const r = await fetch(`${JARVIS_URL}/api/graph/entities`);
        if (r.ok) {
          const data = await r.json();
          setEntities(Array.isArray(data) ? data : []);
        }
      } catch {
        // offline
      }

      // Try to load agent messages directly
      try {
        const r = await fetch(
          `${SUPABASE_URL}/rest/v1/agent_messages?select=*&order=created_at.desc&limit=30`,
          {
            headers: {
              "apikey": process.env.NEXT_PUBLIC_JARVISCORE_ANON_KEY ?? "",
              "Authorization": `Bearer ${process.env.NEXT_PUBLIC_JARVISCORE_ANON_KEY ?? ""}`,
            },
          }
        );
        if (r.ok) setMessages(await r.json());
      } catch {
        // offline
      }

      setLoading(false);
    };
    load();
    const t = setInterval(load, 15_000);
    return () => clearInterval(t);
  }, []);

  return (
    <Shell>
      <div className="flex h-full gap-6">
        <div className="flex-1 min-w-0">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-white">Memory Graph</h1>
            <p className="text-sm text-slate-400 mt-0.5">
              Agent conversation history · entity relationships · long-term context
            </p>
          </div>

          {/* Agent chat channel */}
          <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">Agent Chat Channel</h2>
              <span className="flex items-center gap-1.5 text-[10px] text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Supabase Realtime
              </span>
            </div>

            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-12 animate-pulse rounded bg-slate-800/50" />
                ))}
              </div>
            ) : messages.length === 0 ? (
              <p className="text-sm text-slate-500">No messages yet — agent chat is live on Supabase</p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {messages.map((msg) => {
                  const cls = AGENT_COLORS[msg.from_agent] ?? "bg-slate-500/10 text-slate-400 border-slate-500/20";
                  return (
                    <div key={msg.id} className="flex gap-3 rounded-lg border border-slate-800/50 bg-slate-900 p-3">
                      <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium self-start ${cls}`}>
                        {msg.from_agent}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">
                          {msg.message}
                        </p>
                        <p className="mt-1 text-[10px] text-slate-600">
                          {new Date(msg.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Knowledge graph entities */}
          {entities.length > 0 && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-5">
              <h2 className="mb-4 text-sm font-semibold text-white">Knowledge Graph Entities</h2>
              <div className="flex flex-wrap gap-2">
                {entities.flatMap((n) => n.entities).slice(0, 40).map((e, i) => (
                  <span
                    key={i}
                    className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] text-slate-400"
                  >
                    {e.name}
                    <span className="ml-1 text-slate-600">{e.type}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="w-64 shrink-0 space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Channel Info
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Table</span>
                <span className="text-slate-300 font-mono">agent_messages</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Messages</span>
                <span className="text-slate-300">{messages.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Mode</span>
                <span className="text-emerald-400">Realtime</span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              Agents Online
            </h3>
            <div className="space-y-2">
              {["aaa-srv", "aa-bkdc2"].map((agent) => {
                const lastMsg = messages.find((m) => m.from_agent === agent);
                const cls = AGENT_COLORS[agent] ?? "";
                return (
                  <div key={agent} className="flex items-center gap-2">
                    <span className={`rounded border px-1.5 py-0.5 text-[10px] font-medium ${cls}`}>
                      {agent}
                    </span>
                    <span className="text-[10px] text-slate-600 truncate">
                      {lastMsg ? new Date(lastMsg.created_at).toLocaleTimeString() : "no messages"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
