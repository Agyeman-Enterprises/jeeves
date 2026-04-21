import Shell from "@/components/layout/Shell";

export default function PurrkoinPage() {
  return (
    <Shell>
      <div className="p-6 text-slate-200 space-y-2">
        <h1 className="text-3xl font-bold">Purrkoin Economy Dashboard</h1>
        <p className="text-slate-400">
          Track token supply, in-game usage, and meme-economy health here.
        </p>
      </div>
    </Shell>
  );
}

