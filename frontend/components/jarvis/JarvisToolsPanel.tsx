// components/jarvis/JarvisToolsPanel.tsx

"use client";

import Link from "next/link";
import { useJarvisTheme } from "@/components/theme/JarvisThemeProvider";

const tools = [
  { name: "Nexus", description: "Business + clinic analytics engine.", href: "/nexus" },
  { name: "AccessMD", description: "Telehealth + GLP operations.", href: "/accessmd" },
  { name: "Purrkoin", description: "Crypto + economy control panel.", href: "/purrkoin" },
  { name: "Election Empire", description: "Game-world orchestration layer.", href: "/election" },
];

export default function JarvisToolsPanel() {
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

  const subClass =
    skin === "black-gold"
      ? "text-xs text-[#bba666]"
      : skin === "purple"
      ? "text-xs text-violet-300"
      : "text-xs text-slate-400";

  const cardClass =
    skin === "black-gold"
      ? "rounded-lg border border-[#6d580f] bg-black/90 px-3 py-2 shadow"
      : skin === "purple"
      ? "rounded-lg border border-purple-700 bg-black/80 px-3 py-2 shadow"
      : "rounded-lg border border-slate-800 bg-slate-900 px-3 py-2";

  const nameClass =
    skin === "black-gold"
      ? "font-semibold text-[#ffea9d]"
      : skin === "purple"
      ? "font-semibold text-violet-100"
      : "font-semibold text-slate-100";

  const descClass =
    skin === "black-gold"
      ? "text-[#bba666]"
      : skin === "purple"
      ? "text-violet-300"
      : "text-slate-400";

  return (
    <section className={containerClass}>
      <h2 className={titleClass}>Connected Systems</h2>
      <p className={subClass}>
        Jarvis can route commands through these meta-API modules.
      </p>

      <div className="mt-3 grid grid-cols-1 gap-2 text-xs sm:grid-cols-2">
        {tools.map((tool) => (
          <Link key={tool.name} href={tool.href}>
            <div className={`${cardClass} cursor-pointer transition-all hover:scale-105 hover:shadow-lg`}>
              <div className={nameClass}>{tool.name}</div>
              <div className={descClass}>{tool.description}</div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

