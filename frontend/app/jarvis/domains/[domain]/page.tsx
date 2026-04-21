"use client";

import { useParams, useRouter } from "next/navigation";
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

const COLOR_MAP: Record<string, { border: string; badge: string; icon: string; dot: string }> = {
  teal:    { border: "border-teal-500/30",    badge: "bg-teal-500/10 text-teal-300",    icon: "text-teal-400",    dot: "bg-teal-500" },
  yellow:  { border: "border-yellow-500/30",  badge: "bg-yellow-500/10 text-yellow-300", icon: "text-yellow-400", dot: "bg-yellow-500" },
  purple:  { border: "border-purple-500/30",  badge: "bg-purple-500/10 text-purple-300", icon: "text-purple-400", dot: "bg-purple-500" },
  orange:  { border: "border-orange-500/30",  badge: "bg-orange-500/10 text-orange-300", icon: "text-orange-400", dot: "bg-orange-500" },
  pink:    { border: "border-pink-500/30",    badge: "bg-pink-500/10 text-pink-300",    icon: "text-pink-400",    dot: "bg-pink-500" },
  blue:    { border: "border-blue-500/30",    badge: "bg-blue-500/10 text-blue-300",    icon: "text-blue-400",    dot: "bg-blue-500" },
  indigo:  { border: "border-indigo-500/30",  badge: "bg-indigo-500/10 text-indigo-300", icon: "text-indigo-400", dot: "bg-indigo-500" },
  emerald: { border: "border-emerald-500/30", badge: "bg-emerald-500/10 text-emerald-300", icon: "text-emerald-400", dot: "bg-emerald-500" },
};

export default function DomainDetailPage() {
  const { domain: domainId } = useParams<{ domain: string }>();
  const router = useRouter();

  const domain = DOMAINS.find((d) => d.id === domainId);

  if (!domain) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <p className="text-slate-400">Domain &quot;{domainId}&quot; not found.</p>
          <button
            onClick={() => router.push("/jarvis/domains")}
            className="text-sm text-emerald-400 hover:text-emerald-300 underline"
          >
            ← Back to Domains
          </button>
        </div>
      </Shell>
    );
  }

  const cls = COLOR_MAP[domain.color] ?? COLOR_MAP.emerald;

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/jarvis/domains")}
              className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
              data-testid="back-to-domains"
            >
              ← Domains
            </button>
            <span className="text-slate-700">/</span>
            <div className="flex items-center gap-3">
              <span className={`text-3xl ${cls.icon}`}>{domain.icon}</span>
              <div>
                <h1 className="text-xl font-semibold text-white">{domain.label}</h1>
                <p className="text-sm text-slate-400 mt-0.5">{domain.description}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Agents */}
          <div className={`rounded-lg border ${cls.border} bg-slate-900/50 p-5`}>
            <h2 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">
              Agents ({domain.agents.length})
            </h2>
            <ul className="space-y-2">
              {domain.agents.map((agent) => (
                <li key={agent} className="flex items-center gap-3 text-sm text-slate-300">
                  <span className={`h-2 w-2 rounded-full ${cls.dot}`} />
                  {agent}
                  <span className="ml-auto text-xs text-slate-600">idle</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Projects */}
          <div className={`rounded-lg border ${cls.border} bg-slate-900/50 p-5`}>
            <h2 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">
              Active Projects ({domain.projects.length})
            </h2>
            <ul className="space-y-2">
              {domain.projects.map((project) => (
                <li key={project} className="flex items-center gap-3 text-sm text-slate-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
                  {project}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Shell>
  );
}
