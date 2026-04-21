// components/theme/JarvisThemeProvider.tsx

"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export type JarvisSkin = "purple" | "black-gold" | "slate";

type JarvisThemeContextValue = {
  skin: JarvisSkin;
  setSkin: (skin: JarvisSkin) => void;
};

const JarvisThemeContext = createContext<JarvisThemeContextValue | undefined>(
  undefined
);

const STORAGE_KEY = "jarvis-skin";

export function JarvisThemeProvider({ children }: { children: React.ReactNode }) {
  const [skin, setSkinState] = useState<JarvisSkin>("purple");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(STORAGE_KEY) as JarvisSkin | null;
    if (stored === "purple" || stored === "black-gold" || stored === "slate") {
      setSkinState(stored);
    }
  }, []);

  const setSkin = (next: JarvisSkin) => {
    setSkinState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, next);
    }
  };

  return (
    <JarvisThemeContext.Provider value={{ skin, setSkin }}>
      {/* data attribute makes it easy to theme via CSS if needed */}
      <div data-jarvis-skin={skin} className="min-h-screen">
        {children}
      </div>
    </JarvisThemeContext.Provider>
  );
}

export function useJarvisTheme(): JarvisThemeContextValue {
  const ctx = useContext(JarvisThemeContext);
  if (!ctx) {
    throw new Error("useJarvisTheme must be used within JarvisThemeProvider");
  }
  return ctx;
}

