"""
Lineup Optimizer Backend
Provides 5-man unit stats, league-wide best lineups, and team comparison.
Zero Gemini calls — pure SQL + Python.
"""

from .sql_engine import execute_query


def get_team_lineups(team_abbreviation: str, min_minutes: float = 50) -> dict:
    """
    Get lineup stats for a team, filtered by minimum minutes.
    
    Returns dict with:
        - team: team info
        - lineups: list of lineup dicts sorted by net_rating
        - total_lineups: number of qualifying lineups
    """
    result = execute_query(f"""
        SELECT
            lineup, games, wins, losses, win_pct,
            minutes, points, rebounds, assists, steals, blocks,
            turnovers, fg_pct, three_pct, plus_minus
        FROM lineup_stats
        WHERE team_abbreviation = '{team_abbreviation.upper()}'
        AND minutes >= {min_minutes}
        ORDER BY plus_minus DESC
    """)

    if result["error"]:
        return {"team": team_abbreviation, "lineups": [], "total_lineups": 0, "error": result["error"]}

    lineups = []
    for row in result["rows"]:
        lineups.append({
            "lineup": row[0],
            "games": row[1],
            "wins": row[2],
            "losses": row[3],
            "win_pct": row[4],
            "minutes": round(row[5], 1),
            "points": row[6],
            "rebounds": row[7],
            "assists": row[8],
            "steals": row[9],
            "blocks": row[10],
            "turnovers": row[11],
            "fg_pct": round(row[12] * 100, 1) if row[12] and row[12] < 1 else row[12],
            "three_pct": round(row[13] * 100, 1) if row[13] and row[13] < 1 else row[13],
            "plus_minus": row[14]
        })

    return {
        "team": team_abbreviation.upper(),
        "lineups": lineups,
        "total_lineups": len(lineups)
    }


def get_league_best_lineups(min_minutes: float = 100, limit: int = 20) -> dict:
    """
    Get the best lineups in the league by plus_minus.
    
    Returns dict with:
        - lineups: list of lineup dicts with team context
        - total_count: number returned
    """
    result = execute_query(f"""
        SELECT
            team_abbreviation, lineup, games, wins, losses, win_pct,
            minutes, points, rebounds, assists, plus_minus
        FROM lineup_stats
        WHERE minutes >= {min_minutes}
        ORDER BY plus_minus DESC
        LIMIT {limit}
    """)

    if result["error"]:
        return {"lineups": [], "total_count": 0, "error": result["error"]}

    lineups = []
    for row in result["rows"]:
        lineups.append({
            "team": row[0],
            "lineup": row[1],
            "games": row[2],
            "wins": row[3],
            "losses": row[4],
            "win_pct": row[5],
            "minutes": round(row[6], 1),
            "points": row[7],
            "rebounds": row[8],
            "assists": row[9],
            "plus_minus": row[10]
        })

    return {
        "lineups": lineups,
        "total_count": len(lineups)
    }
