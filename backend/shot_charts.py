"""
Shot Chart Data Retrieval
Handles spatiotemporal shot data from the NBA database.
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nba_data.db")


def get_db():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


def get_available_players() -> list:
    """Get sorted list of players with shot chart data."""
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT DISTINCT player_name FROM shot_chart ORDER BY player_name"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def get_shot_data(player_name: str) -> dict:
    """
    Get all shot data and summary stats for a player.

    Returns dict with:
        - shots: list of shot dicts (x, y, made/missed, zone, date)
        - summary: total attempts, makes, FG%, avg distance, zone breakdown
    """
    conn = get_db()
    try:
        query = """
            SELECT x_coord, y_coord, shot_made, shot_distance,
                   shot_zone_basic, shot_zone_area, game_date
            FROM shot_chart
            WHERE player_name = ?
        """
        df = pd.read_sql_query(query, conn, params=(player_name,))

        if df.empty:
            return {"shots": [], "summary": {}}

        shots = df.to_dict("records")
        total = len(df)
        made = df["shot_made"].sum()

        summary = {
            "total_attempts": total,
            "makes": int(made),
            "fg_pct": round(made / total * 100, 1) if total > 0 else 0,
            "avg_distance": round(df["shot_distance"].mean(), 1),
            "zones": df["shot_zone_basic"].value_counts().to_dict(),
        }

        return {"shots": shots, "summary": summary}
    finally:
        conn.close()


def get_zone_stats(player_name: str) -> list:
    """
    Get shot zone efficiency breakdown for a player.

    Groups shots by zone and calculates FG% for each.
    """
    conn = get_db()
    try:
        query = """
            SELECT
                shot_zone_basic,
                COUNT(*) as attempts,
                SUM(shot_made) as makes,
                ROUND(SUM(shot_made) * 100.0 / COUNT(*), 1) as fg_pct,
                ROUND(AVG(shot_distance), 1) as avg_distance
            FROM shot_chart
            WHERE player_name = ?
            GROUP BY shot_zone_basic
            ORDER BY attempts DESC
        """
        df = pd.read_sql_query(query, conn, params=(player_name,))
        return df.to_dict("records")
    finally:
        conn.close()
