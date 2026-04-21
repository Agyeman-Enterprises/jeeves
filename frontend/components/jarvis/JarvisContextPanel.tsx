// components/jarvis/JarvisContextPanel.tsx

"use client";

import { useJarvisTheme } from "@/components/theme/JarvisThemeProvider";

export default function JarvisContextPanel() {
  const { skin } = useJarvisTheme();

  const containerClass =
    skin === "black-gold"
      ? "rounded-xl border border-[#3a2f10] bg-black/85 p-4 text-sm text-[#f5d56f] shadow-lg"
      : skin === "purple"
      ? "rounded-xl border border-purple-800 bg-gradient-to-br from-purple-950/90 via-indigo-950/80 to-black p-4 text-sm text-violet-100 shadow-lg"
      : "rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-sm text-slate-200";

  const titleClass =
    skin === "black-gold"
      ? "mb-2 text-sm font-semibold text-[#ffea9d]"
      : skin === "purple"
      ? "mb-2 text-sm font-semibold text-violet-100"
      : "mb-2 text-sm font-semibold text-slate-200";

  const mutedClass =
    skin === "black-gold"
      ? "text-xs text-[#bba666]"
      : skin === "purple"
      ? "text-xs text-violet-300"
      : "text-xs text-slate-400";

  return (
    <section className={containerClass}>
      <h2 className={titleClass}>Context / Memory State</h2>
      <p className={mutedClass}>
        Real-time awareness Jarvis uses to interpret your commands.
      </p>
      <ul className="mt-3 space-y-1 text-xs">
        <li>• Active Project: Next.js Jarvis OS Rebuild</li>
        <li>• Backend: THE BEAST / ROG (local compute)</li>
        <li>• Ecosystems: AccessMD · MedRx · Nexus · Purrkoin</li>
      </ul>
    </section>
  );
}

