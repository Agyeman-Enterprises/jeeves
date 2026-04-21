"use client";

import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useJarvisWorkspace, type WorkspaceId } from "@/components/jarvis/JarvisWorkspaceContext";

type NavSection = {
  label: string;
  items: { href: string; label: string; icon: string; workspace: WorkspaceId }[];
};

const navSections: NavSection[] = [
  {
    label: "Command",
    items: [
      { href: "/jarvis/home",     label: "Dashboard",      icon: "⬡", workspace: "ops" },
      { href: "/jarvis/briefing", label: "Daily Briefing", icon: "◈", workspace: "ops" },
      { href: "/jarvis/jobs",     label: "Jobs",           icon: "◎", workspace: "ops" },
      { href: "/jarvis/console",  label: "Console",        icon: "▸", workspace: "system" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { href: "/jarvis/agents",    label: "Agents",         icon: "◈", workspace: "ops" },
      { href: "/jarvis/domains",   label: "Domains",        icon: "◫", workspace: "ops" },
      { href: "/jarvis/workflows", label: "Workflows",      icon: "⇢", workspace: "ops" },
      { href: "/jarvis/knowledge", label: "Knowledge",      icon: "◉", workspace: "ops" },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/nexus",              label: "Nexus",          icon: "◈", workspace: "ops" },
      { href: "/jarvis/analytics",   label: "Analytics",      icon: "▦", workspace: "ops" },
      { href: "/jarvis/memory",      label: "Memory Graph",   icon: "◌", workspace: "ops" },
      { href: "/jarvis/settings",    label: "Settings",       icon: "◧", workspace: "system" },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { setActiveWorkspace } = useJarvisWorkspace();

  function navigateTo(path: string, workspace: WorkspaceId) {
    setActiveWorkspace(workspace);
    router.push(path);
  }

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-slate-800/60 bg-slate-950">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-800/60">
        <div className="h-7 w-7 rounded-md bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-xs font-bold text-slate-900">
          J
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold tracking-wide text-white">JARVIS OS</span>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest">AI Operating System</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex flex-1 flex-col gap-4 overflow-y-auto px-3 py-4">
        {navSections.map((section) => (
          <div key={section.label}>
            <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
              {section.label}
            </p>
            <div className="flex flex-col gap-0.5">
              {section.items.map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <button
                    key={item.href}
                    onClick={() => navigateTo(item.href, item.workspace)}
                    className={cn(
                      "flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-left text-sm transition-colors",
                      active
                        ? "bg-emerald-500/10 text-emerald-300 font-medium"
                        : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                    )}
                  >
                    <span className={cn("text-base leading-none", active ? "text-emerald-400" : "text-slate-600")}>
                      {item.icon}
                    </span>
                    {item.label}
                    {active && (
                      <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-800/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] text-slate-500">aaa-srv · port 8001</span>
        </div>
      </div>
    </aside>
  );
}

