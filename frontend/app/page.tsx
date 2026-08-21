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
  { href: "/sql", label: "SQL Analytics", desc: "Query NBA data with SQL", icon: Database, color: "from-blue-500 to-blue-600" },
  { href: "/shots", label: "Shot Charts", desc: "Visualize shot locations", icon: Target, color: "from-green-500 to-green-600" },
  { href: "/teams", label: "Teams", desc: "Standings and team profiles", icon: Trophy, color: "from-yellow-500 to-yellow-600" },
  { href: "/games", label: "Games", desc: "Browse game results", icon: Calendar, color: "from-purple-500 to-purple-600" },
  { href: "/ratings", label: "Ratings", desc: "Player ratings (0-100)", icon: Star, color: "from-court-gold to-yellow-500" },
  { href: "/compare", label: "Compare", desc: "Player vs player", icon: GitCompare, color: "from-court-orange to-orange-600" },
  { href: "/matches", label: "Matches", desc: "Game box scores", icon: LayoutGrid, color: "from-red-500 to-red-600" },
  { href: "/lineups", label: "Lineups", desc: "5-man unit stats", icon: Wrench, color: "from-teal-500 to-teal-600" },
  { href: "/chat", label: "AI Assistant", desc: "Ask questions in natural language", icon: MessageSquare, color: "from-pink-500 to-pink-600" },
];

export default function Home() {
  return (
    <div className="py-12">
      {/* Hero */}
      <div className="text-center mb-16">
        <h1 className="text-6xl font-extrabold bg-gradient-to-r from-court-orange via-court-gold to-court-orange bg-clip-text text-transparent mb-4">
          NBA Operations AI
        </h1>
        <p className="text-court-muted text-xl max-w-2xl mx-auto">
          SQL Analytics • Shot Charts • Teams • Games • Ratings • Compare • Matches • AI Assistant
        </p>
        <div className="flex justify-center gap-2 mt-6">
          {["Python", "FastAPI", "Next.js", "SQLite", "Gemini AI", "Recharts"].map(
            (tech) => (
              <span
                key={tech}
                className="px-3 py-1 bg-court-card border border-court-border rounded-full text-xs text-court-muted"
              >
                {tech}
              </span>
            )
          )}
        </div>
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {features.map((f) => {
          const Icon = f.icon;
          return (
            <Link
              key={f.href}
              href={f.href}
              className="bg-court-card border border-court-border rounded-xl p-6 hover:bg-white/5 transition-all hover:-translate-y-1 hover:shadow-lg hover:shadow-court-orange/5 group"
            >
              <div
                className={`w-10 h-10 rounded-lg bg-gradient-to-br ${f.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}
              >
                <Icon size={20} className="text-white" />
              </div>
              <h3 className="font-bold mb-1">{f.label}</h3>
              <p className="text-sm text-court-muted">{f.desc}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
