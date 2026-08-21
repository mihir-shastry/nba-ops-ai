"use client";

import Link from "next/link";
import {
  Database,
  Target,
  Trophy,
  Calendar,
  Star,
  GitCompare,
  LayoutGrid,
  Wrench,
  MessageSquare,
} from "lucide-react";

const features = [
  { href: "/sql", label: "SQL Analytics", desc: "Query NBA data with SQL", icon: Database },
  { href: "/shots", label: "Shot Charts", desc: "Visualize shot locations", icon: Target },
  { href: "/teams", label: "Teams", desc: "Standings and team profiles", icon: Trophy },
  { href: "/games", label: "Games", desc: "Browse game results", icon: Calendar },
  { href: "/ratings", label: "Ratings", desc: "Player ratings (0-100)", icon: Star },
  { href: "/compare", label: "Compare", desc: "Player vs player", icon: GitCompare },
  { href: "/matches", label: "Matches", desc: "Game box scores", icon: LayoutGrid },
  { href: "/lineups", label: "Lineups", desc: "5-man unit stats", icon: Wrench },
  { href: "/chat", label: "AI Assistant", desc: "Ask questions in natural language", icon: MessageSquare },
];

export default function Home() {
  return (
    <div className="py-12">
      <div className="text-center mb-16">
        <h1 className="text-5xl font-extrabold tracking-tight mb-3">
          NBA Operations AI
        </h1>
        <p className="text-court-muted text-lg max-w-xl mx-auto">
          SQL Analytics • Shot Charts • Teams • Games • Ratings • Compare • Matches • AI Assistant
        </p>
        <div className="flex justify-center gap-2 mt-6">
          {["Python", "FastAPI", "Next.js", "SQLite", "Gemini AI", "Recharts"].map(
            (tech) => (
              <span
                key={tech}
                className="px-3 py-1 bg-court-card border border-court-border rounded text-xs text-court-muted"
              >
                {tech}
              </span>
            )
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {features.map((f) => {
          const Icon = f.icon;
          return (
            <Link
              key={f.href}
              href={f.href}
              className="bg-court-card border border-court-border rounded-lg p-5 hover:bg-white/[0.03] transition-colors group"
            >
              <div className="w-9 h-9 rounded-md bg-white/[0.06] flex items-center justify-center mb-3">
                <Icon size={18} className="text-court-muted group-hover:text-white transition-colors" />
              </div>
              <h3 className="font-semibold text-sm mb-0.5">{f.label}</h3>
              <p className="text-xs text-court-muted">{f.desc}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
