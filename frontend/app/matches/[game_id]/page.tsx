"use client";

import { useQuery } from "@tanstack/react-query";
import { use } from "react";
import { fetchMatchDetail } from "@/lib/api";
import Link from "next/link";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function MatchDetailPage({
  params,
}: {
  params: Promise<{ game_id: string }>;
}) {
  const { game_id } = use(params);
  const { data, isLoading, error } = useQuery({
    queryKey: ["matchDetail", game_id],
    queryFn: () => fetchMatchDetail(game_id),
  });

  if (isLoading) return <LoadingSkeleton rows={10} />;
  if (error || !data) return <p className="text-court-red">Game not found.</p>;

  const { game, home_team, away_team, player_stats } = data;

  const renderBoxScore = (team: any, stats: any[]) => (
    <div>
      <h3 className="text-lg font-bold mb-3">{team.abbreviation} Box Score</h3>
      <div className="overflow-auto rounded-xl border border-court-border bg-court-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-court-border">
              {["Player", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "Rating"].map(
                (h) => (
                  <th
                    key={h}
                    className="px-3 py-2 text-left text-court-muted text-xs uppercase"
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {stats.map((p: any, i: number) => (
              <tr key={i} className="border-b border-court-border last:border-0">
                <td className="px-3 py-2 font-semibold">{p.player_name}</td>
                <td className="px-3 py-2">{p.minutes}</td>
                <td className="px-3 py-2">{p.points}</td>
                <td className="px-3 py-2">{p.rebounds}</td>
                <td className="px-3 py-2">{p.assists}</td>
                <td className="px-3 py-2">{p.steals}</td>
                <td className="px-3 py-2">{p.blocks}</td>
                <td className="px-3 py-2">{p.turnovers}</td>
                <td className="px-3 py-2 text-court-gold font-bold">
                  {p.rating}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div>
      <Link
        href="/matches"
        className="text-court-muted hover:text-court-gold text-sm mb-4 inline-block"
      >
        ← Back to matches
      </Link>

      {/* Scoreboard */}
      <div className="bg-court-card border border-court-border rounded-xl p-8 mb-8">
        <div className="grid grid-cols-3 items-center gap-8">
          <div className="text-center">
            <div
              className={`text-5xl font-extrabold ${
                home_team.result === "W" ? "text-court-green" : "text-court-red"
              }`}
            >
              {home_team.points}
            </div>
            <div className="text-xl font-bold mt-2">{home_team.abbreviation}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl text-court-muted">vs</div>
            <div className="text-sm text-court-muted mt-2">{game.date}</div>
          </div>
          <div className="text-center">
            <div
              className={`text-5xl font-extrabold ${
                away_team.result === "W" ? "text-court-green" : "text-court-red"
              }`}
            >
              {away_team.points}
            </div>
            <div className="text-xl font-bold mt-2">{away_team.abbreviation}</div>
          </div>
        </div>
      </div>

      {/* Team Stats Comparison */}
      <h2 className="text-lg font-bold mb-4">Team Stats</h2>
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "REB", home: home_team.rebounds, away: away_team.rebounds },
          { label: "AST", home: home_team.assists, away: away_team.assists },
          { label: "FG%", home: `${home_team.fg_pct}%`, away: `${away_team.fg_pct}%` },
          { label: "+/-", home: home_team.plus_minus, away: away_team.plus_minus },
        ].map((s) => (
          <div
            key={s.label}
            className="bg-court-card border border-court-border rounded-xl p-4 text-center"
          >
            <div className="text-xs text-court-muted uppercase mb-2">
              {s.label}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="font-bold">{s.home}</div>
              <div className="font-bold">{s.away}</div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-court-muted mt-1">
              <div>{home_team.abbreviation}</div>
              <div>{away_team.abbreviation}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Box Scores */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {renderBoxScore(home_team, player_stats.home)}
        {renderBoxScore(away_team, player_stats.away)}
      </div>
    </div>
  );
}
