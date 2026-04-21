import Shell from "@/components/layout/Shell";

export default function AccessMDPage() {
  return (
    <Shell>
      <div className="p-6 text-slate-200 space-y-2">
        <h1 className="text-3xl font-bold">AccessMD Operations</h1>
        <p className="text-slate-400">
          This panel will orchestrate GLP workflows, telehealth sessions, and patient routing.
        </p>
      </div>
    </Shell>
  );
}

