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
from nba_api.stats.endpoints import (
    leagueleaders,
    leaguedashteamstats,
    playergamelogs,
    shotchartdetail
)
from nba_api.stats.static import teams

# Configuration
REQUEST_TIMEOUT = 60
DELAY_BETWEEN_CALLS = 1.0
MAX_RETRIES = 2
BACKOFF_BASE = 2.0

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "nba_data.db")


# Retry decorator with exponential backoff
def retry_with_backoff(max_retries=MAX_RETRIES, backoff_base=BACKOFF_BASE):
    """Decorator that retries a function on exception with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
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
    return sqlite3.connect(DB_PATH)


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
            x_coord REAL,
            y_coord REAL,
            shot_distance REAL,
            shot_zone_basic TEXT,
            shot_zone_area TEXT,
            FOREIGN KEY (player_id) REFERENCES league_leaders(player_id)
        );

        CREATE INDEX IF NOT EXISTS idx_game_logs_player ON player_game_logs(player_id);
        CREATE INDEX IF NOT EXISTS idx_shots_player ON shot_chart(player_id);
    """)
    conn.commit()


# API fetch functions with retry
@retry_with_backoff()
def _api_league_leaders():
    """Raw API call for league leaders."""
    return leagueleaders.LeagueLeaders(
        stat_category_abbreviation="PTS",
        per_mode48="PerGame",
        season="2024-25",
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
        season="2024-25",
        per_mode_detailed="PerGame",
        timeout=REQUEST_TIMEOUT
    )


def fetch_team_stats(conn):
    """Fetch team statistics."""
    print("Fetching team stats...")
    stats = _api_team_stats()
    df = stats.get_data_frames()[0]
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

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


@retry_with_backoff()
def _api_game_logs(player_id):
    """Raw API call for a single player's game logs."""
    return playergamelogs.PlayerGameLogs(
        player_id_nullable=player_id,
        season_nullable="2024-25",
        timeout=REQUEST_TIMEOUT
    )


def fetch_game_logs(conn, player_ids):
    """Fetch game logs for specified players."""
    print("Fetching game logs...")
    all_logs = []

    for i, pid in enumerate(player_ids):
        print(f"  Fetching logs for player {pid}...")
        try:
            logs = _api_game_logs(pid)
            df = logs.get_data_frames()[0]
            if not df.empty:
                df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                all_logs.append(df)
        except Exception as e:
            print(f"    Skipping player {pid}: {e}")

        if i < len(player_ids) - 1:
            time.sleep(DELAY_BETWEEN_CALLS)

    if all_logs:
        combined = pd.concat(all_logs, ignore_index=True)
        combined.to_sql("player_game_logs", conn, if_exists="replace", index=False)
        print(f"  Inserted {len(combined)} game logs")


@retry_with_backoff()
def _api_shot_charts(player_id, team_id):
    """Raw API call for a single player's shot chart."""
    return shotchartdetail.ShotChartDetail(
        player_id=player_id,
        team_id=team_id,
        season_nullable="2024-25",
        context_measure_simple="FGA",
        timeout=REQUEST_TIMEOUT
    )


def fetch_shot_charts(conn, player_ids):
    """Fetch shot chart data for specified players."""
    print("Fetching shot charts...")
    nba_teams = {t["abbreviation"]: t["id"] for t in teams.get_teams()}
    all_shots = []

    for i, pid in enumerate(player_ids):
        print(f"  Fetching shots for player {pid}...")
        try:
            cursor = conn.execute(
                "SELECT team_abbreviation FROM league_leaders WHERE player_id = ?",
                (pid,)
            )
            row = cursor.fetchone()
            if not row:
                continue
            team_abbrev = row[0]
            team_id = nba_teams.get(team_abbrev, 0)

            shots = _api_shot_charts(pid, team_id)
            df = shots.get_data_frames()[0]
            if not df.empty:
                df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                all_shots.append(df)
        except Exception as e:
            print(f"    Skipping player {pid}: {e}")

        if i < len(player_ids) - 1:
            time.sleep(DELAY_BETWEEN_CALLS)

    if all_shots:
        combined = pd.concat(all_shots, ignore_index=True)
        combined.to_sql("shot_chart", conn, if_exists="replace", index=False)
        print(f"  Inserted {len(combined)} shots")


# Cache check
REQUIRED_TABLES = ["league_leaders", "team_stats", "player_game_logs", "shot_chart"]

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

    if is_database_populated():
        print("  Database already populated — skipping fetch. Delete data/nba_data.db to re-fetch.")
        return

    print(f"  Delay between calls: {DELAY_BETWEEN_CALLS}s")
    print(f"  Max retries: {MAX_RETRIES}\n")

    conn = get_db()
    init_database(conn)

    leaders_df = fetch_league_leaders(conn)
    time.sleep(DELAY_BETWEEN_CALLS)

    fetch_team_stats(conn)
    time.sleep(DELAY_BETWEEN_CALLS)

    top_player_ids = leaders_df.head(20)["player_id"].tolist()
    fetch_game_logs(conn, top_player_ids)
    time.sleep(DELAY_BETWEEN_CALLS)

    fetch_shot_charts(conn, top_player_ids[:15])

    conn.close()
    print(f"\nPipeline complete! Database: {DB_PATH}")


if __name__ == "__main__":
    run_pipeline()
