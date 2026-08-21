"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchGameTeams, fetchGames } from "@/lib/api";
import { useRouter } from "next/navigation";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function GamesPage() {
  const router = useRouter();
  const [team, setTeam] = useState("");
  const [result, setResult] = useState("");

  const { data: teamsData } = useQuery({
    queryKey: ["gameTeams"],
    queryFn: fetchGameTeams,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["games", team, result],
    queryFn: () =>
      fetchGames({
        team: team || undefined,
        result: result || undefined,
      }),
  });

  const teams = teamsData?.teams || [];
  const matches = data?.matches || [];

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">Game Log Explorer</h1>
      <p className="text-court-muted mb-6">
        Browse game results — click a game to see the full box score
      </p>

      <div className="flex gap-4 mb-6">
        <select
          value={team}
          onChange={(e) => setTeam(e.target.value)}
          className="bg-court-card border border-court-border rounded-lg px-4 py-2 text-sm text-white"
        >
          <option value="">All Teams</option>
          {teams.map((t: string) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={result}
          onChange={(e) => setResult(e.target.value)}
          className="bg-court-card border border-court-border rounded-lg px-4 py-2 text-sm text-white"
        >
          <option value="">All</option>
          <option value="W">Wins</option>
          <option value="L">Losses</option>
        </select>
        <span className="text-court-muted text-sm self-center">
          {data?.total_count || 0} games
        </span>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={15} />
      ) : (
        <div className="overflow-auto rounded-xl border border-court-border bg-court-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-court-border">
                {["Date", "Matchup", "Result", "PTS", "REB", "AST", "+/-"].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-court-muted text-xs uppercase tracking-wider"
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {matches.map((m: any, i: number) => {
                const resultColor =
                  m.result === "W" ? "text-court-green" : "text-court-red";
                const pmColor =
                  m.plus_minus >= 0 ? "text-court-green" : "text-court-red";

                return (
                  <tr
                    key={`${m.game_id}-${m.team}-${i}`}
                    className="border-b border-court-border hover:bg-white/5 cursor-pointer"
                    onClick={() => router.push(`/matches/${m.game_id}`)}
                  >
                    <td className="px-4 py-3 text-court-muted">{m.date}</td>
                    <td className="px-4 py-3 font-semibold">
                      {m.team} {m.matchup}
                    </td>
                    <td className={`px-4 py-3 font-bold ${resultColor}`}>
                      {m.result}
                    </td>
                    <td className="px-4 py-3">{m.points}</td>
                    <td className="px-4 py-3">{m.rebounds}</td>
                    <td className="px-4 py-3">{m.assists}</td>
                    <td className={`px-4 py-3 ${pmColor}`}>
                      {m.plus_minus > 0 ? "+" : ""}
                      {m.plus_minus}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
