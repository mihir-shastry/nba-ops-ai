"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  Activity,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Home", icon: Activity },
  { href: "/sql", label: "SQL Analytics", icon: Database },
  { href: "/shots", label: "Shot Charts", icon: Target },
  { href: "/teams", label: "Teams", icon: Trophy },
  { href: "/games", label: "Games", icon: Calendar },
  { href: "/ratings", label: "Ratings", icon: Star },
  { href: "/compare", label: "Compare", icon: GitCompare },
  { href: "/matches", label: "Matches", icon: LayoutGrid },
  { href: "/lineups", label: "Lineups", icon: Wrench },
  { href: "/chat", label: "AI Assistant", icon: MessageSquare },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 min-h-screen bg-court-card border-r border-court-border p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-extrabold bg-gradient-to-r from-court-orange to-court-gold bg-clip-text text-transparent">
          🏀 NBA Ops AI
        </h1>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-gradient-to-r from-court-orange to-court-gold text-court-bg"
                  : "text-court-muted hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-8 text-xs text-court-muted">
        <p>Python • FastAPI • Next.js</p>
        <p>SQLite • Gemini AI • Recharts</p>
      </div>
    </aside>
  );
}
