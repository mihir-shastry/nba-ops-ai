# Replace Auto-Insights with Team Dashboard & Game Log Explorer

**Date:** 2026-08-18
**Author:** Buffy (Codebuff)
**Status:** Approved

## Overview

Replace the auto-insights feature (1B) with two new features that better fit the basketball operations vision:

1. **Team Dashboard** — conference standings → team overview with core + advanced stats
2. **Game Log Explorer** — filterable table of game results with box-score style data

Both features are zero-Gemini (pure SQL + Python + Plotly). The auto-insights code (`backend/insights.py` and related frontend) will be removed.

---

## Scope

- **In scope:** Team Dashboard tab, Game Log Explorer tab, removal of auto-insights
- **Out of scope:** Multi-season support (single season only), player comparison (Phase 2A), shot chart enhancements (Phase 2B), player-level drill-down in game logs (future), quarter-by-quarter breakdowns (future)

---

## Feature 1: Team Dashboard Tab ("🏆 Teams")

### Entry Point

Conference standings table displayed side by side (East + West).

**Columns:** Rank, Team, W, L, Win%, GB (Games Behind)

**Behavior:** Rows are clickable — clicking a team navigates to that team's overview.

### Team Overview (after clicking a team)

**Header:** Team name, win-loss record

**Core Stats Row (metric cards):**
- Points Per Game (PPG)
- Rebounds Per Game (RPG)
- Assists Per Game (APG)
- Field Goal % (FG%)
- Three-Point % (3PT%)

**Advanced Metrics (expandable section):**
- Offensive Rating — points scored per 100 possessions (simplified: PPG / pace * 100)
- Defensive Rating — points allowed per 100 possessions (simplified: opponent PPG / pace * 100)
- Net Rating — offensive rating minus defensive rating
- Pace — estimated possessions per game (simplified: (team FGA + 0.44 * team FTA + team TOV) - (opponent FGA + 0.44 * opponent FTA + opponent TOV))
- True Shooting % — PTS / (2 * (FGA + 0.44 * FTA))

These are computed from `team_game_logs` aggregations. If data is insufficient for precise calculations, simplified versions using available columns will be used.

**Recent Form:** Last 10 games for the team, displayed as W/L color-coded indicators (green = win, red = loss)

**Roster Snapshot:** Top 5 players on that team by PPG, pulled from `league_leaders`

### Data Sources

| Component | Table | Query Approach |
|-----------|-------|----------------|
| Standings | `team_stats` | Direct query, sorted by win% |
| Core stats | `team_stats` | Direct query per team |
| Advanced metrics | `team_stats` / `player_game_logs` | Derived computations |
| Recent form | `player_game_logs` | Aggregate by game_date, filter last 10 |
| Roster | `league_leaders` | Filter by team_abbreviation, order by PPG |

### Backend Endpoints

- `GET /teams` — returns all teams with standings data (W, L, Win%, etc.)
- `GET /teams/{team_name}` — returns team overview: core stats, advanced metrics, recent form, roster

### Frontend

- New tab: "🏆 Teams" (third tab position, after Shot Charts)
- Standings view → click team → team overview with back button
- Uses existing dark theme styling and metric card patterns

---

## Feature 2: Game Log Explorer Tab ("📅 Games")

### Entry Point

Filterable table of all games in the database.

### Filters

- **Team dropdown** — filter to a specific team's games (optional)
- **Result toggle** — All / Wins only / Losses only

### Table Columns

| Column | Description |
|--------|-------------|
| Date | Game date |
| Matchup | "vs LAL" or "BOS" (home/away indicator) |
| Result | W/L with color coding (green/red) |
| Points | Team's score for that game |
| Rebounds | Team total rebounds |
| Assists | Team total assists |
| +/- | Point differential |

### Data Source

**Primary source:** New `team_game_logs` table populated from `LeagueGameFinder` with `player_or_team_abbreviation="T"`. This gives team-level box scores directly (points, rebounds, assists, etc. per game per team).

**Pipeline change:** Update `data_pipeline.py` to fetch team game logs in addition to player game logs. This is a separate API call that returns complete team-level data.

**Note:** The `matchup` field from the NBA API contains values like "OKC vs. LAL" or "OKC @ BOS". Home/away is derived from the matchup format.

### Backend Endpoint

- `GET /games?team={team_name}&result={W|L}` — returns filtered, aggregated game logs

### Frontend

- New tab: "📅 Games" (fourth tab position)
- Filters at top, table below
- Uses existing dark theme styling and dataframe patterns

### Future Readiness

- Table structure supports player-level drill-down (Phase B): clicking a game row could expand to show individual stat lines
- Quarter-by-quarter breakdowns (Phase C) can be added later by extending the data model

---

## Removal: Auto-Insights

The following will be deleted:

- `backend/insights.py` — entire file
- `backend/main.py` — remove `GET /insights` endpoint and import
- `app.py` — remove insights section from SQL Analytics tab

---

## Architecture

### Backend Changes

**New files:**
- `backend/teams.py` — team standings and overview logic
- `backend/games.py` — game log aggregation and filtering

**Modified files:**
- `backend/main.py` — add `/teams` and `/games` endpoints, remove `/insights`
- `app.py` — add Teams and Games tabs, remove insights section
- `data_pipeline.py` — add team game logs fetching (new table `team_game_logs`)

**Deleted files:**
- `backend/insights.py`

**New database table:**
- `team_game_logs` — team-level game-by-game stats (date, matchup, W/L, points, rebounds, assists, etc.)

### Frontend Changes

**Modified file:** `app.py`

**New tabs:**
- "🏆 Teams" — standings table → team overview
- "📅 Games" — filterable game log table

**Removed:**
- Auto-insights section from SQL Analytics tab

### Data Flow

```
User selects tab
    ↓
Streamlit Frontend
    ↓ (HTTP)
FastAPI Backend
    ↓ (SQL)
SQLite Database
    ↓ (Results)
Backend Processing (Python)
    ↓ (JSON)
Frontend Visualization (Plotly / DataFrames)
```

**Gemini usage:** None — all features are pure SQL + Python.

---

## Error Handling

- All new endpoints return structured error responses
- Frontend handles 4xx/5xx with user-friendly messages
- Team overview gracefully handles missing data (e.g., no advanced metrics computed)
- Game log table shows empty state with message if no games match filters

## Testing

- Unit tests for new backend functions (teams.py, games.py)
- Integration tests for new endpoints
- Frontend smoke tests for new UI sections

---

## Success Criteria

1. **Data pipeline:** `team_game_logs` table populated successfully from NBA API
2. **Team Dashboard:** Standings load in <1 second, team overview renders with all stat cards
3. **Game Log Explorer:** Filtered table loads in <1 second, filters work correctly
4. **No Gemini calls** for any new features
5. **Auto-insights removed** — no remnants in codebase
6. **Existing features unaffected** — SQL Analytics, Shot Charts, AI Assistant still work

---

## Out of Scope

- Multi-season support (single season only)
- Player comparison tool (Phase 2A)
- Shot chart enhancements (Phase 2B)
- Player-level drill-down in game logs (future)
- Quarter-by-quarter breakdowns (future)
- Authentication/user accounts
- Real-time data updates
- Deployment/CI/CD setup
