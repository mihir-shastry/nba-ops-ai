"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchStandings } from "@/lib/api";
import Link from "next/link";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function TeamsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["standings"],
    queryFn: fetchStandings,
  });

  if (isLoading) return <LoadingSkeleton rows={15} />;
  if (error) return <p className="text-court-red">Failed to load standings.</p>;

  const renderTable = (teams: any[], title: string) => (
    <div>
      <h2 className="text-lg font-bold mb-3">{title}</h2>
      <div className="overflow-hidden rounded-xl border border-court-border bg-court-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-court-border">
              {["#", "Team", "W", "L", "Win%", "GB"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-court-muted text-xs uppercase tracking-wider"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {teams.map((t) => (
              <tr
                key={t.abbreviation}
                className="border-b border-court-border hover:bg-white/5 cursor-pointer"
              >
                <td className="px-4 py-3 text-court-muted">{t.rank}</td>
                <td className="px-4 py-3 font-semibold">
                  <Link
                    href={`/teams/${t.abbreviation}`}
                    className="hover:text-court-gold transition-colors"
                  >
                    {t.team_name}
                  </Link>
                </td>
                <td className="px-4 py-3">{t.wins}</td>
                <td className="px-4 py-3">{t.losses}</td>
                <td className="px-4 py-3">{t.win_pct}</td>
                <td className="px-4 py-3 text-court-muted">{t.gb}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">Team Dashboard</h1>
      <p className="text-court-muted mb-6">
        Conference standings — click a team to see their profile
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {renderTable(data?.east || [], "Eastern Conference")}
        {renderTable(data?.west || [], "Western Conference")}
      </div>
    </div>
  );
}
