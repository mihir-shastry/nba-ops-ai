"""
NBA Data Pipeline
Fetches player stats, game logs, and shot data from the NBA API
and stores them in SQLite.
"""

import sqlite3
import pandas as pd
import os
import time
import functools
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Patch nba_api to use curl_cffi (bypasses Akamai TLS fingerprinting)
import nba_api_compat  # noqa: F401

from nba_api.stats.endpoints import (
    leagueleaders,
    leaguedashteamstats,
    leaguegamefinder,
    shotchartdetail
)
from nba_api.stats.static import teams

# Configuration
REQUEST_TIMEOUT = 60
DELAY_BETWEEN_CALLS = 0.7
MAX_RETRIES = 2
BACKOFF_BASE = 2.0
MAX_WORKERS = 5
PLAYER_LIMIT = 50

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "nba_data.db")

# Thread-safe rate limiting
_rate_lock = threading.Lock()
_last_request_time = [0.0]


def _rate_limit():
    """Global rate limiter — ensures minimum delay between API calls across all threads."""
    with _rate_lock:
        elapsed = time.time() - _last_request_time[0]
        if elapsed < DELAY_BETWEEN_CALLS:
            time.sleep(DELAY_BETWEEN_CALLS - elapsed)
        _last_request_time[0] = time.time()


# Retry decorator with exponential backoff
def retry_with_backoff(max_retries=MAX_RETRIES, backoff_base=BACKOFF_BASE):
    """Retries a function on exception with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    _rate_limit()
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait = backoff_base * (2 ** attempt)
                    print(f"    Attempt {attempt + 1}/{max_retries} failed: {e}")
                    print(f"    Retrying in {wait:.0f}s...")
                    time.sleep(wait)
            raise last_exception
        return wrapper
    return decorator


# Database helpers
def get_db():
    """Get SQLite database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_database(conn):
    """Initialize database schema."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS league_leaders (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT,
            team_abbreviation TEXT,
            points_per_game REAL,
            rebounds_per_game REAL,
            assists_per_game REAL,
            steals_per_game REAL,
            blocks_per_game REAL,
            turnovers_per_game REAL,
            field_goal_pct REAL,
            three_point_pct REAL,
            free_throw_pct REAL,
            games_played INTEGER,
            minutes_per_game REAL
        );

        CREATE TABLE IF NOT EXISTS team_stats (
            team_id INTEGER PRIMARY KEY,
            team_name TEXT,
            abbreviation TEXT,
            wins INTEGER,
            losses INTEGER,
            points_per_game REAL,
            rebounds_per_game REAL,
            assists_per_game REAL,
            field_goal_pct REAL,
            three_point_pct REAL
        );

        CREATE TABLE IF NOT EXISTS player_game_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            player_name TEXT,
            team_abbreviation TEXT,
            game_date TEXT,
            matchup TEXT,
            win TEXT,
            points INTEGER,
            rebounds INTEGER,
            assists INTEGER,
            steals INTEGER,
            blocks INTEGER,
            turnovers INTEGER,
            minutes REAL,
            field_goal_pct REAL,
            three_point_pct REAL,
            plus_minus REAL,
            FOREIGN KEY (player_id) REFERENCES league_leaders(player_id)
        );

        CREATE TABLE IF NOT EXISTS shot_chart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            player_name TEXT,
            team_id INTEGER,
            game_date TEXT,
            period INTEGER,
            minutes_remaining INTEGER,
            seconds_remaining INTEGER,
            event_type TEXT,
            shot_made INTEGER,
            loc_x REAL,
            loc_y REAL,
            shot_distance REAL,
            shot_zone_basic TEXT,
            shot_zone_area TEXT,
            FOREIGN KEY (player_id) REFERENCES league_leaders(player_id)
        );

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

        CREATE INDEX IF NOT EXISTS idx_game_logs_player ON player_game_logs(player_id);
        CREATE INDEX IF NOT EXISTS idx_shots_player ON shot_chart(player_id);
        CREATE INDEX IF NOT EXISTS idx_team_game_logs_team ON team_game_logs(team_abbreviation);
        CREATE INDEX IF NOT EXISTS idx_team_game_logs_date ON team_game_logs(game_date);
    """)
    conn.commit()


# API fetch functions with retry
@retry_with_backoff()
def _api_league_leaders():
    """Raw API call for league leaders."""
    return leagueleaders.LeagueLeaders(
        stat_category_abbreviation="PTS",
        per_mode48="PerGame",
        season="2025-26",
        timeout=REQUEST_TIMEOUT
    )


def fetch_league_leaders(conn):
    """Fetch top players by PPG."""
    print("Fetching league leaders...")
    leaders = _api_league_leaders()
    df = leaders.get_data_frames()[0]
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    cols = [
        "player_id", "player", "team",
        "pts", "reb", "ast", "stl", "blk", "tov",
        "fg_pct", "fg3_pct", "ft_pct", "gp", "min"
    ]
    rename_map = {
        "player": "player_name",
        "team": "team_abbreviation",
        "pts": "points_per_game",
        "reb": "rebounds_per_game",
        "ast": "assists_per_game",
        "stl": "steals_per_game",
        "blk": "blocks_per_game",
        "tov": "turnovers_per_game",
        "fg_pct": "field_goal_pct",
        "fg3_pct": "three_point_pct",
        "ft_pct": "free_throw_pct",
        "gp": "games_played",
        "min": "minutes_per_game"
    }

    df = df[cols].rename(columns=rename_map)
    df.to_sql("league_leaders", conn, if_exists="replace", index=False)
    print(f"  Inserted {len(df)} players")
    return df


@retry_with_backoff()
def _api_team_stats():
    """Raw API call for team stats."""
    return leaguedashteamstats.LeagueDashTeamStats(
        season="2025-26",
        per_mode_detailed="PerGame",
        timeout=REQUEST_TIMEOUT
    )


def fetch_team_stats(conn):
    """Fetch team statistics."""
    print("Fetching team stats...")
    stats = _api_team_stats()
    df = stats.get_data_frames()[0]
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # Build name-to-abbreviation mapping from nba_api static teams
    name_to_abbr = {t["full_name"]: t["abbreviation"] for t in teams.get_teams()}
    # Fallback for known API name mismatches
    name_to_abbr["LA Clippers"] = "LAC"
    name_to_abbr["LA Lakers"] = "LAL"
    df["abbreviation"] = df["team_name"].map(name_to_abbr)

    available = df.columns.tolist()
    col_map = {}
    for orig, target in [
        ("team_id", "team_id"), ("team_name", "team_name"), ("abbreviation", "abbreviation"),
        ("w", "wins"), ("l", "losses"), ("pts", "points_per_game"),
        ("reb", "rebounds_per_game"), ("ast", "assists_per_game"),
        ("fg_pct", "field_goal_pct"), ("fg3_pct", "three_point_pct")
    ]:
        if orig in available:
            col_map[orig] = target
    cols = list(col_map.keys())

    df = df[cols].rename(columns=col_map)
    df.to_sql("team_stats", conn, if_exists="replace", index=False)
    print(f"  Inserted {len(df)} teams")


# --- Batch game logs via LeagueGameFinder ---

@retry_with_backoff()
def _api_all_game_logs():
    """Raw API call — fetches ALL player game logs for the season in one request."""
    return leaguegamefinder.LeagueGameFinder(
        player_or_team_abbreviation="P",
        season_nullable="2025-26",
        timeout=REQUEST_TIMEOUT
    )


def fetch_game_logs(conn, player_ids):
    """Fetch game logs for all players in a single batch request, then filter to top N."""
    print("Fetching game logs (single batch request)...")

    finder = _api_all_game_logs()
    df = finder.get_data_frames()[0]
    print(f"  Fetched {len(df)} total game logs")

    # Filter to players in our league_leaders table
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # Map NBA API column names to our schema
    rename_map = {
        "player_id": "player_id",
        "player_name": "player_name",
        "team_abbreviation": "team_abbreviation",
        "game_date": "game_date",
        "matchup": "matchup",
        "wl": "win",
        "pts": "points",
        "reb": "rebounds",
        "ast": "assists",
        "stl": "steals",
        "blk": "blocks",
        "tov": "turnovers",
        "min": "minutes",
        "fg_pct": "field_goal_pct",
        "fg3_pct": "three_point_pct",
        "plus_minus": "plus_minus"
    }

    # Only rename columns that exist
    available = df.columns.tolist()
    actual_rename = {k: v for k, v in rename_map.items() if k in available}
    df = df.rename(columns=actual_rename)

    # Filter to top N players
    df = df[df["player_id"].isin(player_ids)]

    # Select only columns that exist in our schema
    target_cols = [
        "player_id", "player_name", "team_abbreviation", "game_date",
        "matchup", "win", "points", "rebounds", "assists", "steals",
        "blocks", "turnovers", "minutes", "field_goal_pct",
        "three_point_pct", "plus_minus"
    ]
    available_target = [c for c in target_cols if c in df.columns]
    df = df[available_target]

    df.to_sql("player_game_logs", conn, if_exists="replace", index=False)
    print(f"  Inserted {len(df)} game logs for top {len(player_ids)} players")


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


# --- Threaded shot chart fetch ---

@retry_with_backoff()
def _api_shot_charts(player_id, team_id):
    """Raw API call for a single player's shot chart."""
    return shotchartdetail.ShotChartDetail(
        player_id=player_id,
        team_id=team_id,
        season_nullable="2025-26",
        context_measure_simple="FGA",
        timeout=REQUEST_TIMEOUT
    )


def _fetch_single_shot_chart(player_id, team_id):
    """Fetch and return a single player's shot chart as a DataFrame."""
    try:
        shots = _api_shot_charts(player_id, team_id)
        df = shots.get_data_frames()[0]
        if not df.empty:
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            return df
        return None
    except Exception as e:
        print(f"    Skipping shot chart for player {player_id}: {e}")
        return None


def fetch_shot_charts(conn, player_ids):
    """Fetch shot chart data for specified players using thread pool."""
    print(f"Fetching shot charts ({len(player_ids)} players, {MAX_WORKERS} threads)...")

    nba_teams = {t["abbreviation"]: t["id"] for t in teams.get_teams()}

    # Build player_id -> team_id mapping from league_leaders table
    team_map = {}
    cursor = conn.execute("SELECT player_id, team_abbreviation FROM league_leaders")
    for row in cursor:
        team_map[row[0]] = nba_teams.get(row[1], 0)

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_fetch_single_shot_chart, pid, team_map.get(pid, 0)): pid
            for pid in player_ids
        }
        for i, future in enumerate(as_completed(futures), 1):
            pid = futures[future]
            df = future.result()
            if df is not None:
                results.append(df)
                print(f"  [{i}/{len(player_ids)}] Fetched shots for player {pid}")
            else:
                print(f"  [{i}/{len(player_ids)}] Skipped player {pid}")

    if results:
        combined = pd.concat(results, ignore_index=True)
        combined.to_sql("shot_chart", conn, if_exists="replace", index=False)
        print(f"  Inserted {len(combined)} shots")


# Cache check
REQUIRED_TABLES = ["league_leaders", "team_stats", "player_game_logs", "shot_chart", "team_game_logs"]

def is_database_populated():
    """Check if the database already has data in all required tables."""
    if not os.path.exists(DB_PATH):
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        for table in REQUIRED_TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count == 0:
                conn.close()
                return False
        conn.close()
        return True
    except Exception:
        return False


# Main pipeline
def run_pipeline():
    """Main pipeline execution."""
    print("=== NBA Data Pipeline ===")
    print(f"  nba_api version: {__import__('nba_api').__version__}")
    print(f"  Threads: {MAX_WORKERS}")
    print(f"  Player limit: {PLAYER_LIMIT}")
    print(f"  Rate limit delay: {DELAY_BETWEEN_CALLS}s\n")

    if is_database_populated():
        print("  Database already populated — skipping fetch. Delete data/nba_data.db to re-fetch.")
        return

    conn = get_db()
    init_database(conn)

    leaders_df = fetch_league_leaders(conn)
    time.sleep(DELAY_BETWEEN_CALLS)

    fetch_team_stats(conn)
    time.sleep(DELAY_BETWEEN_CALLS)

    fetch_team_game_logs(conn)
    time.sleep(DELAY_BETWEEN_CALLS)

    top_player_ids = leaders_df.head(PLAYER_LIMIT)["player_id"].tolist()
    fetch_game_logs(conn, top_player_ids)

    fetch_shot_charts(conn, top_player_ids[:15])

    conn.close()
    print(f"\nPipeline complete! Database: {DB_PATH}")


if __name__ == "__main__":
    run_pipeline()
