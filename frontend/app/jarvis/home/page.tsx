// app/jarvis/home/page.tsx

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useJarvisTheme } from "@/components/theme/JarvisThemeProvider";
import {
  getGreetingForTime,
  getMoodForTime,
  describeMood,
} from "@/lib/jarvisPersona";
import { sendJarvisCommand } from "@/lib/api/jarvisClient";
import Shell from "@/components/layout/Shell";
import {
  useJarvisWorkspace,
  WORKSPACES,
} from "@/components/jarvis/JarvisWorkspaceContext";

type QuickAction = {
  label: string;
  cmd: string;
  naturalLanguage: string;
  /** If set, calls this API endpoint directly instead of sending a natural-language command */
  directApi?: { url: string; method: "GET" | "POST"; body?: object };
};

type TimelineItem = {
  id: string | number;
  time: string;
  source: string;
  text: string;
};

type PersonalSnapshot = {
  weather: {
    location: string;
    summary: string;
    temp: string;
  } | null;
  nextEvent: {
    title: string;
    start_time: string;
  } | null;
  tasks: { title: string }[];
};

const quickActions: QuickAction[] = [
  {
    label: "What can you do?",
    cmd: "show-capabilities",
    naturalLanguage: "Tell me what you can do for me.",
  },
  {
    label: "Summarize my world",
    cmd: "daily-summary",
    naturalLanguage: "Give me a quick summary of my current world and priorities.",
  },
  {
    label: "Check schedule",
    cmd: "check-schedule",
    naturalLanguage: "Show me my upcoming schedule and critical appointments.",
  },
  {
    label: "Latest tasks",
    cmd: "latest-tasks",
    naturalLanguage: "Show me the latest tasks you think I should care about.",
  },
  {
    label: "Brain dump",
    cmd: "start-brain-dump",
    naturalLanguage:
      "Open a new space so I can brain dump and you can organize it.",
  },
  {
    label: "Calm the chaos",
    cmd: "calm-chaos",
    naturalLanguage:
      "Look at everything on my plate and suggest the next 3 highest-leverage moves.",
  },
  // ── Embodiment layer quick actions ──────────────────────────────────────
  {
    label: "Search Web",
    cmd: "search-web",
    naturalLanguage: "Search the web for current news and interesting topics.",
    directApi: {
      url: "/api/proxy/api/browser/search",
      method: "POST",
      body: { query: "latest AI news and technology" },
    },
  },
  {
    label: "Look at Screen",
    cmd: "look-at-screen",
    naturalLanguage: "Look at my screen and tell me what you see.",
    directApi: {
      url: "/api/proxy/api/vision/screenshot",
      method: "POST",
      body: { question: "What do you see on this screen? Describe it fully." },
    },
  },
  {
    label: "System Status",
    cmd: "system-status",
    naturalLanguage: "Check my system resources — CPU, memory, disk.",
    directApi: {
      url: "/api/proxy/api/system/status",
      method: "GET",
    },
  },
  {
    label: "Voice Mode",
    cmd: "voice-mode",
    naturalLanguage: "Start continuous voice listening mode.",
    directApi: {
      url: "/api/proxy/api/voice/pipeline/start",
      method: "POST",
    },
  },
];

export default function JarvisHomePage() {
  const { skin } = useJarvisTheme();
  const { activeWorkspace, setActiveWorkspace, workspace } =
    useJarvisWorkspace();

  const [greeting, setGreeting] = useState("");
  const [moodText, setMoodText] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [timeline, setTimeline] = useState<TimelineItem[] | null>(null);
  const [personal, setPersonal] = useState<PersonalSnapshot | null>(null);
  const [loadingTimeline, setLoadingTimeline] = useState(true);
  const [loadingPersonal, setLoadingPersonal] = useState(true);

  type PriorityItem = { category: string; urgency: string; title: string; detail: string; source: string };
  type PrioritiesData = { summary: string; decision_prompt: string; total: number; priorities: PriorityItem[] };
  const [priorities, setPriorities] = useState<PrioritiesData | null>(null);

  useEffect(() => {
    const now = new Date();
    const mood = getMoodForTime(now);
    setGreeting(getGreetingForTime(now, "Dr. Agyeman"));
    setMoodText(describeMood(mood));
  }, []);

  useEffect(() => {
    async function loadTimeline() {
      try {
        setLoadingTimeline(true);
        const res = await fetch("/api/jarvis/timeline");
        const data = await res.json();
        if (Array.isArray(data)) {
          setTimeline(data);
        } else {
          setTimeline(null);
        }
      } catch (err) {
        console.error("Failed to load timeline", err);
        setTimeline(null);
      } finally {
        setLoadingTimeline(false);
      }
    }

    async function loadPersonal() {
      try {
        setLoadingPersonal(true);
        const res = await fetch("/api/jarvis/personal");
        const data = (await res.json()) as PersonalSnapshot;
        setPersonal(data);
      } catch (err) {
        console.error("Failed to load personal snapshot", err);
        setPersonal(null);
      } finally {
        setLoadingPersonal(false);
      }
    }

    async function loadPriorities() {
      try {
        const res = await fetch("/api/jarvis/priorities");
        if (res.ok) {
          const data = await res.json();
          if (data.ok && data.data?.total > 0) setPriorities(data.data);
        }
      } catch {
        // non-critical — priorities panel stays hidden
      }
    }

    loadTimeline();
    loadPersonal();
    loadPriorities();
  }, []);

  const bgClass =
    skin === "purple"
      ? "bg-gradient-to-br from-purple-900 via-indigo-900 to-black"
      : skin === "black-gold"
      ? "bg-gradient-to-br from-black via-neutral-950 to-stone-950"
      : "bg-slate-950";

  const titleClass =
    skin === "purple"
      ? "text-violet-200"
      : skin === "black-gold"
      ? "text-[#ffea9d]"
      : "text-slate-200";

  const subtitleClass =
    skin === "purple"
      ? "text-violet-300"
      : skin === "black-gold"
      ? "text-[#bba666]"
      : "text-slate-400";

  const bubbleClass =
    skin === "purple"
      ? "bg-gradient-to-br from-violet-700/40 to-fuchsia-700/30 border border-violet-700/40 text-violet-50"
      : skin === "black-gold"
      ? "bg-gradient-to-br from-black/60 to-neutral-900/40 border border-[#6d580f] text-[#f5d56f]"
      : "bg-slate-800 border border-slate-700 text-slate-200";

  const cardClass =
    skin === "purple"
      ? "rounded-2xl border border-purple-800/70 bg-black/60 backdrop-blur-lg"
      : skin === "black-gold"
      ? "rounded-2xl border border-[#3a2f10] bg-black/75 backdrop-blur-lg"
      : "rounded-2xl border border-slate-800 bg-slate-950/80 backdrop-blur";

  const cardTitleClass =
    skin === "purple"
      ? "text-sm font-semibold text-violet-100"
      : skin === "black-gold"
      ? "text-sm font-semibold text-[#ffea9d]"
      : "text-sm font-semibold text-slate-100";

  const cardTextMutedClass =
    skin === "purple"
      ? "text-xs text-violet-300"
      : skin === "black-gold"
      ? "text-xs text-[#bba666]"
      : "text-xs text-slate-400";

  async function handleQuickAction(action: QuickAction) {
    setStatusMessage(`${action.label}…`);

    try {
      // If the action has a direct backend API endpoint, call it
      if (action.directApi) {
        const { url, method, body } = action.directApi;
        const fetchOpts: RequestInit = {
          method,
          headers: { "Content-Type": "application/json" },
        };
        if (method === "POST" && body) {
          fetchOpts.body = JSON.stringify(body);
        }
        const apiRes = await fetch(url, fetchOpts);
        if (!apiRes.ok) {
          const errText = await apiRes.text();
          setStatusMessage(`Error: ${errText.slice(0, 120)}`);
        } else {
          const data = await apiRes.json();
          // Extract a useful summary string from the response
          const summary =
            data.description ||
            data.text ||
            data.message ||
            (data.cpu_percent !== undefined
              ? `CPU: ${data.cpu_percent}% | RAM: ${data.ram_percent}% | Disk: ${data.disk_percent}%`
              : null) ||
            (Array.isArray(data.results) && data.results.length > 0
              ? `Found ${data.results.length} results. Top: ${data.results[0]?.title ?? ""}`
              : null) ||
            (data.state
              ? `Voice pipeline: ${data.state}`
              : null) ||
            JSON.stringify(data).slice(0, 120);
          setStatusMessage(String(summary));
        }
      } else {
        // Default: send as a natural-language command to JARVIS
        const res = await sendJarvisCommand({
          command: action.cmd,
          metadata: {
            naturalLanguage: action.naturalLanguage,
            source: "home-quick-action",
            workspace: activeWorkspace,
          },
        });
        setStatusMessage(res.reply || `Jarvis processed: ${action.label}`);
      }
    } catch (err) {
      setStatusMessage(
        `Failed: ${err instanceof Error ? err.message : String(err)}`
      );
    }

    setTimeout(() => setStatusMessage(null), 8000);
  }

  const tasks =
    personal?.tasks && personal.tasks.length > 0
      ? personal.tasks.map((t) => t.title)
      : [
          "Review high-level priorities for the week.",
          "Clarify next steps for GLP pipeline.",
          "Pick one creative task for 'future you'.",
        ];

  return (
    <Shell>
      <div data-testid="app-root" className={`min-h-full w-full ${bgClass} rounded-3xl p-6 lg:p-8`}>
        <div className="mx-auto flex max-w-6xl flex-col gap-8 lg:gap-10">
          {/* Hero Section */}
          <section className="flex flex-col items-center gap-6 text-center lg:flex-row lg:items-center lg:justify-between lg:text-left">
            {/* Avatar + Title */}
            <div className="flex flex-col items-center gap-4 lg:flex-row lg:items-center">
              <div className="relative">
                {/* Glow */}
                <div
                  className={`
                    absolute inset-0 rounded-full blur-2xl
                    ${
                      skin === "purple"
                        ? "bg-gradient-to-br from-fuchsia-500 via-violet-500 to-indigo-500 opacity-60"
                        : skin === "black-gold"
                        ? "bg-gradient-to-br from-yellow-600 via-amber-500 to-orange-500 opacity-40"
                        : "bg-slate-400 opacity-40"
                    }
                  `}
                />
                {/* Avatar */}
                <div className="relative h-28 w-28 animate-pulse rounded-full border border-white/10 bg-black/60 shadow-2xl backdrop-blur flex items-center justify-center overflow-hidden lg:h-32 lg:w-32">
                  <div
                    className={`
                      absolute inset-0 blur-xl
                      ${
                        skin === "purple"
                          ? "bg-gradient-to-br from-purple-400 via-pink-400 to-indigo-400 opacity-30"
                          : skin === "black-gold"
                          ? "bg-gradient-to-br from-yellow-400 via-amber-400 to-orange-300 opacity-30"
                          : "bg-slate-300 opacity-20"
                      }
                    `}
                  />
                  <span className="relative z-10 text-4xl lg:text-5xl">
                    🤖
                  </span>
                </div>
              </div>

              <div className="mt-4 lg:mt-0 lg:ml-4">
                <h1
                  className={`text-2xl font-bold tracking-wide lg:text-3xl ${titleClass}`}
                >
                  Your Personal AI Chief of Staff
                </h1>
                <p className={`mt-1 text-xs ${subtitleClass}`}>
                  Online • Guam (ChST)
                </p>
                <p className={`mt-3 text-sm ${subtitleClass}`}>
                  {greeting} Jarvis is currently{" "}
                  <span className="font-semibold">
                    {moodText}
                  </span>
                </p>
              </div>
            </div>

            {/* Quick link to console */}
            <div className="mt-2 lg:mt-0">
              <Link
                href="/jarvis/console"
                className={`
                  inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold shadow-lg transition-all
                  ${
                    skin === "purple"
                      ? "bg-violet-600 hover:bg-violet-500 text-slate-100"
                      : skin === "black-gold"
                      ? "bg-[#c9a646] text-black hover:bg-[#f5d56f]"
                      : "bg-emerald-500 hover:bg-emerald-400 text-slate-900"
                  }
                `}
              >
                Open Command Console
                <span>↗</span>
              </Link>
            </div>
          </section>

          {/* Quick Actions */}
          <section>
            <h2 className={cardTitleClass}>Quick actions</h2>
            <p className={cardTextMutedClass}>
              Tap a card and Jarvis will route the right command to your backend
              for the{" "}
              <span className="font-semibold">{workspace.label}</span>{" "}
              workspace.
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-3 lg:justify-start">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleQuickAction(action)}
                  className={`
                    ${bubbleClass}
                    rounded-xl px-4 py-3 text-xs font-medium shadow-lg
                    hover:-translate-y-0.5 hover:shadow-2xl
                    active:translate-y-0
                    transition-transform transition-shadow duration-200
                    flex items-center gap-2
                  `}
                >
                  <span>●</span>
                  <span>{action.label}</span>
                </button>
              ))}
            </div>
            {statusMessage && (
              <div className="mt-3 text-xs text-emerald-300">
                {statusMessage}
              </div>
            )}
          </section>

          {/* Competing Priorities Panel — only renders when there's something due */}
          {priorities && priorities.total > 0 && (
            <section className={`${cardClass} p-4`}>
              <div className="flex items-center justify-between">
                <h3 className={cardTitleClass}>Competing right now</h3>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                  skin === "black-gold" ? "bg-amber-900/40 text-amber-300" : "bg-rose-900/40 text-rose-300"
                }`}>{priorities.total} items</span>
              </div>
              <p className={`mt-2 text-xs ${subtitleClass}`}>{priorities.summary}</p>
              <ul className="mt-3 space-y-2">
                {priorities.priorities.slice(0, 4).map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs">
                    <span className={`mt-0.5 shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                      p.urgency === "critical" || p.urgency === "high"
                        ? "bg-rose-900/50 text-rose-300"
                        : "bg-amber-900/30 text-amber-400"
                    }`}>{p.urgency}</span>
                    <span className="text-slate-200 leading-snug">{p.title}</span>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleQuickAction({
                  label: "What should I focus on?",
                  cmd: "priorities",
                  naturalLanguage: "What are my competing priorities right now? Help me decide what to focus on.",
                })}
                className={`mt-4 w-full rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
                  skin === "black-gold"
                    ? "bg-amber-700/30 hover:bg-amber-700/50 text-amber-200"
                    : "bg-violet-700/30 hover:bg-violet-700/50 text-violet-200"
                }`}
              >
                Help me decide →
              </button>
            </section>
          )}

          {/* Lower Grid: Timeline + Personal Data + Workspaces */}
          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {/* Timeline */}
            <div className={`${cardClass} p-4`}>
              <div className="flex items-center justify-between">
                <h3 className={cardTitleClass}>Recent signals</h3>
                <span className={cardTextMutedClass}>Nexus · Jarvis</span>
              </div>
              <div className="mt-3 min-h-[4rem]">
                {loadingTimeline && (
                  <div className={cardTextMutedClass}>Loading timeline…</div>
                )}
                {!loadingTimeline && (!timeline || timeline.length === 0) && (
                  <div className={cardTextMutedClass}>
                    No recent signals yet. Once Nexus + Jarvis are wired in,
                    this feed will light up.
                  </div>
                )}
                {!loadingTimeline && timeline && timeline.length > 0 && (
                  <ul className="space-y-3">
                    {timeline.map((item) => (
                      <li key={item.id} className="text-xs">
                        <div className="flex items-center justify-between">
                          <span className={cardTextMutedClass}>
                            {new Date(item.time).toLocaleString()}
                          </span>
                          <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-wide">
                            {item.source}
                          </span>
                        </div>
                        <p className="mt-1 text-[11px] text-slate-100">
                          {item.text}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Personal Data Panel */}
            <div className={`${cardClass} p-4 space-y-3`}>
              <h3 className={cardTitleClass}>Right-now snapshot</h3>
              <p className={cardTextMutedClass}>
                Jarvis's at-a-glance view of your current environment.
              </p>

              <div className="mt-2 space-y-3 text-xs">
                <div>
                  <div className="text-[11px] uppercase tracking-wide opacity-70">
                    Weather
                  </div>
                  {loadingPersonal ? (
                    <div className={cardTextMutedClass}>Loading…</div>
                  ) : personal?.weather ? (
                    <>
                      <div className="mt-1 flex items-center justify-between">
                        <span>{personal.weather.location}</span>
                        <span>{personal.weather.temp}</span>
                      </div>
                      <div className={cardTextMutedClass}>
                        {personal.weather.summary}
                      </div>
                    </>
                  ) : (
                    <div className={cardTextMutedClass}>
                      No weather snapshot yet.
                    </div>
                  )}
                </div>

                <div className="border-t border-white/5 pt-2">
                  <div className="text-[11px] uppercase tracking-wide opacity-70">
                    Next anchor
                  </div>
                  {loadingPersonal ? (
                    <div className={cardTextMutedClass}>Loading…</div>
                  ) : personal?.nextEvent ? (
                    <>
                      <div className="mt-1 text-xs text-slate-100">
                        {new Date(
                          personal.nextEvent.start_time
                        ).toLocaleString()}
                      </div>
                      <div className={cardTextMutedClass}>
                        {personal.nextEvent.title}
                      </div>
                    </>
                  ) : (
                    <div className={cardTextMutedClass}>
                      No upcoming anchor found.
                    </div>
                  )}
                </div>

                <div className="border-t border-white/5 pt-2">
                  <div className="text-[11px] uppercase tracking-wide opacity-70">
                    Your top 3 right now
                  </div>
                  <ul className="mt-1 list-disc pl-4">
                    {tasks.map((t, idx) => (
                      <li key={idx} className="text-[11px] text-slate-100">
                        {t}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* OS Workspaces */}
            <div className={`${cardClass} p-4`}>
              <h3 className={cardTitleClass}>Workspaces</h3>
              <p className={cardTextMutedClass}>
                Switch mental desktops. Jarvis can adapt context per workspace.
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
                {WORKSPACES.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => setActiveWorkspace(ws.id)}
                    className={`
                      rounded-full px-3 py-1 text-[11px] font-medium
                      border transition-all
                      ${
                        ws.id === activeWorkspace
                          ? skin === "black-gold"
                            ? "border-[#ffea9d] bg-[#ffea9d]/10 text-[#ffea9d]"
                            : skin === "purple"
                            ? "border-violet-300 bg-violet-300/10 text-violet-100"
                            : "border-emerald-400 bg-emerald-400/10 text-emerald-300"
                          : "border-white/10 text-slate-200 hover:border-white/30"
                      }
                    `}
                  >
                    {ws.label}
                  </button>
                ))}
              </div>

              <div className="mt-4 text-xs text-slate-100">
                <div className="text-[11px] uppercase tracking-wide opacity-70">
                  Active desktop
                </div>
                <div className="mt-1 font-semibold">{workspace.label}</div>
                <div className={cardTextMutedClass}>
                  {workspace.description}
                </div>
                <div className="mt-2 text-[11px] text-slate-300">
                  Future: Jarvis will load different tools, dashboards, and
                  notification rules depending on which workspace is active.
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </Shell>
  );
}

