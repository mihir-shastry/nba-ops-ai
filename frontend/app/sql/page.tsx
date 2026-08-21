"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { fetchPrebuiltQueries, executeSQL } from "@/lib/api";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function SQLPage() {
  const [query, setQuery] = useState(
    "SELECT * FROM league_leaders ORDER BY points_per_game DESC LIMIT 10"
  );

  const { data: prebuilt } = useQuery({
    queryKey: ["prebuilt"],
    queryFn: fetchPrebuiltQueries,
  });

  const mutation = useMutation({
    mutationFn: executeSQL,
  });

  const handleRun = () => {
    mutation.mutate(query);
  };

  const result = mutation.data;

  return (
    <div>
      <h1 className="text-3xl font-extrabold mb-1">📊 SQL Analytics</h1>
      <p className="text-court-muted mb-6">Query NBA data with SQL</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Pre-built Queries */}
        <div>
          <h3 className="text-sm font-bold text-court-muted uppercase mb-2">
            Pre-built Queries
          </h3>
          <div className="bg-court-card border border-court-border rounded-xl p-3 space-y-2 max-h-64 overflow-auto">
            {prebuilt?.queries?.map((q: any) => (
              <button
                key={q.key}
                onClick={() => setQuery(q.sql)}
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 text-sm transition-colors"
              >
                <div className="font-medium">{q.name}</div>
                <div className="text-xs text-court-muted">{q.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Query Editor */}
        <div className="lg:col-span-2">
          <h3 className="text-sm font-bold text-court-muted uppercase mb-2">
            SQL Query
          </h3>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full h-32 bg-court-card border border-court-border rounded-xl p-4 text-sm text-white font-mono resize-none focus:outline-none focus:border-court-orange"
            placeholder="Enter your SQL query..."
          />
          <button
            onClick={handleRun}
            disabled={mutation.isPending}
            className="mt-3 px-6 py-2.5 bg-gradient-to-r from-court-orange to-court-gold text-court-bg font-bold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {mutation.isPending ? "Running..." : "▶ Run Query"}
          </button>
        </div>
      </div>

      {/* Results */}
      {mutation.isError && (
        <div className="bg-court-red/10 border border-court-red/30 rounded-xl p-4 text-court-red mb-6">
          Error: {mutation.error?.message}
        </div>
      )}

      {result && (
        <div>
          {result.error ? (
            <div className="bg-court-red/10 border border-court-red/30 rounded-xl p-4 text-court-red">
              {result.error}
            </div>
          ) : (
            <div>
              <p className="text-court-muted text-sm mb-3">
                {result.row_count} rows returned
              </p>
              <div className="overflow-auto rounded-xl border border-court-border bg-court-card">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-court-border">
                      {result.columns.map((col: string) => (
                        <th
                          key={col}
                          className="px-4 py-3 text-left text-court-muted text-xs uppercase tracking-wider"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.rows.map((row: any[], i: number) => (
                      <tr
                        key={i}
                        className="border-b border-court-border last:border-0"
                      >
                        {row.map((val: any, j: number) => (
                          <td key={j} className="px-4 py-3">
                            {val == null ? "—" : String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
