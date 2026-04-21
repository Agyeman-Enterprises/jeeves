// components/layout/Topbar.tsx

"use client";

import { useRouter } from "next/navigation";
import JarvisThemeToggle from "@/components/theme/JarvisThemeToggle";
import { useJarvisTheme } from "@/components/theme/JarvisThemeProvider";
import { useJarvisWorkspace, type WorkspaceId } from "@/components/jarvis/JarvisWorkspaceContext";
import { cn } from "@/lib/utils";

export default function Topbar() {
  const router = useRouter();
  const { skin } = useJarvisTheme();
  const { activeWorkspace, setActiveWorkspace } = useJarvisWorkspace();

  function switchWorkspace(ws: WorkspaceId) {
    setActiveWorkspace(ws);

    // workspace → route mapping
    const routes: Record<WorkspaceId, string> = {
      ops: "/jarvis/home",
      system: "/jarvis/console",
      creative: "/creative",
      financial: "/finance",
      playground: "/playground",
    };

    // navigate
    router.push(routes[ws] ?? "/jarvis/home");
  }

  const bgClass =
    skin === "purple"
      ? "bg-gradient-to-r from-purple-950/90 via-indigo-950/80 to-slate-950/90"
      : skin === "black-gold"
      ? "bg-gradient-to-r from-black via-neutral-950 to-stone-950"
      : "bg-slate-950/70";

  const buttonBaseClass = "px-3 py-1.5 rounded-md text-xs font-medium transition-colors";
  const buttonActiveClass =
    skin === "purple"
      ? "bg-violet-600 text-white"
      : skin === "black-gold"
      ? "bg-[#c9a646] text-black"
      : "bg-emerald-500 text-slate-950";
  const buttonIdleClass =
    skin === "purple"
      ? "bg-violet-950/50 text-violet-300 hover:bg-violet-900/70"
      : skin === "black-gold"
      ? "bg-black/50 text-[#bba666] hover:bg-black/70"
      : "bg-slate-800/50 text-slate-400 hover:bg-slate-800";

  return (
    <header
      className={`flex items-center justify-between border-b border-slate-800 px-6 py-3 backdrop-blur ${bgClass}`}
    >
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-lg font-semibold text-slate-100">
            Jarvis Command Center
          </h1>
          <p className="text-xs text-slate-300">
            Personal AI Chief of Staff · Orchestrating your clinics, games, and life.
          </p>
        </div>

        <div className="flex items-center gap-1 border-l border-slate-700 pl-4">
          <button
            className={cn(buttonBaseClass, activeWorkspace === "ops" ? buttonActiveClass : buttonIdleClass)}
            onClick={() => switchWorkspace("ops")}
          >
            Ops
          </button>
          <button
            className={cn(buttonBaseClass, activeWorkspace === "system" ? buttonActiveClass : buttonIdleClass)}
            onClick={() => switchWorkspace("system")}
          >
            System
          </button>
          <button
            className={cn(buttonBaseClass, activeWorkspace === "creative" ? buttonActiveClass : buttonIdleClass)}
            onClick={() => switchWorkspace("creative")}
          >
            Creative
          </button>
          <button
            className={cn(buttonBaseClass, activeWorkspace === "financial" ? buttonActiveClass : buttonIdleClass)}
            onClick={() => switchWorkspace("financial")}
          >
            Money
          </button>
          <button
            className={cn(buttonBaseClass, activeWorkspace === "playground" ? buttonActiveClass : buttonIdleClass)}
            onClick={() => switchWorkspace("playground")}
          >
            Lab
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-300">
        <span className="rounded-full bg-emerald-500/20 px-2 py-1 text-emerald-300">
          Online · Guam (ChST)
        </span>
        <JarvisThemeToggle />
      </div>
    </header>
  );
}

