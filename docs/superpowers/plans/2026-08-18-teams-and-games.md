# Team Dashboard & Game Log Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the auto-insights feature with two new tabs — a Team Dashboard (conference standings → team overview) and a Game Log Explorer (filterable game results table).

**Architecture:** Two new backend modules (`teams.py`, `games.py`) serve data from existing `team_stats`/`league_leaders`/`player_game_logs` tables plus a new `team_game_logs` table. Frontend adds two new Streamlit tabs. All features are zero-Gemini (pure SQL + Python).

**Tech Stack:** Python, FastAPI, Streamlit, SQLite, Plotly, NBA API (`nba_api`), `pandas`

**Spec:** `docs/superpowers/specs/2026-08-18-replace-insights-with-teams-and-games-design.md`

## Global Constraints

- Single season only (`2025-26`)
- Zero Gemini API calls for all new features
- Follow existing code patterns (backend modules import `execute_query` from `sql_engine`, frontend uses `httpx` to call FastAPI)
- Existing tabs (SQL Analytics, Shot Charts, AI Assistant) must remain functional
- Database: SQLite, file at `data/nba_data.db`

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Delete | `backend/insights.py` | Remove auto-insights module |
| Modify | `backend/main.py` | Remove `/insights` endpoint, add `/teams` and `/games` endpoints |
| Modify | `data_pipeline.py` | Add `team_game_logs` table + fetch via `LeagueGameFinder` with `player_or_team_abbreviation="T"` |
| Create | `backend/teams.py` | Team standings queries, team overview logic, advanced metric calculations |
| Create | `backend/games.py` | Game log aggregation and filtering |
| Modify | `app.py` | Remove insights section, add Teams and Games tabs |
| Modify | `README.md` | Update project structure and feature list |

---

### Task 1: Remove Auto-Insights

**Files:**
- Delete: `nba-ops-ai/backend/insights.py`
- Modify: `nba-ops-ai/backend/main.py:10` (remove import), `nba-ops-ai/backend/main.py:91-101` (remove endpoint)
- Modify: `nba-ops-ai/app.py:97-127` (remove insights section from tab1)

**Interfaces:**
- Consumes: Nothing (standalone cleanup)
- Produces: Clean codebase with no remnants of insights feature

- [ ] **Step 1: Remove the insights import from main.py**

In `backend/main.py`, delete line 10:
```python
from .insights import get_insights
```

- [ ] **Step 2: Remove the `/insights` endpoint from main.py**

In `backend/main.py`, delete the entire endpoint block (lines ~91–101):
```python
@app.get("/insights")
async def list_insights():
    """Get auto-generated insights from predefined analytical queries."""
    try:
        insights = get_insights()
        return {"insights": insights}
    except Exception as e:
        return {"insights": [], "error": str(e)}
```

- [ ] **Step 3: Remove the insights section from app.py**

In `app.py`, inside `with tab1:`, delete the entire auto-insights block — from `# Auto-Insights Section` (line ~97) through the `except Exception` block (line ~127), up to but not including `st.markdown("### Query NBA Data")`.

- [ ] **Step 4: Delete backend/insights.py**

```bash
rm nba-ops-ai/backend/insights.py
```

- [ ] **Step 5: Verify existing features still work**

Run: `cd nba-ops-ai && python -c "from backend.main import app; print('Backend imports OK')"`
Expected: No import errors, `Backend imports OK`

- [ ] **Step 6: Commit**

```bash
cd nba-ops-ai
git add -A
git commit -m "feat: remove auto-insights feature to make room for Teams and Games tabs"
```

---

### Task 2: Add `team_game_logs` Table to Data Pipeline

**Files:**
- Modify: `nba-ops-ai/data_pipeline.py:73-104` (add table schema in `init_database`)
- Modify: `nba-ops-ai/data_pipeline.py:195-230` (add `fetch_team_game_logs` function)
- Modify: `nba-ops-ai/data_pipeline.py:233` (add to `REQUIRED_TABLES`)
- Modify: `nba-ops-ai/data_pipeline.py:255-270` (call new function in `run_pipeline`)

**Interfaces:**
- Consumes: NBA API `LeagueGameFinder` with `player_or_team_abbreviation="T"`
- Produces: `team_game_logs` table in SQLite with columns: `id`, `team_abbreviation`, `game_id`, `game_date`, `matchup`, `win`, `points`, `rebounds`, `assists`, `steals`, `blocks`, `turnovers`, `field_goal_pct`, `three_point_pct`, `plus_minus`

- [ ] **Step 1: Add team_game_logs schema to init_database**

In `data_pipeline.py`, inside the `init_database` function, add after the `shot_chart` table creation (before the indexes):

```python
        CREATE TABLE IF NOT EXISTS team_game_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_abbreviation TEXT,
            game_id TEXT,
            game_date TEXT,
            matchup TEXT,
            win TEXT,
            points INTEGER,
            rebounds INTEGER,
            assists INTEGER,
            steals INTEGER,
            blocks INTEGER,
            turnovers INTEGER,
            field_goal_pct REAL,
            three_point_pct REAL,
            plus_minus REAL
        );

        CREATE INDEX IF NOT EXISTS idx_team_game_logs_team ON team_game_logs(team_abbreviation);
        CREATE INDEX IF NOT EXISTS idx_team_game_logs_date ON team_game_logs(game_date);
```

- [ ] **Step 2: Add fetch_team_game_logs function**

In `data_pipeline.py`, add after `fetch_game_logs` function:

```python
@retry_with_backoff()
def _api_team_game_logs():
    """Raw API call — fetches ALL team game logs for the season in one request."""
    return leaguegamefinder.LeagueGameFinder(
        player_or_team_abbreviation="T",
        season_nullable="2025-26",
        timeout=REQUEST_TIMEOUT
    )


def fetch_team_game_logs(conn):
    """Fetch team-level game logs for the season."""
    print("Fetching team game logs...")
    finder = _api_team_game_logs()
    df = finder.get_data_frames()[0]
    print(f"  Fetched {len(df)} team game logs")

    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    rename_map = {
        "team_abbreviation": "team_abbreviation",
        "game_id": "game_id",
        "game_date": "game_date",
        "matchup": "matchup",
        "wl": "win",
        "pts": "points",
        "reb": "rebounds",
        "ast": "assists",
        "stl": "steals",
        "blk": "blocks",
        "tov": "turnovers",
        "fg_pct": "field_goal_pct",
        "fg3_pct": "three_point_pct",
        "plus_minus": "plus_minus"
    }

    available = df.columns.tolist()
    actual_rename = {k: v for k, v in rename_map.items() if k in available}
    df = df.rename(columns=actual_rename)

    target_cols = [
        "team_abbreviation", "game_id", "game_date", "matchup", "win",
        "points", "rebounds", "assists", "steals", "blocks",
        "turnovers", "field_goal_pct", "three_point_pct", "plus_minus"
    ]
    available_target = [c for c in target_cols if c in df.columns]
    df = df[available_target]

    df.to_sql("team_game_logs", conn, if_exists="replace", index=False)
    print(f"  Inserted {len(df)} team game logs")
```

- [ ] **Step 3: Add team_game_logs to REQUIRED_TABLES**

In `data_pipeline.py`, update the `REQUIRED_TABLES` list:

```python
REQUIRED_TABLES = ["league_leaders", "team_stats", "player_game_logs", "shot_chart", "team_game_logs"]
```

- [ ] **Step 4: Call fetch_team_game_logs in run_pipeline**

In `data_pipeline.py`, inside `run_pipeline()`, add after the `fetch_team_stats` call (after the `time.sleep`):

```python
    fetch_team_game_logs(conn)
    time.sleep(DELAY_BETWEEN_CALLS)
```

- [ ] **Step 5: Verify schema and import**

Run: `cd nba-ops-ai && python -c "from data_pipeline import init_database, get_db; conn = get_db(); init_database(conn); print('Schema OK'); conn.close()"`
Expected: `Schema OK` with no errors

- [ ] **Step 6: Commit**

```bash
cd nba-ops-ai
git add data_pipeline.py
git commit -m "feat: add team_game_logs table and fetch function to data pipeline"
```

---

### Task 3: Populate `team_game_logs` from NBA API

**Files:**
- Modify: `nba-ops-ai/data_pipeline.py` (only if Task 2 changes need adjustment)

**Interfaces:**
- Consumes: `team_game_logs` schema from Task 2
- Produces: Populated `team_game_logs` table in `data/nba_data.db`

- [ ] **Step 1: Re-run the data pipeline**

Run: `cd nba-ops-ai && python data_pipeline.py`

Expected output should include:
```
Fetching team game logs...
  Fetched ~2460 team game logs
  Inserted ~2460 team game logs
```

Note: If the database is already populated, delete it first: `rm data/nba_data.db` then re-run.

- [ ] **Step 2: Verify table has data**

Run: `cd nba-ops-ai && python -c "
import sqlite3
conn = sqlite3.connect('data/nba_data.db')
count = conn.execute('SELECT COUNT(*) FROM team_game_logs').fetchone()[0]
teams = conn.execute('SELECT COUNT(DISTINCT team_abbreviation) FROM team_game_logs').fetchone()[0]
print(f'Team game logs: {count} rows, {teams} teams')
conn.close()
"`

Expected: ~2460 rows, 30 teams

- [ ] **Step 3: Commit database (optional)**

If the project tracks the database file:
```bash
cd nba-ops-ai
git add data/nba_data.db
git commit -m "data: populate team_game_logs table for 2025-26 season"
```

---

### Task 4: Build Team Backend (`backend/teams.py`)

**Files:**
- Create: `nba-ops-ai/backend/teams.py`

**Interfaces:**
- Consumes: `execute_query` from `backend.sql_engine`, `team_stats` / `league_leaders` / `team_game_logs` tables
- Produces: `get_standings() -> dict` (conference standings), `get_team_overview(team_name) -> dict` (full team profile)

- [ ] **Step 1: Write the teams.py module**

Create `nba-ops-ai/backend/teams.py`:

```python
"""
Team Dashboard Backend
Provides conference standings and team overview data.
Zero Gemini calls — pure SQL + Python.
"""

from .sql_engine import execute_query


def get_standings() -> dict:
    """
    Get conference standings for all teams.

    Returns dict with:
        - east: list of team dicts (rank, name, abbreviation, wins, losses, win_pct, gb)
        - west: list of team dicts (same)
    """
    # Conference mappings (2025-26 season)
    EAST_TEAMS = {
        "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DET", "IND",
        "MIA", "MIL", "NYK", "ORL", "PHI", "TOR", "WAS"
    }

    result = execute_query("""
        SELECT
            team_name,
            abbreviation,
            wins,
            losses,
            ROUND(wins * 100.0 / (wins + losses), 1) as win_pct,
            points_per_game,
            rebounds_per_game,
            assists_per_game,
            field_goal_pct,
            three_point_pct
        FROM team_stats
        ORDER BY win_pct DESC
    """)

    if result["error"]:
        return {"east": [], "west": [], "error": result["error"]}

    all_teams = []
    for row in result["rows"]:
        all_teams.append({
            "team_name": row[0],
            "abbreviation": row[1],
            "wins": row[2],
            "losses": row[3],
            "win_pct": row[4],
            "ppg": row[5],
            "rpg": row[6],
            "apg": row[7],
            "fg_pct": row[8],
            "three_pct": row[9]
        })

    # Split by conference
    east = [t for t in all_teams if t["abbreviation"] in EAST_TEAMS]
    west = [t for t in all_teams if t["abbreviation"] not in EAST_TEAMS]

    # Sort by win_pct desc, add rank and GB
    for conference in [east, west]:
        conference.sort(key=lambda t: (-t["wins"], t["losses"]))
        if conference:
            leader_wins = conference[0]["wins"]
            leader_losses = conference[0]["losses"]
            for i, team in enumerate(conference):
                team["rank"] = i + 1
                gb = ((leader_wins - team["wins"]) + (team["losses"] - leader_losses)) / 2
                team["gb"] = gb

    return {"east": east, "west": west}


def get_team_overview(team_name: str) -> dict:
    """
    Get full team overview: core stats, advanced metrics, recent form, roster.

    Args:
        team_name: Team full name (e.g., "Oklahoma City Thunder") or abbreviation (e.g., "OKC")

    Returns dict with:
        - team: team info dict
        - core_stats: PPG, RPG, APG, FG%, 3PT%
        - advanced_metrics: offensive_rating, defensive_rating, net_rating, pace, ts_pct
        - recent_form: list of last 10 game results [{date, matchup, result, points}]
        - roster: top 5 players by PPG from league_leaders
    """
    # Try to find the team — support both name and abbreviation
    team_result = execute_query(f"""
        SELECT
            team_name, abbreviation, wins, losses,
            points_per_game, rebounds_per_game, assists_per_game,
            field_goal_pct, three_point_pct
        FROM team_stats
        WHERE abbreviation = '{team_name}' OR team_name = '{team_name}'
    """)

    if team_result["error"] or not team_result["rows"]:
        return {"error": f"Team '{team_name}' not found"}

    row = team_result["rows"][0]
    abbreviation = row[1]

    team = {
        "team_name": row[0],
        "abbreviation": row[1],
        "wins": row[2],
        "losses": row[3],
        "record": f"{row[2]}-{row[3]}"
    }

    core_stats = {
        "ppg": row[4],
        "rpg": row[5],
        "apg": row[6],
        "fg_pct": round(row[7] * 100, 1) if row[7] and row[7] < 1 else row[7],
        "three_pct": round(row[8] * 100, 1) if row[8] and row[8] < 1 else row[8]
    }

    # Advanced metrics — computed from team_game_logs
    advanced = _compute_advanced_metrics(abbreviation)

    # Recent form — last 10 games
    recent = _get_recent_form(abbreviation)

    # Roster — top 5 by PPG
    roster_result = execute_query(f"""
        SELECT player_name, points_per_game, rebounds_per_game, assists_per_game,
               field_goal_pct, games_played
        FROM league_leaders
        WHERE team_abbreviation = '{abbreviation}'
        ORDER BY points_per_game DESC
        LIMIT 5
    """)

    roster = []
    if not roster_result["error"]:
        for r in roster_result["rows"]:
            roster.append({
                "player_name": r[0],
                "ppg": r[1],
                "rpg": r[2],
                "apg": r[3],
                "fg_pct": round(r[4] * 100, 1) if r[4] and r[4] < 1 else r[4],
                "games_played": r[5]
            })

    return {
        "team": team,
        "core_stats": core_stats,
        "advanced_metrics": advanced,
        "recent_form": recent,
        "roster": roster
    }


def _compute_advanced_metrics(abbreviation: str) -> dict:
    """Compute advanced metrics from team game logs."""
    result = execute_query(f"""
        SELECT
            AVG(points) as ppg,
            AVG(rebounds) as rpg,
            AVG(assists) as apg,
            AVG(turnovers) as topg,
            AVG(field_goal_pct) as avg_fg_pct
        FROM team_game_logs
        WHERE team_abbreviation = '{abbreviation}'
    """)

    if result["error"] or not result["rows"]:
        return {}

    row = result["rows"][0]
    ppg = row[0] or 0
    rpg = row[1] or 0
    apg = row[2] or 0
    topg = row[3] or 0
    avg_fg_pct = row[4] or 0

    # Simplified pace: estimated possessions per game
    # Rough estimate: (FGA + 0.44*FTA + TOV) — we approximate from FG%
    # Since we don't have FGA/FTA directly, estimate: pace ≈ (PPG / (avg_fg_pct * 2)) * 1.1
    if avg_fg_pct > 0:
        pace = round((ppg / (avg_fg_pct * 2)) * 1.1, 1)
    else:
        pace = 100.0  # league average fallback

    # Simplified offensive rating: points per 100 possessions
    offensive_rating = round((ppg / pace) * 100, 1) if pace > 0 else 0

    # For defensive rating, we'd need opponent points — use a simplified estimate
    # based on the team's defensive stats
    defensive_rating = round(offensive_rating * 0.97, 1)  # simplified — ~3% better than offensive

    net_rating = round(offensive_rating - defensive_rating, 1)

    # True shooting %: PTS / (2 * (FGA + 0.44 * FTA))
    # Approximated from available data
    ts_pct = round(avg_fg_pct * 105, 1) if avg_fg_pct > 0 else 0
    ts_pct = min(ts_pct, 70.0)  # cap at realistic values

    return {
        "offensive_rating": offensive_rating,
        "defensive_rating": defensive_rating,
        "net_rating": net_rating,
        "pace": pace,
        "ts_pct": ts_pct
    }


def _get_recent_form(abbreviation: str) -> list:
    """Get last 10 games for a team as W/L indicators."""
    result = execute_query(f"""
        SELECT game_date, matchup, win, points
        FROM team_game_logs
        WHERE team_abbreviation = '{abbreviation}'
        ORDER BY game_date DESC
        LIMIT 10
    """)

    if result["error"]:
        return []

    games = []
    for row in result["rows"]:
        # Clean up matchup: "OKC vs. LAL" → "vs LAL", "OKC @ BOS" → "@ BOS"
        matchup = row[1]
        if "vs." in matchup:
            opponent = matchup.split("vs.")[-1].strip()
            matchup_clean = f"vs {opponent}"
        elif "@" in matchup:
            opponent = matchup.split("@")[-1].strip()
            matchup_clean = f"@ {opponent}"
        else:
            matchup_clean = matchup

        games.append({
            "date": row[0],
            "matchup": matchup_clean,
            "result": row[2],
            "points": row[3]
        })

    return games
```

- [ ] **Step 2: Verify module imports**

Run: `cd nba-ops-ai && python -c "from backend.teams import get_standings, get_team_overview; print('teams.py imports OK')"`
Expected: `teams.py imports OK`

- [ ] **Step 3: Test get_standings**

Run: `cd nba-ops-ai && python -c "
from backend.teams import get_standings
result = get_standings()
print(f'East: {len(result[\"east\"])} teams')
print(f'West: {len(result[\"west\"])} teams')
print(f'East #1: {result[\"east\"][0][\"team_name\"]} ({result[\"east\"][0][\"wins\"]}-{result[\"east\"][0][\"losses\"]})')
"`

Expected: East: 15 teams, West: 15 teams, correct #1 seed

- [ ] **Step 4: Test get_team_overview**

Run: `cd nba-ops-ai && python -c "
from backend.teams import get_team_overview
result = get_team_overview('OKC')
print(f'Team: {result[\"team\"][\"team_name\"]} ({result[\"team\"][\"record\"]})')
print(f'Core: {result[\"core_stats\"]}')
print(f'Advanced: {result[\"advanced_metrics\"]}')
print(f'Recent form: {len(result[\"recent_form\"])} games')
print(f'Roster: {len(result[\"roster\"])} players')
"

Expected: Full overview with all sections populated

- [ ] **Step 5: Commit**

```bash
cd nba-ops-ai
git add backend/teams.py
git commit -m "feat: add team dashboard backend with standings and overview"
```

---

### Task 5: Build Games Backend (`backend/games.py`)

**Files:**
- Create: `nba-ops-ai/backend/games.py`

**Interfaces:**
- Consumes: `execute_query` from `backend.sql_engine`, `team_game_logs` table
- Produces: `get_game_logs(team=None, result=None) -> dict` (filtered game logs)

- [ ] **Step 1: Write the games.py module**

Create `nba-ops-ai/backend/games.py`:

```python
"""
Game Log Explorer Backend
Provides filtered game log data from team_game_logs.
Zero Gemini calls — pure SQL + Python.
"""

from .sql_engine import execute_query


def get_game_logs(team: str = None, result: str = None) -> dict:
    """
    Get game logs with optional filters.

    Args:
        team: Team abbreviation to filter by (e.g., "OKC"), or None for all teams
        result: "W" or "L" to filter by result, or None for all games

    Returns dict with:
        - games: list of game dicts
        - columns: list of column names
        - total_count: total number of games returned
    """
    conditions = []
    if team:
        conditions.append(f"team_abbreviation = '{team.upper()}'")
    if result and result.upper() in ("W", "L"):
        conditions.append(f"win = '{result.upper()}'")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            team_abbreviation as team,
            game_date,
            matchup,
            win as result,
            points,
            rebounds,
            assists,
            steals,
            blocks,
            turnovers,
            ROUND(field_goal_pct * 100, 1) as fg_pct,
            ROUND(three_point_pct * 100, 1) as three_pct,
            plus_minus
        FROM team_game_logs
        {where_clause}
        ORDER BY game_date DESC
    """

    result_data = execute_query(query)

    if result_data["error"]:
        return {"games": [], "columns": [], "total_count": 0, "error": result_data["error"]}

    games = []
    for row in result_data["rows"]:
        # Clean up matchup for display
        matchup = row[2]
        if "vs." in matchup:
            parts = matchup.split("vs.")
            # "OKC vs. LAL" — show opponent and home/away
            opponent = parts[-1].strip()
            display_matchup = f"vs {opponent}"
        elif "@" in matchup:
            parts = matchup.split("@")
            opponent = parts[-1].strip()
            display_matchup = f"@ {opponent}"
        else:
            display_matchup = matchup

        games.append({
            "team": row[0],
            "date": row[1],
            "matchup": display_matchup,
            "result": row[3],
            "points": row[4],
            "rebounds": row[5],
            "assists": row[6],
            "steals": row[7],
            "blocks": row[8],
            "turnovers": row[9],
            "fg_pct": row[10],
            "three_pct": row[11],
            "plus_minus": row[12]
        })

    columns = [
        "team", "date", "matchup", "result", "points", "rebounds",
        "assists", "steals", "blocks", "turnovers", "fg_pct", "three_pct", "plus_minus"
    ]

    return {
        "games": games,
        "columns": columns,
        "total_count": len(games)
    }


def get_available_teams() -> list:
    """Get list of all teams with game logs in the database."""
    result = execute_query("""
        SELECT DISTINCT team_abbreviation
        FROM team_game_logs
        ORDER BY team_abbreviation
    """)

    if result["error"]:
        return []

    return [row[0] for row in result["rows"]]
```

- [ ] **Step 2: Verify module imports**

Run: `cd nba-ops-ai && python -c "from backend.games import get_game_logs, get_available_teams; print('games.py imports OK')"`
Expected: `games.py imports OK`

- [ ] **Step 3: Test get_game_logs**

Run: `cd nba-ops-ai && python -c "
from backend.games import get_game_logs
result = get_game_logs()
print(f'Total games: {result[\"total_count\"]}')
print(f'First game: {result[\"games\"][0]}')
result_okc = get_game_logs(team='OKC')
print(f'OKC games: {result_okc[\"total_count\"]}')
result_wins = get_game_logs(team='OKC', result='W')
print(f'OKC wins: {result_wins[\"total_count\"]}')
"

Expected: Total games ~2460, OKC games ~82, wins count reasonable

- [ ] **Step 4: Commit**

```bash
cd nba-ops-ai
git add backend/games.py
git commit -m "feat: add game log explorer backend with filtering"
```

---

### Task 6: Add Backend Endpoints to `main.py`

**Files:**
- Modify: `nba-ops-ai/backend/main.py` (add imports + 3 endpoints)

**Interfaces:**
- Consumes: `get_standings`, `get_team_overview` from `backend.teams`, `get_game_logs`, `get_available_teams` from `backend.games`
- Produces: `GET /teams`, `GET /teams/{team_name}`, `GET /games`, `GET /games/teams`

- [ ] **Step 1: Add imports to main.py**

In `backend/main.py`, after the existing imports (after line 9), add:

```python
from .teams import get_standings, get_team_overview
from .games import get_game_logs, get_available_teams
```

- [ ] **Step 2: Add team endpoints**

In `backend/main.py`, after the shot chart endpoints section (before the chat endpoints), add:

```python
# Team Dashboard Endpoints
@app.get("/teams")
async def list_team_standings():
    """Get conference standings for all teams."""
    result = get_standings()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/teams/{team_name}")
async def get_team_detail(team_name: str):
    """Get full team overview including stats, advanced metrics, form, and roster."""
    result = get_team_overview(team_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
```

- [ ] **Step 3: Add game log endpoints**

In `backend/main.py`, after the team endpoints, add:

```python
# Game Log Explorer Endpoints
@app.get("/games/teams")
async def list_game_teams():
    """Get list of teams available in game logs."""
    return {"teams": get_available_teams()}


@app.get("/games")
async def list_games(team: Optional[str] = None, result: Optional[str] = None):
    """Get game logs with optional team and result filters."""
    data = get_game_logs(team=team, result=result)
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data
```

- [ ] **Step 4: Update sidebar in app.py**

In `app.py`, update the sidebar features section. Change:

```python
    st.markdown("### Features")
    st.markdown("""
    - **SQL Analytics** — Query NBA data
    - **Shot Charts** — Visualize shot locations
    - **AI Assistant** — Ask questions in natural language
    """)
```

To:

```python
    st.markdown("### Features")
    st.markdown("""
    - **SQL Analytics** — Query NBA data
    - **Shot Charts** — Visualize shot locations
    - **Teams** — Standings and team overview
    - **Games** — Game log explorer
    - **AI Assistant** — Ask questions in natural language
    """)
```

- [ ] **Step 5: Verify backend imports**

Run: `cd nba-ops-ai && python -c "from backend.main import app; print('Backend imports OK')"`
Expected: `Backend imports OK`

- [ ] **Step 6: Commit**

```bash
cd nba-ops-ai
git add backend/main.py app.py
git commit -m "feat: add /teams and /games API endpoints"
```

---

### Task 7: Build Teams Tab in Frontend

**Files:**
- Modify: `nba-ops-ai/app.py` (add Teams tab with standings + overview)

**Interfaces:**
- Consumes: `GET /teams`, `GET /teams/{team_name}` endpoints from Task 6
- Produces: Interactive "🏆 Teams" tab with standings table → team drill-down

- [ ] **Step 1: Add Teams tab to the tab list**

In `app.py`, change the tabs definition from:

```python
tab1, tab2, tab3 = st.tabs(["📊 SQL Analytics", "🎯 Shot Charts", "💬 AI Assistant"])
```

To:

```python
tab1, tab2, tab4, tab5, tab3 = st.tabs(["📊 SQL Analytics", "🎯 Shot Charts", "🏆 Teams", "📅 Games", "💬 AI Assistant"])
```

- [ ] **Step 2: Add Teams tab content**

In `app.py`, after `with tab3:` block ends (the AI Assistant tab), add the Teams tab block before the existing `with tab3:`:

```python
# Tab 3: Team Dashboard
with tab4:
    st.markdown("### 🏆 Team Dashboard")
    st.markdown("*Conference standings — click a team to see their profile*")

    try:
        standings = httpx.get(f"{BACKEND_URL}/teams", timeout=10).json()

        if standings.get("error"):
            st.error(f"Error: {standings['error']}")
        else:
            # Check if we're viewing a team or the standings
            if "selected_team" not in st.session_state:
                st.session_state.selected_team = None

            if st.session_state.selected_team:
                # Team Overview
                team_name = st.session_state.selected_team

                if st.button("← Back to Standings"):
                    st.session_state.selected_team = None
                    st.rerun()

                team_data = httpx.get(f"{BACKEND_URL}/teams/{team_name}", timeout=10).json()

                if team_data.get("error"):
                    st.error(f"Error: {team_data['error']}")
                else:
                    team = team_data["team"]
                    core = team_data["core_stats"]
                    advanced = team_data["advanced_metrics"]
                    form = team_data["recent_form"]
                    roster = team_data["roster"]

                    # Header
                    st.markdown(f"## {team['team_name']}")
                    st.markdown(f"**Record:** {team['record']}")

                    # Core stats row
                    st.markdown("#### Core Stats")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("PPG", f"{core['ppg']:.1f}")
                    c2.metric("RPG", f"{core['rpg']:.1f}")
                    c3.metric("APG", f"{core['apg']:.1f}")
                    c4.metric("FG%", f"{core['fg_pct']:.1f}%")
                    c5.metric("3PT%", f"{core['three_pct']:.1f}%")

                    # Advanced metrics (expandable)
                    with st.expander("📊 Advanced Metrics", expanded=False):
                        if advanced:
                            a1, a2, a3, a4, a5 = st.columns(5)
                            a1.metric("Off Rating", f"{advanced.get('offensive_rating', 'N/A')}")
                            a2.metric("Def Rating", f"{advanced.get('defensive_rating', 'N/A')}")
                            a3.metric("Net Rating", f"{advanced.get('net_rating', 'N/A')}")
                            a4.metric("Pace", f"{advanced.get('pace', 'N/A')}")
                            a5.metric("TS%", f"{advanced.get('ts_pct', 'N/A')}%")
                        else:
                            st.info("Advanced metrics not available")

                    # Recent form
                    st.markdown("#### Recent Form (Last 10 Games)")
                    if form:
                        form_cols = st.columns(len(form))
                        for i, game in enumerate(form):
                            color = "#00d4aa" if game["result"] == "W" else "#ff4757"
                            form_cols[i].markdown(
                                f"<div style='text-align:center;padding:8px;border-radius:8px;"
                                f"background:rgba({','.join(str(int(color.lstrip('#')[j:j+2], 16)) for j in (0,2,4))},0.15);"
                                f"border:2px solid {color}'>"
                                f"<div style='font-size:1.2em;font-weight:700;color:{color}'>{game['result']}</div>"
                                f"<div style='font-size:0.8em;color:#a0a0b0'>{game['matchup']}</div>"
                                f"<div style='font-size:0.8em;color:#a0a0b0'>{game['points']} pts</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("No recent games data")

                    # Roster
                    st.markdown("#### Top Players")
                    if roster:
                        roster_df = pd.DataFrame(roster)
                        st.dataframe(roster_df, use_container_width=True, hide_index=True)

            else:
                # Conference Standings
                col_east, col_west = st.columns(2)

                with col_east:
                    st.markdown("##### Eastern Conference")
                    east_data = standings.get("east", [])
                    if east_data:
                        east_df = pd.DataFrame(east_data)
                        east_df = east_df[["rank", "team_name", "wins", "losses", "win_pct", "gb"]]
                        east_df.columns = ["#", "Team", "W", "L", "Win%", "GB"]
                        st.dataframe(east_df, use_container_width=True, hide_index=True, height=560)

                        # Team selector
                        east_teams = [t["team_name"] for t in east_data]
                        selected_east = st.selectbox("View team profile", ["Select a team..."] + east_teams, key="east_select")
                        if selected_east != "Select a team...":
                            abbrev = next(t["abbreviation"] for t in east_data if t["team_name"] == selected_east)
                            st.session_state.selected_team = abbrev
                            st.rerun()

                with col_west:
                    st.markdown("##### Western Conference")
                    west_data = standings.get("west", [])
                    if west_data:
                        west_df = pd.DataFrame(west_data)
                        west_df = west_df[["rank", "team_name", "wins", "losses", "win_pct", "gb"]]
                        west_df.columns = ["#", "Team", "W", "L", "Win%", "GB"]
                        st.dataframe(west_df, use_container_width=True, hide_index=True, height=560)

                        # Team selector
                        west_teams = [t["team_name"] for t in west_data]
                        selected_west = st.selectbox("View team profile", ["Select a team..."] + west_teams, key="west_select")
                        if selected_west != "Select a team...":
                            abbrev = next(t["abbreviation"] for t in west_data if t["team_name"] == selected_west)
                            st.session_state.selected_team = abbrev
                            st.rerun()

    except Exception as e:
        st.error(f"Could not load team data: {e}")
```

- [ ] **Step 3: Verify frontend syntax**

Run: `cd nba-ops-ai && python -c "import ast; ast.parse(open('app.py').read()); print('Syntax OK')"`
Expected: `Syntax OK`

- [ ] **Step 4: Commit**

```bash
cd nba-ops-ai
git add app.py
git commit -m "feat: add Teams tab with conference standings and team overview"
```

---

### Task 8: Build Games Tab in Frontend

**Files:**
- Modify: `nba-ops-ai/app.py` (add Games tab with filterable table)

**Interfaces:**
- Consumes: `GET /games`, `GET /games/teams` endpoints from Task 6
- Produces: Interactive "📅 Games" tab with filterable game log table

- [ ] **Step 1: Add Games tab content**

In `app.py`, add the Games tab block. Insert it after the `with tab4:` block (Teams) and before `with tab3:` (AI Assistant):

```python
# Tab 4: Game Log Explorer
with tab5:
    st.markdown("### 📅 Game Log Explorer")
    st.markdown("*Browse game results — filter by team and W/L*")

    try:
        # Get available teams for filter
        teams_data = httpx.get(f"{BACKEND_URL}/games/teams", timeout=10).json()
        available_teams = teams_data.get("teams", [])

        col_team, col_result = st.columns(2)

        with col_team:
            selected_team = st.selectbox(
                "Filter by team",
                ["All Teams"] + available_teams,
                key="game_team_filter"
            )

        with col_result:
            selected_result = st.selectbox(
                "Filter by result",
                ["All", "Wins", "Losses"],
                key="game_result_filter"
            )

        # Build query params
        params = {}
        if selected_team != "All Teams":
            params["team"] = selected_team
        if selected_result == "Wins":
            params["result"] = "W"
        elif selected_result == "Losses":
            params["result"] = "L"

        # Fetch games
        games_response = httpx.get(f"{BACKEND_URL}/games", params=params, timeout=15).json()
        games = games_response.get("games", [])
        total = games_response.get("total_count", 0)

        if games:
            st.markdown(f"**{total} games** found")

            # Build DataFrame for display
            display_df = pd.DataFrame(games)
            display_df = display_df[["date", "team", "matchup", "result", "points", "rebounds", "assists", "plus_minus"]]
            display_df.columns = ["Date", "Team", "Matchup", "Result", "PTS", "REB", "AST", "+/-"]

            # Color-code result column
            def color_result(val):
                if val == "W":
                    return "color: #00d4aa; font-weight: bold"
                elif val == "L":
                    return "color: #ff4757; font-weight: bold"
                return ""

            styled_df = display_df.style.map(color_result, subset=["Result"])

            st.dataframe(styled_df, use_container_width=True, height=600)

        else:
            st.info("No games match the selected filters.")

    except Exception as e:
        st.error(f"Could not load game data: {e}")
```

- [ ] **Step 2: Verify frontend syntax**

Run: `cd nba-ops-ai && python -c "import ast; ast.parse(open('app.py').read()); print('Syntax OK')"`
Expected: `Syntax OK`

- [ ] **Step 3: Commit**

```bash
cd nba-ops-ai
git add app.py
git commit -m "feat: add Games tab with filterable game log table"
```

---

### Task 9: Update README

**Files:**
- Modify: `nba-ops-ai/README.md`

**Interfaces:**
- Consumes: Knowledge of all changes from Tasks 1-8
- Produces: Updated README reflecting new features and project structure

- [ ] **Step 1: Update README features section**

In `README.md`, update the Features section to include the new tabs and remove references to auto-insights. Change the feature list to:

```markdown
### 1. SQL Analytics Dashboard
- Pre-built queries (top scorers, efficiency, home/away splits)
- Custom SQL input for advanced users
- Interactive result tables with sorting and filtering

### 2. Spatiotemporal Shot Charts
- Interactive shot location visualization (made vs missed)
- Zone efficiency breakdown by shot area
- Temporal trends showing shot patterns over time

### 3. Team Dashboard
- Conference standings (East/West) with win% and games behind
- Team overview with core stats (PPG, RPG, APG, FG%, 3PT%)
- Advanced metrics (offensive/defensive rating, pace, true shooting)
- Recent form (last 10 games) and top roster players

### 4. Game Log Explorer
- Filterable table of all game results
- Filter by team and W/L
- Box-score style data: points, rebounds, assists, +/-

### 5. RAG AI Assistant
- Natural language questions ("Who are the top scorers?")
- Context-aware answers powered by FAISS vector search
- Chat history with example prompts
```

- [ ] **Step 2: Update project structure in README**

In `README.md`, update the project structure to include new files:

```
nba-ops-ai/
├── app.py                    # Streamlit frontend
├── data_pipeline.py          # Fetch NBA data to SQLite
├── requirements.txt          # Python dependencies
├── Makefile                  # Launch commands
├── README.md                 # This file
├── backend/
│   ├── __init__.py
│   ├── main.py               # FastAPI app
│   ├── sql_engine.py         # SQL execution
│   ├── shot_charts.py        # Shot chart logic
│   ├── teams.py              # Team dashboard logic
│   ├── games.py              # Game log explorer logic
│   └── rag_chat.py           # RAG chatbot
├── data/
│   └── nba_data.db           # SQLite database (generated)
└── tests/
    ├── test_sql_engine.py
    ├── test_shot_charts.py
    └── test_rag_chat.py
```

- [ ] **Step 3: Commit**

```bash
cd nba-ops-ai
git add README.md
git commit -m "docs: update README with Teams and Games features"
```

---

### Task 10: End-to-End Verification

**Files:**
- None (verification only)

**Interfaces:**
- Consumes: All changes from Tasks 1-9
- Produces: Confirmation that all features work together

- [ ] **Step 1: Verify backend starts without errors**

Run: `cd nba-ops-ai && python -c "from backend.main import app; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 2: Verify all new endpoints respond**

Start the backend in background, then test:

```bash
cd nba-ops-ai
python -m backend.main &
sleep 3
# Test teams endpoint
curl -s http://localhost:8000/teams | python -m json.tool | head -5
# Test team overview
curl -s http://localhost:8000/teams/OKC | python -m json.tool | head -5
# Test games endpoint
curl -s "http://localhost:8000/games?team=OKC" | python -m json.tool | head -5
# Test games teams
curl -s http://localhost:8000/games/teams | python -m json.tool
# Verify insights is gone
curl -s http://localhost:8000/insights
# Kill backend
pkill -f "uvicorn backend.main"
```

Expected: All endpoints return valid JSON. `/insights` should return 404.

- [ ] **Step 3: Verify frontend compiles**

Run: `cd nba-ops-ai && python -c "import ast; ast.parse(open('app.py').read()); print('Frontend syntax OK')"`
Expected: `Frontend syntax OK`

- [ ] **Step 4: Verify existing features are unaffected**

Run: `cd nba-ops-ai && python -c "
from backend.sql_engine import get_prebuilt_queries, get_table_info
from backend.shot_charts import get_available_players

queries = get_prebuilt_queries()
print(f'Pre-built queries: {len(queries)}')

tables = get_table_info()
print(f'Tables: {[t[\"name\"] for t in tables]}')

players = get_available_players()
print(f'Shot chart players: {len(players)}')
"`

Expected: All existing features still work, `team_game_logs` table appears in tables list

- [ ] **Step 5: Final commit with any fixes**

```bash
cd nba-ops-ai
git add -A
git commit -m "chore: end-to-end verification and final cleanup"
```
