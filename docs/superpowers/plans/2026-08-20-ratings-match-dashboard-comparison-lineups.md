# Player Ratings, Match Dashboard, Comparison & Lineup Optimizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four new features: a player rating system, a match dashboard with box scores, a player comparison tool, and a lineup optimizer.

**Architecture:** Four independent feature modules, each with its own backend file and frontend tab. Shared infrastructure: player rating formula used by match dashboard and comparison tool. New data pipeline fetches lineup data from `leaguedashlineups` endpoint.

**Tech Stack:** Python, FastAPI, Streamlit, SQLite, Plotly, NBA API (`nba_api`), `curl_cffi`

**Spec:** Brainstormed from user requirements (no formal spec document — features defined inline below)

## Global Constraints

- Single season only (`2025-26`)
- Zero Gemini API calls for all new features
- Follow existing code patterns (backend modules import `execute_query` from `sql_engine`, frontend uses `httpx` to call FastAPI)
- Existing tabs must remain functional
- Database: SQLite, file at `data/nba_data.db`
- NBA API requires `nba_api_compat` patch (curl_cffi TLS bypass)

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `backend/ratings.py` | Player rating computation (formula + per-game + season) |
| Create | `backend/matches.py` | Match dashboard: game box scores, team vs team, quarter scoring |
| Create | `backend/compare.py` | Player comparison: radar charts, head-to-head stats |
| Create | `backend/lineups.py` | Lineup optimizer: 5-man unit stats, on/off splits |
| Modify | `backend/main.py` | Add endpoints for all 4 features |
| Modify | `app.py` | Add 4 new tabs (Ratings, Matches, Compare, Lineups) |
| Modify | `data_pipeline.py` | Fetch lineup data from `leaguedashlineups` |
| Modify | `requirements.txt` | No new deps needed |

## Feature 1: Player Rating System

### Rating Formula

Context-aware player rating (0-100 scale), computed from `player_game_logs`:

```
base_rating = (PTS * 1.0 + REB * 1.2 + AST * 1.5 + STL * 2.0 + BLK * 2.0 - TOV * 1.0) / MIN * 36

efficiency_bonus = FG% * 10 + 3PT% * 5 + FT% * 3

clutch_bonus = 0  # Future: weight late-game performance higher

minutes_penalty = 0 if GP >= 40 else (40 - GP) * 0.5

rating = base_rating + efficiency_bonus - minutes_penalty
# Normalize to 0-100 scale
```

### Data Sources
- `league_leaders` — season averages for rating computation
- `player_game_logs` — per-game ratings for game log display

### Backend: `backend/ratings.py`

```python
def get_player_ratings(sort_by="rating", limit=50) -> dict:
    """
    Get all player ratings sorted by the rating formula.
    
    Returns dict with:
        - players: list of player dicts with name, team, rating, stats
        - columns: list of column names
    """

def get_player_rating_detail(player_name: str) -> dict:
    """
    Get detailed rating breakdown for a single player.
    
    Returns dict with:
        - player: player info dict
        - rating: overall rating
        - breakdown: component scores (scoring, rebounding, playmaking, defense, efficiency)
        - game_log: list of per-game ratings for trend chart
    """
```

### Frontend
- New tab: "⭐ Ratings"
- Default view: top 50 players by rating in a sortable table
- Click player → detail view with:
  - Overall rating (big number)
  - Radar chart of component scores
  - Game-by-game rating trend line (Plotly)
  - Season averages below

---

## Feature 2: Match Dashboard

### Data Sources
- `team_game_logs` — team-level box scores per game (has `game_id`)
- `player_game_logs` — player-level stats per game (link via `game_date` + `matchup`)
- `shot_chart` — shot locations per game (has `game_id`)

### Backend: `backend/matches.py`

```python
def get_match_list(team: str = None, date_from: str = None, date_to: str = None) -> dict:
    """
    Get list of games with scores and basic stats.
    
    Returns dict with:
        - matches: list of match dicts (date, matchup, score, result, team_stats)
        - total_count: number of matches
    """

def get_match_detail(game_id: str) -> dict:
    """
    Get full match detail: box scores for both teams, quarter scoring, shot chart.
    
    Returns dict with:
        - game: game info (date, matchup, final score)
        - home_team: {name, abbreviation, stats, player_stats}
        - away_team: {name, abbreviation, stats, player_stats}
        - quarter_scoring: list of quarter scores per team
        - ratings: player ratings for this game
    """
```

### Frontend
- Modify existing "📅 Games" tab or new "🏟️ Matches" tab
- Game list view: clickable rows
- Click game → match detail:
  - Scoreboard header (home vs away, final score)
  - Team stat comparison bar (PPG, RPG, APG, FG%)
  - Box score tables (both teams, sortable)
  - Player ratings column in box score
  - Quarter-by-quarter scoring chart (Plotly grouped bar)

---

## Feature 3: Player Comparison Tool

### Data Sources
- `league_leaders` — season averages for radar chart + stat comparison
- `player_game_logs` — head-to-head game log comparison

### Backend: `backend/compare.py`

```python
def get_player_stats(player_name: str) -> dict:
    """
    Get all stats for a player for comparison.
    
    Returns dict with:
        - player: player info (name, team, position)
        - season_stats: all season averages
        - rating: overall rating from ratings.py
        - radar_values: normalized values for radar chart (0-100 scale per category)
    """

def compare_players(player1: str, player2: str) -> dict:
    """
    Compare two players head-to-head.
    
    Returns dict with:
        - player1: player stats dict
        - player2: player stats dict
        - radar_comparison: overlapping radar data
        - stat_table: side-by-side stat comparison
        - verdict: which player is better in each category
    """
```

### Frontend
- New tab: "🔄 Compare"
- Two player selectboxes side by side
- On selection:
  - Overlapping radar chart (Plotly)
  - Side-by-side stat table with color coding
  - Verdict cards: "Better scorer: Player A", "Better playmaker: Player B"
  - Head-to-head if they played each other (game logs where matchup contains both)

---

## Feature 4: Lineup Optimizer

### Data Sources
- **New:** `leaguedashlineups` endpoint from NBA API → new `lineup_stats` table
- `team_stats` — team context

### Data Pipeline Update
Fetch lineup data from NBA API:
```python
from nba_api.stats.endpoints import leaguedashlineups

# This gives 5-man unit stats: MIN, OFF_RATING, DEF_RATING, NET_RATING, AST%, etc.
```

New table schema:
```sql
CREATE TABLE IF NOT EXISTS lineup_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER,
    team_abbreviation TEXT,
    lineup TEXT,  -- "Player1/Player2/Player3/Player4/Player5"
    games INTEGER,
    minutes REAL,
    points REAL,
    rebounds REAL,
    assists REAL,
    steals REAL,
    blocks REAL,
    turnovers REAL,
    fg_pct REAL,
    three_pct REAL,
    off_rating REAL,
    def_rating REAL,
    net_rating REAL,
    pace REAL
);
```

### Backend: `backend/lineups.py`

```python
def get_team_lineups(team_abbreviation: str, min_minutes: float = 50) -> dict:
    """
    Get lineup stats for a team, filtered by minimum minutes.
    
    Returns dict with:
        - team: team info
        - lineups: list of lineup dicts sorted by net_rating
        - total_lineups: number of qualifying lineups
    """

def get_league_best_lineups(min_minutes: float = 100, limit: int = 20) -> dict:
    """
    Get the best lineups in the league by net rating.
    
    Returns dict with:
        - lineups: list of lineup dicts with team context
        - total_count: number returned
    """

def get_lineup_comparison(team1: str, team2: str) -> dict:
    """
    Compare lineups between two teams.
    
    Returns dict with:
        - team1_lineups: top lineups for team 1
        - team2_lineups: top lineups for team 2
        - comparison: key differences
    """
```

### Frontend
- New tab: "🔧 Lineups"
- Default view: league-wide best lineups table
- Team filter dropdown
- Click lineup → expandable details:
  - 5-player names
  - Net rating, offensive/defensive rating
  - Pace, minutes played
  - Comparison to team average
- Team comparison mode: select two teams, side-by-side lineup comparison

---

## Backend Endpoint Additions to `main.py`

```python
# Ratings Endpoints
@app.get("/ratings")
async def list_player_ratings(sort_by: str = "rating", limit: int = 50)

@app.get("/ratings/{player_name}")
async def get_player_rating_detail(player_name: str)

# Match Endpoints
@app.get("/matches")
async def list_matches(team: str = None, date_from: str = None, date_to: str = None)

@app.get("/matches/{game_id}")
async def get_match_detail(game_id: str)

# Compare Endpoints
@app.get("/compare/stats/{player_name}")
async def get_comparison_stats(player_name: str)

@app.get("/compare/{player1}/{player2}")
async def compare_two_players(player1: str, player2: str)

# Lineup Endpoints
@app.get("/lineups/{team_name}")
async def get_team_lineups(team_name: str, min_minutes: float = 50)

@app.get("/lineups/league/best")
async def get_best_lineups(min_minutes: float = 100, limit: int = 20)

@app.get("/lineups/compare/{team1}/{team2}")
async def compare_team_lineups(team1: str, team2: str)
```

---

## Task Breakdown

### Task 1: Player Rating System Backend
**Files:** Create `backend/ratings.py`, Modify `backend/main.py`
**Interfaces:** Consumes `league_leaders`, `player_game_logs` tables. Produces `get_player_ratings()`, `get_player_rating_detail()`.
- [ ] Create `backend/ratings.py` with rating formula
- [ ] Add `/ratings` and `/ratings/{player_name}` endpoints to `main.py`
- [ ] Test: verify ratings return correct data for top players
- [ ] Commit

### Task 2: Player Rating System Frontend
**Files:** Modify `app.py`
**Interfaces:** Consumes `/ratings` and `/ratings/{player_name}` endpoints.
- [ ] Add "⭐ Ratings" tab with player table
- [ ] Add player detail view with radar chart + trend line
- [ ] Test: verify tab renders and player drill-down works
- [ ] Commit

### Task 3: Player Comparison Tool Backend
**Files:** Create `backend/compare.py`, Modify `backend/main.py`
**Interfaces:** Consumes `league_leaders` tables, `get_player_ratings()` from Task 1. Produces `get_player_stats()`, `compare_players()`.
- [ ] Create `backend/compare.py` with comparison logic
- [ ] Add `/compare/stats/{player_name}` and `/compare/{player1}/{player2}` endpoints
- [ ] Test: verify comparison returns correct side-by-side data
- [ ] Commit

### Task 4: Player Comparison Tool Frontend
**Files:** Modify `app.py`
**Interfaces:** Consumes `/compare/stats/{player_name}` and `/compare/{player1}/{player2}` endpoints.
- [ ] Add "🔄 Compare" tab with two player selectboxes
- [ ] Add radar chart overlay + stat table + verdict cards
- [ ] Test: verify comparison renders correctly
- [ ] Commit

### Task 5: Match Dashboard Backend
**Files:** Create `backend/matches.py`, Modify `backend/main.py`
**Interfaces:** Consumes `team_game_logs`, `player_game_logs`, `shot_chart` tables. Produces `get_match_list()`, `get_match_detail()`.
- [ ] Create `backend/matches.py` with match logic
- [ ] Add `/matches` and `/matches/{game_id}` endpoints
- [ ] Test: verify match detail returns box scores and quarter data
- [ ] Commit

### Task 6: Match Dashboard Frontend
**Files:** Modify `app.py`
**Interfaces:** Consumes `/matches` and `/matches/{game_id}` endpoints.
- [ ] Add "🏟️ Matches" tab with game list
- [ ] Add match detail view with scoreboard, box scores, quarter chart
- [ ] Integrate player ratings into box score
- [ ] Test: verify match detail renders correctly
- [ ] Commit

### Task 7: Lineup Data Pipeline
**Files:** Modify `data_pipeline.py`
**Interfaces:** Consumes `leaguedashlineups` endpoint. Produces `lineup_stats` table.
- [ ] Add `lineup_stats` table schema to `init_database`
- [ ] Add `fetch_lineup_stats()` function
- [ ] Add to `REQUIRED_TABLES` and `run_pipeline()`
- [ ] Run pipeline to populate data
- [ ] Commit

### Task 8: Lineup Optimizer Backend
**Files:** Create `backend/lineups.py`, Modify `backend/main.py`
**Interfaces:** Consumes `lineup_stats`, `team_stats` tables. Produces `get_team_lineups()`, `get_league_best_lineups()`, `get_lineup_comparison()`.
- [ ] Create `backend/lineups.py` with lineup logic
- [ ] Add `/lineups/{team_name}`, `/lineups/league/best`, `/lineups/compare/{team1}/{team2}` endpoints
- [ ] Test: verify lineup data returns correctly
- [ ] Commit

### Task 9: Lineup Optimizer Frontend
**Files:** Modify `app.py`
**Interfaces:** Consumes `/lineups/{team_name}`, `/lineups/league/best`, `/lineups/compare/{team1}/{team2}` endpoints.
- [ ] Add "🔧 Lineups" tab with league-wide table
- [ ] Add team filter and lineup detail expandable
- [ ] Add team comparison mode
- [ ] Test: verify lineup tab renders correctly
- [ ] Commit

### Task 10: End-to-End Verification
**Files:** None (verification only)
- [ ] Verify all 4 new tabs render without errors
- [ ] Verify all new endpoints return valid data
- [ ] Verify existing tabs still work
- [ ] Update README with new features
- [ ] Commit

---

## Execution Order

Tasks 1-2 (Ratings) → Tasks 3-4 (Comparison) → Tasks 5-6 (Matches) → Tasks 7-9 (Lineups) → Task 10 (Verification)

Each pair (backend + frontend) is independent and can be built separately. The comparison tool depends on ratings (Task 1), but all others are independent.
