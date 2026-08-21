"""
Player Comparison Tool
Compare two players head-to-head with radar charts and stat tables.
Zero Gemini calls — pure SQL + Python.
"""

from .sql_engine import execute_query
from .ratings import _compute_rating, _get_league_stats


def get_player_stats(player_name: str) -> dict:
    """
    Get all stats for a player for comparison.
    
    Returns dict with:
        - player: player info (name, team, position)
        - season_stats: all season averages
        - rating: overall rating from ratings.py
        - radar_values: normalized values for radar chart (0-100 scale per category)
    """
    result = execute_query(f"""
        SELECT
            player_name, team_abbreviation,
            points_per_game, rebounds_per_game, assists_per_game,
            steals_per_game, blocks_per_game, turnovers_per_game,
            field_goal_pct, three_point_pct, free_throw_pct,
            games_played, minutes_per_game
        FROM league_leaders
        WHERE player_name = '{player_name}'
    """)

    if result["error"] or not result["rows"]:
        return {"error": f"Player '{player_name}' not found"}

    row = result["rows"][0]

    stats = {
        "pts": row[2], "reb": row[3], "ast": row[4],
        "stl": row[5], "blk": row[6], "tov": row[7],
        "fg_pct": row[8], "three_pct": row[9], "ft_pct": row[10],
        "min": row[12]
    }
    gp = row[11]
    league_stats = _get_league_stats()
    rating = _compute_rating(stats, league_stats)

    # Component scores for radar chart (0-100 each)
    max_pts, max_reb, max_ast, max_stl, max_blk = 35, 14, 12, 2.5, 3.0

    radar_values = {
        "Scoring": min(100, round((row[2] / max_pts) * 100, 1)),
        "Rebounding": min(100, round((row[3] / max_reb) * 100, 1)),
        "Playmaking": min(100, round((row[4] / max_ast) * 100, 1)),
        "Defense": min(100, round(((row[5] / max_stl) + (row[6] / max_blk)) * 50, 1)),
        "Efficiency": min(100, round((row[8] or 0) * 100 + (row[9] or 0) * 50, 1))
    }

    return {
        "player": {
            "player_name": row[0],
            "team_abbreviation": row[1],
            "points_per_game": row[2],
            "rebounds_per_game": row[3],
            "assists_per_game": row[4],
            "steals_per_game": row[5],
            "blocks_per_game": row[6],
            "turnovers_per_game": row[7],
            "field_goal_pct": round(row[8] * 100, 1) if row[8] and row[8] < 1 else row[8],
            "three_point_pct": round(row[9] * 100, 1) if row[9] and row[9] < 1 else row[9],
            "free_throw_pct": round(row[10] * 100, 1) if row[10] and row[10] < 1 else row[10],
            "games_played": gp,
            "minutes_per_game": row[12]
        },
        "rating": rating,
        "radar_values": radar_values
    }


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
    p1 = get_player_stats(player1)
    p2 = get_player_stats(player2)

    if "error" in p1:
        return {"error": p1["error"]}
    if "error" in p2:
        return {"error": p2["error"]}

    # Stat comparison table
    stat_keys = [
        ("points_per_game", "PPG"),
        ("rebounds_per_game", "RPG"),
        ("assists_per_game", "APG"),
        ("steals_per_game", "SPG"),
        ("blocks_per_game", "BPG"),
        ("turnovers_per_game", "TOPG"),
        ("field_goal_pct", "FG%"),
        ("three_point_pct", "3PT%"),
        ("free_throw_pct", "FT%"),
        ("games_played", "GP"),
        ("minutes_per_game", "MPG")
    ]

    stat_table = []
    for key, label in stat_keys:
        v1 = p1["player"][key]
        v2 = p2["player"][key]
        winner = "player1" if v1 > v2 else ("player2" if v2 > v1 else "tie")
        # For turnovers, lower is better
        if key == "turnovers_per_game":
            winner = "player1" if v1 < v2 else ("player2" if v2 < v1 else "tie")
        stat_table.append({
            "stat": label,
            "player1_value": v1,
            "player2_value": v2,
            "winner": winner
        })

    # Verdicts per category
    categories = ["Scoring", "Rebounding", "Playmaking", "Defense", "Efficiency"]
    verdicts = []
    for cat in categories:
        v1 = p1["radar_values"][cat]
        v2 = p2["radar_values"][cat]
        diff = abs(v1 - v2)
        if diff < 5:
            verdicts.append({"category": cat, "winner": "Even", "margin": "close"})
        elif v1 > v2:
            verdicts.append({"category": cat, "winner": p1["player"]["player_name"], "margin": f"+{diff:.0f}"})
        else:
            verdicts.append({"category": cat, "winner": p2["player"]["player_name"], "margin": f"+{diff:.0f}"})

    return {
        "player1": p1,
        "player2": p2,
        "stat_table": stat_table,
        "verdicts": verdicts
    }
