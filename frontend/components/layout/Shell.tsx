"use client";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { useJarvisWorkspace } from "@/components/jarvis/JarvisWorkspaceContext";

interface ShellProps {
  children: React.ReactNode;
}

export default function Shell({ children }: ShellProps) {
  const { activeWorkspace } = useJarvisWorkspace();

  return (
    <div className={`flex min-h-screen shell-container workspace-${activeWorkspace}`}>
      <Sidebar />
      <div className="flex flex-1 flex-col main-content">
        <Topbar />
        <main className="flex-1 overflow-y-auto bg-slate-900 px-6 py-4">
          {children}
        </main>
      </div>
    </div>
  );
}

