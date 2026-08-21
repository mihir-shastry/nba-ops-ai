"""
Player Rating System
Z-score based player ratings (0-100 scale) computed from season averages.
Normalizes each stat to standard deviations from the mean, then combines
with weights. Avoids per36 inflation that makes bench players look elite.
Zero Gemini calls — pure SQL + Python.
"""

import math
from .sql_engine import execute_query


def _compute_rating(row, league_stats=None):
    """
    Compute a player rating using z-score normalization.
    
    Args:
        row: dict with pts, reb, ast, stl, blk, tov, min, fg_pct, three_pct, ft_pct, gp
        league_stats: dict with mean and std for each stat (precomputed)
    
    Returns:
        float: rating on 0-100 scale
    """
    pts = row.get("pts", 0) or 0
    reb = row.get("reb", 0) or 0
    ast = row.get("ast", 0) or 0
    stl = row.get("stl", 0) or 0
    blk = row.get("blk", 0) or 0
    tov = row.get("tov", 0) or 0
    gp = row.get("gp", 82) or 82
    
    # Z-score normalization for each stat
    if league_stats:
        z_pts = (pts - league_stats["pts_mean"]) / league_stats["pts_std"] if league_stats["pts_std"] > 0 else 0
        z_reb = (reb - league_stats["reb_mean"]) / league_stats["reb_std"] if league_stats["reb_std"] > 0 else 0
        z_ast = (ast - league_stats["ast_mean"]) / league_stats["ast_std"] if league_stats["ast_std"] > 0 else 0
        z_stl = (stl - league_stats["stl_mean"]) / league_stats["stl_std"] if league_stats["stl_std"] > 0 else 0
        z_blk = (blk - league_stats["blk_mean"]) / league_stats["blk_std"] if league_stats["blk_std"] > 0 else 0
        z_tov = (tov - league_stats["tov_mean"]) / league_stats["tov_std"] if league_stats["tov_std"] > 0 else 0
    else:
        # Fallback: use rough league averages
        z_pts = (pts - 12) / 6
        z_reb = (reb - 4.5) / 2.5
        z_ast = (ast - 3) / 2
        z_stl = (stl - 1) / 0.5
        z_blk = (blk - 0.5) / 0.5
        z_tov = (tov - 2) / 1
    
    # Weighted combination (scoring weighted highest, turnovers penalized)
    raw_z = (z_pts * 1.0 + z_reb * 0.8 + z_ast * 1.2 + z_stl * 1.5 + z_blk * 1.5 - z_tov * 0.8)
    
    # Scale to 0-100: raw_z typically ranges from -3 to +4
    # Map: -3 → 0, +3 → 100
    rating = 50 + (raw_z / 6) * 50
    rating = min(100, max(0, rating))
    
    return round(rating, 1)


def _get_league_stats():
    """Compute league-wide mean and std for each stat."""
    result = execute_query("""
        SELECT
            AVG(points_per_game) as pts_mean,
            -- Approximate std using max-min range / 4 (rough estimate)
            (MAX(points_per_game) - MIN(points_per_game)) / 4.0 as pts_std,
            AVG(rebounds_per_game) as reb_mean,
            (MAX(rebounds_per_game) - MIN(rebounds_per_game)) / 4.0 as reb_std,
            AVG(assists_per_game) as ast_mean,
            (MAX(assists_per_game) - MIN(assists_per_game)) / 4.0 as ast_std,
            AVG(steals_per_game) as stl_mean,
            (MAX(steals_per_game) - MIN(steals_per_game)) / 4.0 as stl_std,
            AVG(blocks_per_game) as blk_mean,
            (MAX(blocks_per_game) - MIN(blocks_per_game)) / 4.0 as blk_std,
            AVG(turnovers_per_game) as tov_mean,
            (MAX(turnovers_per_game) - MIN(turnovers_per_game)) / 4.0 as tov_std
        FROM league_leaders
        WHERE games_played >= 20
    """)

    if result["error"] or not result["rows"]:
        return None

    row = result["rows"][0]
    # Ensure no zero stds
    return {
        "pts_mean": row[0] or 12, "pts_std": max(row[1] or 6, 1),
        "reb_mean": row[2] or 4.5, "reb_std": max(row[3] or 2.5, 0.5),
        "ast_mean": row[4] or 3, "ast_std": max(row[5] or 2, 0.5),
        "stl_mean": row[6] or 1, "stl_std": max(row[7] or 0.5, 0.1),
        "blk_mean": row[8] or 0.5, "blk_std": max(row[9] or 0.5, 0.1),
        "tov_mean": row[10] or 2, "tov_std": max(row[11] or 1, 0.3),
    }


def get_player_ratings(sort_by="rating", limit=50) -> dict:
    """
    Get all player ratings using z-score normalization.
    
    Returns dict with:
        - players: list of player dicts with name, team, rating, stats
        - columns: list of column names
    """
    league_stats = _get_league_stats()

    result = execute_query("""
        SELECT
            player_name,
            team_abbreviation,
            points_per_game,
            rebounds_per_game,
            assists_per_game,
            steals_per_game,
            blocks_per_game,
            turnovers_per_game,
            field_goal_pct,
            three_point_pct,
            free_throw_pct,
            games_played,
            minutes_per_game
        FROM league_leaders
        WHERE games_played >= 20
        ORDER BY points_per_game DESC
    """)

    if result["error"]:
        return {"players": [], "columns": [], "error": result["error"]}

    players = []
    for row in result["rows"]:
        stats = {
            "pts": row[2], "reb": row[3], "ast": row[4],
            "stl": row[5], "blk": row[6], "tov": row[7],
            "fg_pct": row[8], "three_pct": row[9], "ft_pct": row[10],
            "min": row[12], "gp": row[11]
        }
        rating = _compute_rating(stats, league_stats)

        # Component scores for radar chart (z-scores normalized to 0-100)
        max_pts, max_reb, max_ast, max_stl, max_blk = 35, 14, 12, 2.5, 3.0

        players.append({
            "player_name": row[0],
            "team_abbreviation": row[1],
            "rating": rating,
            "points_per_game": row[2],
            "rebounds_per_game": row[3],
            "assists_per_game": row[4],
            "steals_per_game": row[5],
            "blocks_per_game": row[6],
            "turnovers_per_game": row[7],
            "field_goal_pct": round(row[8] * 100, 1) if row[8] and row[8] < 1 else row[8],
            "three_point_pct": round(row[9] * 100, 1) if row[9] and row[9] < 1 else row[9],
            "games_played": row[11],
            "minutes_per_game": row[12],
            "scoring": min(100, max(0, 50 + ((row[2] - (league_stats["pts_mean"] if league_stats else 12)) / (league_stats["pts_std"] if league_stats else 6)) * 25)),
            "rebounding": min(100, max(0, 50 + ((row[3] - (league_stats["reb_mean"] if league_stats else 4.5)) / (league_stats["reb_std"] if league_stats else 2.5)) * 25)),
            "playmaking": min(100, max(0, 50 + ((row[4] - (league_stats["ast_mean"] if league_stats else 3)) / (league_stats["ast_std"] if league_stats else 2)) * 25)),
            "defense": min(100, max(0, 50 + (((row[5] + row[6]) - ((league_stats["stl_mean"] if league_stats else 1) + (league_stats["blk_mean"] if league_stats else 0.5))) / ((league_stats["stl_std"] if league_stats else 0.5) + (league_stats["blk_std"] if league_stats else 0.5))) * 25)),
            "efficiency": min(100, max(0, 50 + ((row[8] or 0.45 - 0.45) / 0.08) * 50))
        })

    # Sort
    if sort_by == "rating":
        players.sort(key=lambda p: -p["rating"])
    elif sort_by == "pts":
        players.sort(key=lambda p: -p["points_per_game"])
    elif sort_by == "reb":
        players.sort(key=lambda p: -p["rebounds_per_game"])
    elif sort_by == "ast":
        players.sort(key=lambda p: -p["assists_per_game"])

    players = players[:limit]

    return {
        "players": players,
        "columns": ["player_name", "team_abbreviation", "rating", "points_per_game",
                     "rebounds_per_game", "assists_per_game", "steals_per_game",
                     "blocks_per_game", "field_goal_pct", "three_point_pct", "games_played"]
    }


def get_player_rating_detail(player_name: str) -> dict:
    """
    Get detailed rating breakdown for a single player.
    """
    league_stats = _get_league_stats()

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
        "min": row[12], "gp": row[11]
    }
    rating = _compute_rating(stats, league_stats)

    # Component scores
    max_pts, max_reb, max_ast, max_stl, max_blk = 35, 14, 12, 2.5, 3.0

    player = {
        "player_name": row[0],
        "team_abbreviation": row[1],
        "rating": rating,
        "points_per_game": row[2],
        "rebounds_per_game": row[3],
        "assists_per_game": row[4],
        "steals_per_game": row[5],
        "blocks_per_game": row[6],
        "turnovers_per_game": row[7],
        "field_goal_pct": round(row[8] * 100, 1) if row[8] and row[8] < 1 else row[8],
        "three_point_pct": round(row[9] * 100, 1) if row[9] and row[9] < 1 else row[9],
        "games_played": row[11],
        "minutes_per_game": row[12]
    }

    breakdown = {
        "scoring": min(100, max(0, 50 + ((row[2] - (league_stats["pts_mean"] if league_stats else 12)) / (league_stats["pts_std"] if league_stats else 6)) * 25)),
        "rebounding": min(100, max(0, 50 + ((row[3] - (league_stats["reb_mean"] if league_stats else 4.5)) / (league_stats["reb_std"] if league_stats else 2.5)) * 25)),
        "playmaking": min(100, max(0, 50 + ((row[4] - (league_stats["ast_mean"] if league_stats else 3)) / (league_stats["ast_std"] if league_stats else 2)) * 25)),
        "defense": min(100, max(0, 50 + (((row[5] + row[6]) - ((league_stats["stl_mean"] if league_stats else 1) + (league_stats["blk_mean"] if league_stats else 0.5))) / ((league_stats["stl_std"] if league_stats else 0.5) + (league_stats["blk_std"] if league_stats else 0.5))) * 25)),
        "efficiency": min(100, max(0, 50 + ((row[8] or 0.45 - 0.45) / 0.08) * 50))
    }

    # Get game log for trend chart
    game_result = execute_query(f"""
        SELECT game_date, points, rebounds, assists, steals, blocks,
               turnovers, minutes, field_goal_pct, three_point_pct
        FROM player_game_logs
        WHERE player_name = '{player_name}'
        ORDER BY game_date ASC
    """)

    game_log = []
    if not game_result["error"]:
        for g in game_result["rows"]:
            g_stats = {
                "pts": g[1], "reb": g[2], "ast": g[3],
                "stl": g[4], "blk": g[5], "tov": g[6],
                "fg_pct": g[8], "three_pct": g[9], "ft_pct": 0,
                "min": g[7] or 36, "gp": 1
            }
            g_rating = _compute_rating(g_stats, league_stats)
            game_log.append({
                "date": g[0],
                "rating": g_rating,
                "points": g[1],
                "rebounds": g[2],
                "assists": g[3]
            })

    return {
        "player": player,
        "rating": rating,
        "breakdown": breakdown,
        "game_log": game_log
    }
