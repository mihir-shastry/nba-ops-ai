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
            game_id,
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
        GROUP BY game_id, team_abbreviation
        ORDER BY game_date DESC
    """

    result_data = execute_query(query)

    if result_data["error"]:
        return {"games": [], "columns": [], "total_count": 0, "error": result_data["error"]}

    games = []
    for row in result_data["rows"]:
        # Clean up matchup for display
        matchup = row[3]
        if "vs." in matchup:
            opponent = matchup.split("vs.")[-1].strip()
            display_matchup = f"vs {opponent}"
        elif "@" in matchup:
            opponent = matchup.split("@")[-1].strip()
            display_matchup = f"@ {opponent}"
        else:
            display_matchup = matchup

        games.append({
            "game_id": row[0],
            "team": row[1],
            "date": row[2],
            "matchup": display_matchup,
            "result": row[4],
            "points": row[5],
            "rebounds": row[6],
            "assists": row[7],
            "steals": row[8],
            "blocks": row[9],
            "turnovers": row[10],
            "fg_pct": row[11],
            "three_pct": row[12],
            "plus_minus": row[13]
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
