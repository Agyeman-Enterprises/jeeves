// components/jarvis/JarvisWorkspaceContext.tsx

"use client";

import {
  createContext,
  useContext,
  useState,
  useMemo,
  ReactNode,
} from "react";

export type WorkspaceId = "ops" | "system" | "creative" | "financial" | "playground";

export type Workspace = {
  id: WorkspaceId;
  label: string;
  description: string;
};

export const WORKSPACES: Workspace[] = [
  {
    id: "ops",
    label: "Ops Desk",
    description: "Operations, triage, and immediate fires.",
  },
  {
    id: "system",
    label: "System Console",
    description: "Command console and system operations.",
  },
  {
    id: "creative",
    label: "Creative Studio",
    description: "Writing, world-building, and design.",
  },
  {
    id: "financial",
    label: "Money & Metrics",
    description: "Revenue, forecasts, and resource allocation.",
  },
  {
    id: "playground",
    label: "Playground",
    description: "Experiments, new tools, and random ideas.",
  },
];

type JarvisWorkspaceContextValue = {
  activeWorkspace: WorkspaceId;
  setActiveWorkspace: (id: WorkspaceId) => void;
  workspace: Workspace;
};

const JarvisWorkspaceContext =
  createContext<JarvisWorkspaceContextValue | null>(null);

export function JarvisWorkspaceProvider({ children }: { children: ReactNode }) {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>("ops");

  const value = useMemo(() => {
    const workspace =
      WORKSPACES.find((w) => w.id === activeWorkspace) ?? WORKSPACES[0];
    return { activeWorkspace, setActiveWorkspace, workspace };
  }, [activeWorkspace]);

  return (
    <JarvisWorkspaceContext.Provider value={value}>
      {children}
    </JarvisWorkspaceContext.Provider>
  );
}

export function useJarvisWorkspace() {
  const ctx = useContext(JarvisWorkspaceContext);
  if (!ctx) {
    throw new Error(
      "useJarvisWorkspace must be used within JarvisWorkspaceProvider"
    );
  }
  return ctx;
}

