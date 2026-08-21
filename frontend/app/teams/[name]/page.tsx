"use client";

import { useQuery } from "@tanstack/react-query";
import { use } from "react";
import { fetchTeamOverview } from "@/lib/api";
import { formatPct } from "@/lib/utils";
import StatCard from "@/components/StatCard";
import Link from "next/link";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function TeamPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = use(params);
  const { data, isLoading, error } = useQuery({
    queryKey: ["team", name],
    queryFn: () => fetchTeamOverview(name),
  });

  if (isLoading) return <LoadingSkeleton rows={10} />;
  if (error || !data) return <p className="text-court-red">Team not found.</p>;

  const { team, core_stats, advanced_metrics, recent_form, roster } = data;

  return (
    <div>
      <Link
        href="/teams"
        className="text-court-muted hover:text-court-gold text-sm mb-4 inline-block"
      >
        ← Back to Standings
      </Link>

      <h1 className="text-3xl font-extrabold mb-1">{team.team_name}</h1>
      <p className="text-court-muted mb-6">Record: {team.record}</p>

      <h2 className="text-lg font-bold mb-3">Core Stats</h2>
      <div className="grid grid-cols-5 gap-4 mb-8">
        <StatCard label="PPG" value={core_stats.ppg.toFixed(1)} />
        <StatCard label="RPG" value={core_stats.rpg.toFixed(1)} />
        <StatCard label="APG" value={core_stats.apg.toFixed(1)} />
        <StatCard label="FG%" value={`${core_stats.fg_pct.toFixed(1)}%`} />
        <StatCard
          label="3PT%"
          value={`${core_stats.three_pct.toFixed(1)}%`}
        />
      </div>

      {advanced_metrics && (
        <>
          <h2 className="text-lg font-bold mb-3">Advanced Metrics</h2>
          <div className="grid grid-cols-5 gap-4 mb-8">
            <StatCard
              label="Off Rating"
              value={advanced_metrics.offensive_rating ?? "N/A"}
            />
            <StatCard
              label="Def Rating"
              value={advanced_metrics.defensive_rating ?? "N/A"}
            />
            <StatCard
              label="Net Rating"
              value={advanced_metrics.net_rating ?? "N/A"}
            />
            <StatCard label="Pace" value={advanced_metrics.pace ?? "N/A"} />
            <StatCard
              label="TS%"
              value={
                advanced_metrics.ts_pct
                  ? `${advanced_metrics.ts_pct}%`
                  : "N/A"
              }
            />
          </div>
        </>
      )}

      <h2 className="text-lg font-bold mb-3">Recent Form (Last 10)</h2>
      <div className="flex gap-2 mb-8">
        {recent_form.map((g: any, i: number) => (
          <div
            key={i}
            className={`text-center px-3 py-2 rounded-lg border ${
              g.result === "W"
                ? "bg-court-green/10 border-court-green/30"
                : "bg-court-red/10 border-court-red/30"
            }`}
          >
            <div
              className={`text-lg font-bold ${
                g.result === "W" ? "text-court-green" : "text-court-red"
              }`}
            >
              {g.result}
            </div>
            <div className="text-xs text-court-muted">{g.matchup}</div>
            <div className="text-xs text-court-muted">{g.points} pts</div>
          </div>
        ))}
      </div>

      {roster?.length > 0 && (
        <>
          <h2 className="text-lg font-bold mb-3">Top Players</h2>
          <div className="overflow-hidden rounded-xl border border-court-border bg-court-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-court-border">
                  {["Player", "PPG", "RPG", "APG", "FG%"].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-court-muted text-xs uppercase"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {roster.map((p: any, i: number) => (
                  <tr key={i} className="border-b border-court-border">
                    <td className="px-4 py-3 font-semibold">
                      {p.player_name}
                    </td>
                    <td className="px-4 py-3">{p.points_per_game}</td>
                    <td className="px-4 py-3">{p.rebounds_per_game}</td>
                    <td className="px-4 py-3">{p.assists_per_game}</td>
                    <td className="px-4 py-3">{formatPct(p.field_goal_pct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
