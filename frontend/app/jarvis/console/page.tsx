// app/jarvis/console/page.tsx

import Shell from "@/components/layout/Shell";
import JarvisConsole from "@/components/jarvis/JarvisConsole";
import JarvisContextPanel from "@/components/jarvis/JarvisContextPanel";
import JarvisToolsPanel from "@/components/jarvis/JarvisToolsPanel";
import JarvisStatusBar from "@/components/jarvis/JarvisStatusBar";

export default function JarvisConsolePage() {
  return (
    <Shell>
      <div className="flex h-full flex-col gap-3">
        <div className="grid flex-1 gap-3 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
          <div className="flex flex-col gap-3">
            <JarvisConsole />
            <JarvisStatusBar />
          </div>
          <div className="grid grid-rows-[minmax(0,1fr)_minmax(0,1fr)] gap-3">
            <JarvisContextPanel />
            <JarvisToolsPanel />
          </div>
        </div>
      </div>
    </Shell>
  );
}

