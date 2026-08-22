"use client";

import { useQuery } from "@tanstack/react-query";
import { useState, useRef, useEffect } from "react";
import { fetchRatings, fetchPlayerRating, fetchSimilarPlayers, fetchPlayerMatches } from "@/lib/api";
import { ratingColor } from "@/lib/utils";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function RatingsPage() {
  const [sortBy, setSortBy] = useState("rating");
  const [limit, setLimit] = useState(50);
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const detailRef = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["ratings", sortBy, limit],
    queryFn: () => fetchRatings(sortBy, limit),
  });

  useEffect(() => {
    if (selectedPlayer && detailRef.current) {
      detailRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [selectedPlayer]);

  const { data: playerDetail, isLoading: detailLoading } = useQuery({
    queryKey: ["playerRating", selectedPlayer],
    queryFn: () => fetchPlayerRating(selectedPlayer!),
    enabled: !!selectedPlayer,
  });

  const { data: similarData, isLoading: similarLoading } = useQuery({
    queryKey: ["similarPlayers", selectedPlayer],
    queryFn: () => fetchSimilarPlayers(selectedPlayer!),
    enabled: !!selectedPlayer,
  });

  const { data: matchesData, isLoading: matchesLoading } = useQuery({
    queryKey: ["playerMatches", selectedPlayer],
    queryFn: () => fetchPlayerMatches(selectedPlayer!),
    enabled: !!selectedPlayer,
  });

  if (isLoading) return <LoadingSkeleton rows={15} />;

  const players = data?.players || [];

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">Player Ratings</h1>
      <p className="text-court-muted mb-6">
        Context-aware ratings (0-100) based on z-score normalization
      </p>

      <div className="flex gap-4 mb-6">
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-court-card border border-court-border rounded-lg px-4 py-2 text-sm text-white"
        >
          <option value="rating">Overall Rating</option>
          <option value="pts">Points</option>
          <option value="reb">Rebounds</option>
          <option value="ast">Assists</option>
        </select>
        <input
          type="range"
          min={10}
          max={100}
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="w-48"
        />
        <span className="text-court-muted text-sm">Top {limit}</span>
      </div>

      <div className="overflow-auto rounded-xl border border-court-border bg-court-card mb-8">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-court-border">
              {[
                "#",
                "Player",
                "Team",
                "Rating",
                "PPG",
                "RPG",
                "APG",
                "FG%",
                "3PT%",
              ].map((h) => (
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
            {players.map((p: any, i: number) => (
              <tr
                key={p.player_name}
                className={`border-b border-court-border hover:bg-white/5 cursor-pointer ${
                  selectedPlayer === p.player_name ? "bg-white/5" : ""
                }`}
                onClick={() => setSelectedPlayer(p.player_name)}
              >
                <td className="px-4 py-3 text-court-muted">{i + 1}</td>
                <td className="px-4 py-3 font-semibold">{p.player_name}</td>
                <td className="px-4 py-3">{p.team_abbreviation}</td>
                <td className={`px-4 py-3 ${ratingColor(p.rating)}`}>
                  {p.rating}
                </td>
                <td className="px-4 py-3">{p.points_per_game}</td>
                <td className="px-4 py-3">{p.rebounds_per_game}</td>
                <td className="px-4 py-3">{p.assists_per_game}</td>
                <td className="px-4 py-3">{p.field_goal_pct}%</td>
                <td className="px-4 py-3">{p.three_point_pct}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedPlayer && (
        <div ref={detailRef} className="bg-court-card border border-court-border rounded-xl p-6">
          {detailLoading ? (
            <LoadingSkeleton rows={5} />
          ) : playerDetail ? (
            <div>
              <div className="flex items-start gap-8 mb-6">
                <div className="flex-1">
                  <h2 className="text-2xl font-extrabold">
                    {playerDetail.player.player_name}
                  </h2>
                  <p className="text-court-muted">
                    {playerDetail.player.team_abbreviation} |{" "}
                    {playerDetail.player.games_played} games |{" "}
                    {playerDetail.player.minutes_per_game?.toFixed(1)} MPG
                  </p>
                </div>
                <div className="text-center">
                  <div className="text-5xl font-extrabold text-court-gold">
                    {playerDetail.rating}
                  </div>
                  <div className="text-court-muted text-sm">RATING</div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Radar Chart */}
                <div>
                  <h3 className="text-sm font-bold text-court-muted mb-2 uppercase">
                    Skill Breakdown
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={Object.entries(playerDetail.breakdown).map(([k, v]) => ({ category: k.charAt(0).toUpperCase() + k.slice(1), value: v }))}>
                      <PolarGrid stroke="rgba(255,255,255,0.1)" />
                      <PolarAngleAxis dataKey="category" tick={{ fill: "#a0a0b0", fontSize: 12 }} />
                      <Radar
                        dataKey="value"
                        stroke="#f7c948"
                        fill="#f7c948"
                        fillOpacity={0.2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>

                {/* Trend Line */}
                <div>
                  <h3 className="text-sm font-bold text-court-muted mb-2 uppercase">
                    Rating Trend
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart
                      data={playerDetail.game_log?.slice(-20) || []}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="date" tick={{ fill: "#a0a0b0", fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fill: "#a0a0b0", fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          background: "#161638",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 8,
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="rating"
                        stroke="#f7c948"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Season Stats */}
              <div className="grid grid-cols-5 gap-4 mt-6">
                {[
                  { label: "PPG", value: playerDetail.player.points_per_game },
                  { label: "RPG", value: playerDetail.player.rebounds_per_game },
                  { label: "APG", value: playerDetail.player.assists_per_game },
                  { label: "FG%", value: `${playerDetail.player.field_goal_pct}%` },
                  { label: "3PT%", value: `${playerDetail.player.three_point_pct}%` },
                ].map((s) => (
                  <div key={s.label} className="text-center">
                    <div className="text-xs text-court-muted uppercase">
                      {s.label}
                    </div>
                    <div className="text-xl font-bold">{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Similar Players */}
              {similarData?.similar_players && similarData.similar_players.length > 0 && (
                <div className="mt-8 border-t border-court-border pt-6">
                  <h3 className="text-sm font-bold text-court-muted mb-4 uppercase">
                    Most Similar Players
                  </h3>
                  <div className="grid grid-cols-5 gap-3">
                    {similarData?.similar_players.map((sp: any) => (
                      <div
                        key={sp.player_name}
                        className="bg-court-bg rounded-lg p-3 border border-court-border hover:border-court-gold/50 transition-colors cursor-pointer"
                        onClick={() => setSelectedPlayer(sp.player_name)}
                      >
                        <div className="text-sm font-bold truncate">{sp.player_name}</div>
                        <div className="text-xs text-court-muted">{sp.team_abbreviation}</div>
                        <div className="mt-2 flex items-center gap-2">
                          <div className="text-lg font-extrabold text-court-gold">
                            {(sp.similarity * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-court-muted">match</div>
                        </div>
                        <div className="mt-1 text-xs text-court-muted">
                          {sp.points_per_game} pts / {sp.rebounds_per_game} reb / {sp.assists_per_game} ast
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-court-muted mt-3">
                    Based on cosine similarity across points, rebounds, assists, steals, blocks, turnovers/36, FG%, and 3PT%
                  </p>
                </div>
              )}
              {/* Recent Matches */}
              {matchesData?.matches && matchesData.matches.length > 0 && (
                <div className="mt-8 border-t border-court-border pt-6">
                  <h3 className="text-sm font-bold text-court-muted mb-4 uppercase">
                    Recent Matches - {playerDetail.player.team_abbreviation}
                  </h3>
                  <div className="overflow-auto rounded-lg border border-court-border">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-court-border bg-court-bg">
                          <th className="px-3 py-2 text-left text-court-muted text-xs">Date</th>
                          <th className="px-3 py-2 text-left text-court-muted text-xs">Matchup</th>
                          <th className="px-3 py-2 text-center text-court-muted text-xs">Result</th>
                          <th className="px-3 py-2 text-right text-court-muted text-xs">PTS</th>
                          <th className="px-3 py-2 text-right text-court-muted text-xs">REB</th>
                          <th className="px-3 py-2 text-right text-court-muted text-xs">AST</th>
                          <th className="px-3 py-2 text-right text-court-muted text-xs">+/-</th>
                        </tr>
                      </thead>
                      <tbody>
                        {matchesData?.matches.map((m: any, idx: number) => (
                          <tr key={idx} className="border-b border-court-border hover:bg-white/5">
                            <td className="px-3 py-2 text-court-muted">{m.date}</td>
                            <td className="px-3 py-2">{m.matchup}</td>
                            <td className={`px-3 py-2 text-center font-bold ${
                              m.result === 'W' ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {m.result}
                            </td>
                            <td className="px-3 py-2 text-right">{m.points}</td>
                            <td className="px-3 py-2 text-right">{m.rebounds}</td>
                            <td className="px-3 py-2 text-right">{m.assists}</td>
                            <td className={`px-3 py-2 text-right font-mono ${
                              m.plus_minus > 0 ? 'text-green-400' : m.plus_minus < 0 ? 'text-red-400' : 'text-court-muted'
                            }`}>
                              {m.plus_minus > 0 ? '+' : ''}{m.plus_minus}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-court-muted mt-2">
                    Team-level game results. Individual player stats shown when available.
                  </p>
                </div>
              )}

            </div>
          ) : null}
        </div>
      )}

      {/* Rating Methodology Note */}
      <div className="mt-12 border-t border-court-border pt-6">
        <h3 className="text-xs font-semibold text-court-muted uppercase tracking-widest mb-3">
          How Ratings Are Calculated
        </h3>
        <div className="text-xs text-court-muted leading-relaxed max-w-2xl space-y-2">
          <p>
            Each rating is computed using <strong className="text-white">z-score normalization</strong> across six core stats: points, rebounds, assists, steals, blocks, and turnovers. For each stat, a player&apos;s value is converted to standard deviations from the league mean.
          </p>
          <p>
            The z-scores are then combined with weights that reflect impact: scoring (1.5×), rebounding (0.8×), playmaking (1.2×), steals (1.0×), blocks (1.0×), and turnovers (−0.5×, normalized per 36 minutes). The combined score is passed through a <strong className="text-white">sigmoid function</strong> to map it to a 0–100 scale, which naturally clusters most players around 50 and spreads elites toward 100.
          </p>
          <p>
            League averages and standard deviations are computed from all players with 20+ games played in the current season. Turnovers are normalized to per-36 minutes to fairly compare players across different roles and minutes played.
          </p>
        </div>
      </div>
    </div>
  );
}
