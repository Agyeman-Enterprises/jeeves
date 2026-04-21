"use client";

import { useRouter } from "next/navigation";
import Shell from "@/components/layout/Shell";

const DOMAINS = [
  {
    id: "medical",
    label: "Medical",
    icon: "⚕",
    description: "Clinical research, patient cases, lab protocols, functional medicine",
    agents: ["HealthcareAgent", "WellnessAgent", "WhoZonAgent"],
    color: "teal",
    projects: ["Thyroid case analysis", "Hormone research", "Functional medicine library"],
  },
  {
    id: "finance",
    label: "Finance",
    icon: "$",
    description: "Portfolio tracking, transactions, subscriptions, safety thresholds",
    agents: ["FinanceAgent"],
    color: "yellow",
    projects: ["Monthly P&L", "Subscription audit", "Revenue forecasting"],
  },
  {
    id: "marketing",
    label: "Marketing",
    icon: "◈",
    description: "Campaigns, content calendar, social media, SEO, ad performance",
    agents: ["MarketingAgent", "SocialMediaManagerAgent", "SEOEcommerceSpecialistAgent", "AdAIAgent"],
    color: "purple",
    projects: ["LinkedIn content calendar", "Ad campaign rotation", "SEO audit"],
  },
  {
    id: "sales",
    label: "Sales & BD",
    icon: "◎",
    description: "Lead generation, cold outreach, deal pipelines, partnerships",
    agents: ["SalesManagerAgent", "BusinessDevelopmentSpecialistAgent"],
    color: "orange",
    projects: ["Outreach sequences", "Partner pipeline", "Cold email templates"],
  },
  {
    id: "creative",
    label: "Creative",
    icon: "◉",
    description: "Copywriting, content production, studio projects, AI art",
    agents: ["CopywriterAgent", "ContentAgent"],
    color: "pink",
    projects: ["Podcast scripts", "Blog content", "Brand copy"],
  },
  {
    id: "data",
    label: "Data & AI",
    icon: "▦",
    description: "Analytics, forecasting, business intelligence, automation",
    agents: ["DataAnalystAgent", "SupervisorAgent"],
    color: "blue",
    projects: ["Portfolio dashboard", "Weekly analytics report", "Agent performance metrics"],
  },
  {
    id: "comms",
    label: "Communications",
    icon: "◫",
    description: "Email, calendar, tasks, Slack, WhatsApp coordination",
    agents: ["EmailAgent", "CalendarAgent", "TaskAgent", "CommunicationsAgent"],
    color: "indigo",
    projects: ["Email digest", "Calendar optimization", "Task prioritization"],
  },
  {
    id: "education",
    label: "Education",
    icon: "◌",
    description: "Course production, curriculum design, student support",
    agents: ["PersonalCoachAgent"],
    color: "emerald",
    projects: ["Course curriculum", "Student portal", "Learning pathways"],
  },
];

const COLOR_MAP: Record<string, { card: string; badge: string; icon: string }> = {
  teal:    { card: "border-teal-500/20 hover:border-teal-500/40",    badge: "bg-teal-500/10 text-teal-400",    icon: "text-teal-400" },
  yellow:  { card: "border-yellow-500/20 hover:border-yellow-500/40", badge: "bg-yellow-500/10 text-yellow-400", icon: "text-yellow-400" },
  purple:  { card: "border-purple-500/20 hover:border-purple-500/40", badge: "bg-purple-500/10 text-purple-400", icon: "text-purple-400" },
  orange:  { card: "border-orange-500/20 hover:border-orange-500/40", badge: "bg-orange-500/10 text-orange-400", icon: "text-orange-400" },
  pink:    { card: "border-pink-500/20 hover:border-pink-500/40",     badge: "bg-pink-500/10 text-pink-400",     icon: "text-pink-400" },
  blue:    { card: "border-blue-500/20 hover:border-blue-500/40",     badge: "bg-blue-500/10 text-blue-400",     icon: "text-blue-400" },
  indigo:  { card: "border-indigo-500/20 hover:border-indigo-500/40", badge: "bg-indigo-500/10 text-indigo-400", icon: "text-indigo-400" },
  emerald: { card: "border-emerald-500/20 hover:border-emerald-500/40", badge: "bg-emerald-500/10 text-emerald-400", icon: "text-emerald-400" },
};

export default function DomainsPage() {
  const router = useRouter();

  return (
    <Shell>
      <div className="flex h-full gap-6">
        <div className="flex-1 min-w-0">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-white">Domain Workspaces</h1>
            <p className="text-sm text-slate-400 mt-0.5">
              {DOMAINS.length} domains · each with dedicated agents and knowledge bases
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {DOMAINS.map((domain) => {
              const cls = COLOR_MAP[domain.color] ?? COLOR_MAP.emerald;
              return (
                <button
                  key={domain.id}
                  onClick={() => router.push(`/jarvis/domains/${domain.id}`)}
                  className={`rounded-lg border bg-slate-900/50 p-5 text-left transition-all hover:bg-slate-900 ${cls.card}`}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`text-2xl ${cls.icon}`}>{domain.icon}</span>
                    <div>
                      <h3 className="text-sm font-semibold text-white">{domain.label}</h3>
                      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${cls.badge}`}>
                        {domain.agents.length} agent{domain.agents.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed mb-3">
                    {domain.description}
                  </p>
                  <div className="space-y-1">
                    {domain.projects.slice(0, 2).map((p) => (
                      <div key={p} className="flex items-center gap-1.5 text-[11px] text-slate-600">
                        <span className="h-1 w-1 rounded-full bg-slate-700" />
                        {p}
                      </div>
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right panel */}
        <div className="w-64 shrink-0">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              All Domains
            </h3>
            <div className="space-y-1">
              {DOMAINS.map((d) => {
                const cls = COLOR_MAP[d.color] ?? COLOR_MAP.emerald;
                return (
                  <button
                    key={d.id}
                    onClick={() => router.push(`/jarvis/domains/${d.id}`)}
                    className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-slate-400 hover:bg-slate-800 transition-colors"
                  >
                    <span className={cls.icon}>{d.icon}</span>
                    {d.label}
                    <span className="ml-auto text-slate-700">{d.agents.length}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
