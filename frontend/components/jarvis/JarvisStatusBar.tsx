// components/jarvis/JarvisStatusBar.tsx

"use client";

import { useJarvisTheme } from "@/components/theme/JarvisThemeProvider";

export default function JarvisStatusBar() {
  const { skin } = useJarvisTheme();

  const containerClass =
    skin === "black-gold"
      ? "mt-2 flex items-center justify-between rounded-lg border border-[#3a2f10] bg-black/85 px-3 py-2 text-xs text-[#bba666] shadow"
      : skin === "purple"
      ? "mt-2 flex items-center justify-between rounded-lg border border-purple-800 bg-black/80 px-3 py-2 text-xs text-violet-300 shadow"
      : "mt-2 flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-400";

  return (
    <div className={containerClass}>
      <span>Mode: Orchestration · Stream: Idle</span>
      <span>Backend: Private (Local GPU)</span>
    </div>
  );
}

