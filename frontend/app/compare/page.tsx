"use client";

import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { fetchRatings, fetchComparison } from "@/lib/api";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function ComparePage() {
  const [player1, setPlayer1] = useState("");
  const [player2, setPlayer2] = useState("");

  const { data: ratingsData } = useQuery({
    queryKey: ["ratingsList"],
    queryFn: () => fetchRatings("rating", 200),
  });

  const players = ratingsData?.players || [];
  const playerNames = players.map((p: any) => p.player_name);

  const { data: comparison, isLoading } = useQuery({
    queryKey: ["comparison", player1, player2],
    queryFn: () => fetchComparison(player1, player2),
    enabled: !!player1 && !!player2 && player1 !== player2,
  });

  // Auto-select first two players
  useEffect(() => {
    if (playerNames.length >= 2 && !player1) {
      setPlayer1(playerNames[0]);
      setPlayer2(playerNames[1]);
    }
  }, [playerNames, player1]);

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">🔄 Player Comparison</h1>
      <p className="text-court-muted mb-6">
        Compare two players head-to-head
      </p>

      <div className="flex gap-4 mb-8">
        <select
          value={player1}
          onChange={(e) => setPlayer1(e.target.value)}
          className="bg-court-card border border-court-border rounded-lg px-4 py-2 text-sm text-white flex-1"
        >
          <option value="">Select Player 1</option>
          {playerNames.map((name: string) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        <select
          value={player2}
          onChange={(e) => setPlayer2(e.target.value)}
          className="bg-court-card border border-court-border rounded-lg px-4 py-2 text-sm text-white flex-1"
        >
          <option value="">Select Player 2</option>
          {playerNames.map((name: string) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <LoadingSkeleton rows={8} />}

      {comparison && !isLoading && (
        <div>
          {/* Player Headers */}
          <div className="grid grid-cols-2 gap-8 mb-8">
            <div className="text-center">
              <div className="text-4xl font-extrabold text-court-gold">
                {comparison.player1.rating}
              </div>
              <div className="text-lg font-bold">
                {comparison.player1.player.player_name}
              </div>
              <div className="text-court-muted text-sm">
                {comparison.player1.player.team_abbreviation} |{" "}
                {comparison.player1.player.points_per_game} PPG
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-extrabold text-court-orange">
                {comparison.player2.rating}
              </div>
              <div className="text-lg font-bold">
                {comparison.player2.player.player_name}
              </div>
              <div className="text-court-muted text-sm">
                {comparison.player2.player.team_abbreviation} |{" "}
                {comparison.player2.player.points_per_game} PPG
              </div>
            </div>
          </div>

          {/* Dual Radar */}
          <div className="bg-court-card border border-court-border rounded-xl p-6 mb-8">
            <h3 className="text-sm font-bold text-court-muted mb-4 uppercase">
              Skill Comparison
            </h3>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart
                data={[
                  "Scoring",
                  "Rebounding",
                  "Playmaking",
                  "Defense",
                  "Efficiency",
                ].map((cat) => ({
                  category: cat,
                  [comparison.player1.player.player_name]:
                    comparison.player1.radar_values[cat],
                  [comparison.player2.player.player_name]:
                    comparison.player2.radar_values[cat],
                }))}
              >
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis
                  dataKey="category"
                  tick={{ fill: "#a0a0b0", fontSize: 12 }}
                />
                <Radar
                  name={comparison.player1.player.player_name}
                  dataKey={comparison.player1.player.player_name}
                  stroke="#f7c948"
                  fill="#f7c948"
                  fillOpacity={0.15}
                />
                <Radar
                  name={comparison.player2.player.player_name}
                  dataKey={comparison.player2.player.player_name}
                  stroke="#ff6b35"
                  fill="#ff6b35"
                  fillOpacity={0.15}
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Verdicts */}
          <div className="grid grid-cols-5 gap-4 mb-8">
            {comparison.verdicts.map((v: any) => {
              const isEven = v.winner === "Even";
              const isP1 = v.winner === comparison.player1.player.player_name;
              const color = isEven
                ? "text-court-muted"
                : isP1
                  ? "text-court-gold"
                  : "text-court-orange";

              return (
                <div
                  key={v.category}
                  className="text-center bg-court-card border border-court-border rounded-xl p-4"
                >
                  <div className="text-xs text-court-muted uppercase mb-2">
                    {v.category}
                  </div>
                  <div className={`text-lg font-bold ${color}`}>
                    {isEven ? "Even" : `${v.winner} ${v.margin}`}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Stat Table */}
          <div className="bg-court-card border border-court-border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-court-border">
                  <th className="px-4 py-3 text-left text-court-muted text-xs uppercase">
                    Stat
                  </th>
                  <th className="px-4 py-3 text-left text-court-muted text-xs uppercase">
                    {comparison.player1.player.player_name}
                  </th>
                  <th className="px-4 py-3 text-left text-court-muted text-xs uppercase">
                    {comparison.player2.player.player_name}
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparison.stat_table.map((s: any, i: number) => (
                  <tr
                    key={s.stat}
                    className="border-b border-court-border last:border-0"
                  >
                    <td className="px-4 py-3 font-semibold">{s.stat}</td>
                    <td
                      className={`px-4 py-3 ${s.winner === "player1" ? "text-court-gold font-bold" : ""}`}
                    >
                      {s.player1_value}
                    </td>
                    <td
                      className={`px-4 py-3 ${s.winner === "player2" ? "text-court-orange font-bold" : ""}`}
                    >
                      {s.player2_value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
