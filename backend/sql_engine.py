"""
SQL Query Execution Engine
Handles SQL queries against the SQLite database.
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nba_data.db")

# Pre-built queries for the SQL Analytics tab
PREBUILT_QUERIES = {
    "top_scorers": {
        "name": "Top 10 Scorers",
        "description": "Players ranked by points per game",
        "sql": """
            SELECT
                player_name,
                team_abbreviation,
                points_per_game,
                games_played,
                field_goal_pct,
                three_point_pct
            FROM league_leaders
            ORDER BY points_per_game DESC
            LIMIT 10
        """
    },
    "efficient_scorers": {
        "name": "Most Efficient Scorers",
        "description": "High-volume scorers with best FG%",
        "sql": """
            SELECT
                player_name,
                team_abbreviation,
                points_per_game,
                field_goal_pct,
                ROUND(points_per_game * field_goal_pct, 2) as efficiency_score
            FROM league_leaders
            WHERE games_played >= 40
            ORDER BY efficiency_score DESC
            LIMIT 10
        """
    },
    "home_vs_away": {
        "name": "Home vs Away Performance",
        "description": "Compare player stats at home vs away",
        "sql": """
            SELECT
                player_name,
                CASE
                    WHEN matchup LIKE '%vs%' THEN 'Home'
                    ELSE 'Away'
                END as location,
                COUNT(*) as games,
                ROUND(AVG(points), 1) as avg_points,
                ROUND(AVG(assists), 1) as avg_assists,
                ROUND(AVG(rebounds), 1) as avg_rebounds
            FROM player_game_logs
            GROUP BY player_name, location
            HAVING COUNT(*) >= 10
            ORDER BY player_name, location
        """
    },
    "team_standings": {
        "name": "Team Standings",
        "description": "All teams ranked by win percentage",
        "sql": """
            SELECT
                team_name,
                wins,
                losses,
                ROUND(wins * 100.0 / (wins + losses), 1) as win_pct,
                points_per_game,
                field_goal_pct
            FROM team_stats
            ORDER BY win_pct DESC
        """
    },
    "triple_double_watch": {
        "name": "Triple-Double Watch",
        "description": "Players closest to averaging a triple-double",
        "sql": """
            SELECT
                player_name,
                team_abbreviation,
                points_per_game,
                rebounds_per_game,
                assists_per_game,
                (CASE WHEN points_per_game >= 10 THEN 1 ELSE 0 END +
                 CASE WHEN rebounds_per_game >= 10 THEN 1 ELSE 0 END +
                 CASE WHEN assists_per_game >= 10 THEN 1 ELSE 0 END) as categories_above_10
            FROM league_leaders
            ORDER BY categories_above_10 DESC, points_per_game DESC
            LIMIT 10
        """
    }
}


def get_db():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


def execute_query(query: str) -> dict:
    """
    Execute a SQL query and return results.

    Returns dict with:
        - columns: list of column names
        - rows: list of row lists
        - row_count: number of rows
        - error: error message if query failed, else None
    """
    conn = get_db()
    try:
        df = pd.read_sql_query(query, conn)
        return {
            "columns": df.columns.tolist(),
            "rows": df.values.tolist(),
            "row_count": len(df),
            "error": None
        }
    except Exception as e:
        return {
            "error": str(e),
            "columns": [],
            "rows": [],
            "row_count": 0
        }
    finally:
        conn.close()


def get_prebuilt_queries() -> dict:
    """Get all pre-built queries."""
    return PREBUILT_QUERIES


def get_table_info() -> list:
    """Get metadata for all tables in the database."""
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        table_info = []
        for table in tables:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            table_info.append({
                "name": table,
                "columns": columns,
                "row_count": count
            })

        return table_info
    finally:
        conn.close()
