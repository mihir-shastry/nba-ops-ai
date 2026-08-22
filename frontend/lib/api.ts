const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ---- Teams ----
export async function fetchStandings() {
  return fetchJSON<{ east: any[]; west: any[] }>("/teams");
}

export async function fetchTeamOverview(name: string) {
  return fetchJSON<{
    team: any;
    core_stats: any;
    advanced_metrics: any;
    recent_form: any[];
    roster: any[];
  }>(`/teams/${encodeURIComponent(name)}`);
}

// ---- Ratings ----
export async function fetchRatings(sortBy = "rating", limit = 50) {
  return fetchJSON<{ players: any[] }>(`/ratings?sort_by=${sortBy}&limit=${limit}`);
}

export async function fetchPlayerRating(name: string) {
  return fetchJSON<{
    player: any;
    rating: number;
    breakdown: any;
    game_log: any[];
  }>(`/ratings/${encodeURIComponent(name)}`);
}

export async function fetchPlayerMatches(name: string, limit = 10) {
  return fetchJSON<{ matches: any[]; total_count: number }>(
    `/ratings/${encodeURIComponent(name)}/matches?limit=${limit}`
  );
}

// ---- Compare ----
export async function fetchComparison(p1: string, p2: string) {
  return fetchJSON<{
    player1: any;
    player2: any;
    stat_table: any[];
    verdicts: any[];
  }>(`/compare/${encodeURIComponent(p1)}/${encodeURIComponent(p2)}`);
}

// ---- Similarity ----
export async function fetchSimilarPlayers(name: string, limit = 5) {
  return fetchJSON<{
    player: any;
    similar_players: any[];
    stat_vector_labels: string[];
  }>(`/similar/${encodeURIComponent(name)}?limit=${limit}`);
}
