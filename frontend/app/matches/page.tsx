"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchMatches, fetchGameTeams } from "@/lib/api";
import { useRouter } from "next/navigation";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function MatchesPage() {
  const router = useRouter();
  const [team, setTeam] = useState("");

  const { data: teamsData } = useQuery({
    queryKey: ["gameTeams"],
    queryFn: fetchGameTeams,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["matches", team],
    queryFn: () => fetchMatches(team ? { team } : undefined),
  });

  const teams = teamsData?.teams || [];
  const matches = data?.matches || [];

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">Match Dashboard</h1>
      <p className="text-court-muted mb-6">
        Game box scores with player ratings
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
        <span className="text-court-muted text-sm self-center">
          {data?.total_count || 0} games
        </span>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={10} />
      ) : (
        <div className="space-y-2">
          {matches.map((m: any) => {
            const pmColor =
              m.plus_minus >= 0 ? "text-court-green" : "text-court-red";
            const resultColor =
              m.result === "W" ? "text-court-green" : "text-court-red";

            return (
              <div
                key={`${m.game_id}-${m.team}`}
                className="bg-court-card border border-court-border rounded-xl p-4 flex items-center gap-6 hover:bg-white/5 cursor-pointer transition-colors"
                onClick={() => router.push(`/matches/${m.game_id}`)}
              >
                <div className="text-sm text-court-muted w-24">{m.date}</div>
                <div className="font-semibold flex-1">
                  {m.team} {m.matchup}
                </div>
                <div className={`text-xl font-bold ${resultColor} w-20`}>
                  {m.result} {m.points}
                </div>
                <div className="text-sm text-court-muted w-48">
                  PTS: {m.points} | REB: {m.rebounds} | AST: {m.assists} | +/-
                  <span className={`ml-1 ${pmColor}`}>
                    {m.plus_minus > 0 ? "+" : ""}
                    {m.plus_minus}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
