// components/theme/JarvisThemeToggle.tsx

"use client";

import { useJarvisTheme, JarvisSkin } from "./JarvisThemeProvider";

const SKINS: { id: JarvisSkin; label: string }[] = [
  { id: "purple", label: "Jarvis OG" },
  { id: "black-gold", label: "Ops Console" },
  { id: "slate", label: "System" },
];

export default function JarvisThemeToggle() {
  const { skin, setSkin } = useJarvisTheme();

  return (
    <div className="flex items-center gap-1 rounded-full border border-slate-700 bg-slate-950/70 px-2 py-1 text-[10px]">
      {SKINS.map((s) => (
        <button
          key={s.id}
          type="button"
          onClick={() => setSkin(s.id)}
          className={[
            "rounded-full px-2 py-1 transition-colors",
            skin === s.id
              ? "bg-emerald-400 text-slate-950 font-semibold"
              : "text-slate-400 hover:text-slate-100",
          ].join(" ")}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}

