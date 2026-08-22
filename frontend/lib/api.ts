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

// ---- Games ----
export async function fetchGameTeams() {
  return fetchJSON<{ teams: string[] }>("/games/teams");
}

export async function fetchGames(params?: { team?: string; result?: string }) {
  const qs = new URLSearchParams();
  if (params?.team) qs.set("team", params.team);
  if (params?.result) qs.set("result", params.result);
  return fetchJSON<{ matches: any[]; total_count: number }>(`/games?${qs}`);
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

// ---- Compare ----
export async function fetchComparison(p1: string, p2: string) {
  return fetchJSON<{
    player1: any;
    player2: any;
    stat_table: any[];
    verdicts: any[];
  }>(`/compare/${encodeURIComponent(p1)}/${encodeURIComponent(p2)}`);
}

// ---- Matches ----
export async function fetchMatches(params?: { team?: string; date_from?: string; date_to?: string }) {
  const qs = new URLSearchParams();
  if (params?.team) qs.set("team", params.team);
  return fetchJSON<{ matches: any[]; total_count: number }>(`/matches?${qs}`);
}

export async function fetchMatchDetail(gameId: string) {
  return fetchJSON<{
    game: any;
    home_team: any;
    away_team: any;
    player_stats: { home: any[]; away: any[] };
  }>(`/matches/${encodeURIComponent(gameId)}`);
}

// ---- Lineups ----
export async function fetchTeamLineups(team: string, minMinutes = 50) {
  return fetchJSON<{
    team: string;
    lineups: any[];
    total_lineups: number;
  }>(`/lineups/${encodeURIComponent(team)}?min_minutes=${minMinutes}`);
}

export async function fetchLeagueBestLineups(minMinutes = 100, limit = 20) {
  return fetchJSON<{ lineups: any[]; total_count: number }>(
    `/lineups/league/best?min_minutes=${minMinutes}&limit=${limit}`
  );
}

// ---- SQL ----
export async function fetchPrebuiltQueries() {
  return fetchJSON<{ queries: any[] }>("/sql/prebuilt");
}

export async function executeSQL(query: string) {
  return fetchJSON<{
    columns: string[];
    rows: any[][];
    row_count: number;
    error?: string;
  }>("/sql/execute", { method: "POST", body: JSON.stringify({ query }) });
}

// ---- Shot Charts ----
export async function fetchShotPlayers() {
  return fetchJSON<{ players: string[] }>("/shots/players");
}

export async function fetchPlayerShots(name: string) {
  return fetchJSON<{
    shots: any[];
    summary: any;
  }>(`/shots/${encodeURIComponent(name)}`);
}

export async function fetchPlayerZones(name: string) {
  return fetchJSON<{ zones: any[] }>(`/shots/${encodeURIComponent(name)}/zones`);
}

// ---- Chat ----
export async function askQuestion(question: string) {
  return fetchJSON<{
    answer: string;
    sql: string;
    columns: string[];
    rows: any[][];
  }>("/chat/ask", { method: "POST", body: JSON.stringify({ question }) });
}


// ---- Similarity ----
export async function fetchSimilarPlayers(name: string, limit = 5) {
  return fetchJSON<{
    player: any;
    similar_players: any[];
    stat_vector_labels: string[];
  }>(`/similar/${encodeURIComponent(name)}?limit=${limit}`);
}
