"use client";

import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { fetchShotPlayers, fetchPlayerShots, fetchPlayerZones } from "@/lib/api";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

export default function ShotsPage() {
  const [player, setPlayer] = useState("");

  const { data: playersData } = useQuery({
    queryKey: ["shotPlayers"],
    queryFn: fetchShotPlayers,
  });

  const { data: shotsData, isLoading: shotsLoading } = useQuery({
    queryKey: ["shots", player],
    queryFn: () => fetchPlayerShots(player),
    enabled: !!player,
  });

  const { data: zonesData, isLoading: zonesLoading } = useQuery({
    queryKey: ["zones", player],
    queryFn: () => fetchPlayerZones(player),
    enabled: !!player,
  });

  const players = playersData?.players || [];

  useEffect(() => {
    if (players.length > 0 && !player) {
      setPlayer(players[0]);
    }
  }, [players, player]);

  const summary = shotsData?.summary;
  const shots = shotsData?.shots || [];
  const zones = zonesData?.zones || [];

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">Shot Charts</h1>
      <p className="text-court-muted mb-6">Shot visualization by player</p>

      <select
        value={player}
        onChange={(e) => setPlayer(e.target.value)}
        className="bg-court-card border border-court-border rounded-lg px-4 py-2 text-sm text-white mb-6"
      >
        <option value="">Select Player</option>
        {players.map((p: string) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>

      {shotsLoading ? (
        <LoadingSkeleton rows={10} />
      ) : summary ? (
        <div>
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            {[
              { label: "Attempts", value: summary.total_attempts?.toLocaleString() },
              { label: "Makes", value: summary.makes?.toLocaleString() },
              { label: "FG%", value: `${summary.fg_pct}%` },
              { label: "Avg Distance", value: `${summary.avg_distance} ft` },
            ].map((s) => (
              <div
                key={s.label}
                className="bg-court-card border border-court-border rounded-xl p-4 text-center"
              >
                <div className="text-xs text-court-muted uppercase">
                  {s.label}
                </div>
                <div className="text-2xl font-bold mt-1">{s.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Shot Chart Court */}
            <div className="lg:col-span-2">
              <h3 className="text-sm font-bold text-court-muted uppercase mb-3">
                Shot Chart
              </h3>
              <div className="bg-court-card border border-court-border rounded-xl p-4">
                <svg
                  viewBox="-260 -50 520 500"
                  className="w-full"
                  style={{ maxHeight: 500 }}
                >
                  {/* Court outline */}
                  <rect
                    x={-250}
                    y={-47.5}
                    width={500}
                    height={470}
                    fill="none"
                    stroke="rgba(255,255,255,0.15)"
                    strokeWidth={2}
                  />
                  {/* Paint */}
                  <rect
                    x={-80}
                    y={-47.5}
                    width={160}
                    height={191}
                    fill="none"
                    stroke="rgba(255,255,255,0.15)"
                    strokeWidth={2}
                  />
                  {/* Three-point line */}
                  <path
                    d="M -220 -47.5 L -220 90 A 237.5 237.5 0 0 1 220 90 L 220 -47.5"
                    fill="none"
                    stroke="rgba(255,255,255,0.15)"
                    strokeWidth={2}
                  />
                  {/* Basket */}
                  <circle cx={0} cy={0} r={10} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={1.5} />
                  {/* Free throw line */}
                  <line x1={-80} y1={143.5} x2={80} y2={143.5} stroke="rgba(255,255,255,0.15)" strokeWidth={2} />

                  {/* Made shots */}
                  {shots
                    .filter((s: any) => s.shot_made_flag === 1)
                    .map((s: any, i: number) => (
                      <circle
                        key={`made-${i}`}
                        cx={s.loc_x}
                        cy={s.loc_y}
                        r={4}
                        fill="#00d4aa"
                        opacity={0.8}
                      />
                    ))}

                  {/* Missed shots */}
                  {shots
                    .filter((s: any) => s.shot_made_flag === 0)
                    .map((s: any, i: number) => (
                      <circle
                        key={`missed-${i}`}
                        cx={s.loc_x}
                        cy={s.loc_y}
                        r={4}
                        fill="#ff4757"
                        opacity={0.6}
                      />
                    ))}
                </svg>
                <div className="flex gap-4 justify-center mt-2 text-xs text-court-muted">
                  <span>
                    <span className="inline-block w-3 h-3 rounded-full bg-court-green mr-1" />
                    Made
                  </span>
                  <span>
                    <span className="inline-block w-3 h-3 rounded-full bg-court-red mr-1" />
                    Missed
                  </span>
                </div>
              </div>
            </div>

            {/* Zone Efficiency */}
            <div>
              <h3 className="text-sm font-bold text-court-muted uppercase mb-3">
                Zone Efficiency
              </h3>
              <div className="bg-court-card border border-court-border rounded-xl p-4">
                {zonesLoading ? (
                  <LoadingSkeleton rows={8} />
                ) : (
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={zones} layout="vertical">
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.05)"
                      />
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                        tick={{ fill: "#a0a0b0", fontSize: 10 }}
                      />
                      <YAxis
                        type="category"
                        dataKey="shot_zone_basic"
                        width={80}
                        tick={{ fill: "#a0a0b0", fontSize: 10 }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#161638",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 8,
                        }}
                      />
                      <Bar dataKey="fg_pct" radius={[0, 4, 4, 0]}>
                        {zones.map((z: any, i: number) => (
                          <Cell
                            key={i}
                            fill={
                              z.fg_pct > 50
                                ? "#00d4aa"
                                : z.fg_pct > 40
                                  ? "#f7c948"
                                  : "#ff4757"
                            }
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
