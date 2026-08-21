"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  fetchLeagueBestLineups,
  fetchTeamLineups,
  fetchGameTeams,
} from "@/lib/api";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function LineupsPage() {
  const [view, setView] = useState<"league" | "team">("league");
  const [selectedTeam, setSelectedTeam] = useState("");
  const [minMinutes, setMinMinutes] = useState(100);
  const [limit, setLimit] = useState(20);

  const { data: teamsData } = useQuery({
    queryKey: ["gameTeams"],
    queryFn: fetchGameTeams,
  });

  const { data: leagueData, isLoading: leagueLoading } = useQuery({
    queryKey: ["leagueLineups", minMinutes, limit],
    queryFn: () => fetchLeagueBestLineups(minMinutes, limit),
    enabled: view === "league",
  });

  const { data: teamData, isLoading: teamLoading } = useQuery({
    queryKey: ["teamLineups", selectedTeam],
    queryFn: () => fetchTeamLineups(selectedTeam),
    enabled: view === "team" && !!selectedTeam,
  });

  const teams = teamsData?.teams || [];
  const lineups =
    view === "league" ? leagueData?.lineups || [] : teamData?.lineups || [];
  const isLoading = view === "league" ? leagueLoading : teamLoading;

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">🔧 Lineup Optimizer</h1>
      <p className="text-court-muted mb-6">
        5-man unit stats — find the best combinations
      </p>

      {/* View Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setView("league")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === "league"
              ? "bg-gradient-to-r from-court-orange to-court-gold text-court-bg"
              : "bg-court-card border border-court-border text-court-muted hover:text-white"
          }`}
        >
          League Best
        </button>
        <button
          onClick={() => setView("team")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === "team"
              ? "bg-gradient-to-r from-court-orange to-court-gold text-court-bg"
              : "bg-court-card border border-court-border text-court-muted hover:text-white"
          }`}
        >
          Team Lineups
        </button>
      </div>

      {/* Filters */}
      {view === "league" && (
        <div className="flex gap-4 mb-6">
          <div>
            <label className="text-xs text-court-muted block mb-1">
              Min Minutes
            </label>
            <input
              type="range"
              min={50}
              max={500}
              value={minMinutes}
              onChange={(e) => setMinMinutes(Number(e.target.value))}
              className="w-48"
            />
            <span className="text-court-muted text-sm ml-2">{minMinutes}</span>
          </div>
          <div>
            <label className="text-xs text-court-muted block mb-1">
              Show Top N
            </label>
            <input
              type="range"
              min={5}
              max={50}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-48"
            />
            <span className="text-court-muted text-sm ml-2">{limit}</span>
          </div>
        </div>
      )}

      {view === "team" && (
        <div className="mb-6">
          <select
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
            className="bg-court-card border border-court-border rounded-lg px-4 py-2 text-sm text-white"
          >
            <option value="">Select a team</option>
            {teams.map((t: string) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      )}

      {isLoading ? (
        <LoadingSkeleton rows={8} />
      ) : (
        <div className="space-y-3">
          {lineups.map((lu: any, i: number) => {
            const pmColor =
              lu.plus_minus >= 0 ? "text-court-green" : "text-court-red";

            return (
              <details
                key={i}
                className="bg-court-card border border-court-border rounded-xl overflow-hidden group"
              >
                <summary className="px-4 py-3 cursor-pointer hover:bg-white/5 flex items-center gap-4">
                  <span className="text-court-muted text-sm w-8">#{i + 1}</span>
                  {view === "league" && (
                    <span className="text-xs font-bold text-court-orange bg-court-orange/10 px-2 py-0.5 rounded">
                      {lu.team}
                    </span>
                  )}
                  <span className="font-medium text-sm flex-1">{lu.lineup}</span>
                  <span className={`font-bold ${pmColor}`}>
                    {lu.plus_minus > 0 ? "+" : ""}
                    {lu.plus_minus}
                  </span>
                </summary>
                <div className="px-4 pb-4 grid grid-cols-5 gap-4 text-sm">
                  <div>
                    <div className="text-xs text-court-muted">Games</div>
                    <div className="font-bold">{lu.games}</div>
                  </div>
                  <div>
                    <div className="text-xs text-court-muted">Record</div>
                    <div className="font-bold">
                      {lu.wins}-{lu.losses}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-court-muted">Win%</div>
                    <div className="font-bold">
                      {(lu.win_pct * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-court-muted">Minutes</div>
                    <div className="font-bold">{lu.minutes?.toFixed(0)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-court-muted">+/-</div>
                    <div className={`font-bold ${pmColor}`}>
                      {lu.plus_minus > 0 ? "+" : ""}
                      {lu.plus_minus}
                    </div>
                  </div>
                </div>
              </details>
            );
          })}
        </div>
      )}
    </div>
  );
}
