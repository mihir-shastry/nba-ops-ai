"""
Player Similarity Model
Computes cosine distance between players using z-score stat vectors.
Enables "find similar players" functionality for scouting and evaluation.
"""

import math
from .sql_engine import execute_query


def _build_stat_vector(row, league_stats):
    """Build a normalized stat vector for a player using z-scores."""
    pts = row.get("pts", 0) or 0
    reb = row.get("reb", 0) or 0
    ast = row.get("ast", 0) or 0
    stl = row.get("stl", 0) or 0
    blk = row.get("blk", 0) or 0
    tov = row.get("tov", 0) or 0
    min_p = row.get("min", 36) or 36
    fg_pct = row.get("fg_pct", 0) or 0
    three_pct = row.get("three_pct", 0) or 0

    tov_per_36 = (tov / min_p) * 36

    def z(val, mean, std):
        return (val - mean) / std if std > 0 else 0

    return [
        z(pts, league_stats["pts_mean"], league_stats["pts_std"]),
        z(reb, league_stats["reb_mean"], league_stats["reb_std"]),
        z(ast, league_stats["ast_mean"], league_stats["ast_std"]),
        z(stl, league_stats["stl_mean"], league_stats["stl_std"]),
        z(blk, league_stats["blk_mean"], league_stats["blk_std"]),
        z(tov_per_36, league_stats["tov_mean"], league_stats["tov_std"]),
        z(fg_pct, league_stats["fg_mean"], league_stats["fg_std"]),
        z(three_pct, league_stats["three_mean"], league_stats["three_std"]),
    ]


def _cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0
    return dot / (mag_a * mag_b)


def _get_league_stats():
    """Compute league-wide mean and std for similarity computation."""
    result = execute_query("""
        SELECT
            points_per_game, rebounds_per_game, assists_per_game,
            steals_per_game, blocks_per_game, turnovers_per_game,
            minutes_per_game, field_goal_pct, three_point_pct
        FROM league_leaders
        WHERE games_played >= 20
    """)

    if result["error"] or not result["rows"]:
        return None

    rows = result["rows"]
    if len(rows) < 2:
        return None

    import math as m

    def mean(vals):
        return sum(vals) / len(vals) if vals else 0

    def stddev(vals):
        mv = mean(vals)
        variance = sum((x - mv) ** 2 for x in vals) / len(vals)
        return m.sqrt(variance) if variance > 0 else 1

    pts = [r[0] or 0 for r in rows]
    reb = [r[1] or 0 for r in rows]
    ast = [r[2] or 0 for r in rows]
    stl = [r[3] or 0 for r in rows]
    blk = [r[4] or 0 for r in rows]
    tov_p36 = [((r[5] or 0) / (r[6] or 36)) * 36 for r in rows]
    fg = [r[7] or 0 for r in rows]
    three = [r[8] or 0 for r in rows]

    return {
        "pts_mean": mean(pts), "pts_std": max(stddev(pts), 1),
        "reb_mean": mean(reb), "reb_std": max(stddev(reb), 0.5),
        "ast_mean": mean(ast), "ast_std": max(stddev(ast), 0.5),
        "stl_mean": mean(stl), "stl_std": max(stddev(stl), 0.1),
        "blk_mean": mean(blk), "blk_std": max(stddev(blk), 0.1),
        "tov_mean": mean(tov_p36), "tov_std": max(stddev(tov_p36), 0.3),
        "fg_mean": mean(fg), "fg_std": max(stddev(fg), 0.01),
        "three_mean": mean(three), "three_std": max(stddev(three), 0.01),
    }


def get_similar_players(player_name: str, limit: int = 5) -> dict:
    """
    Find the most similar players to a given player using cosine distance
    on z-score stat vectors.

    Returns dict with:
        - player: the queried player's info
        - similar_players: list of similar player dicts with similarity score
        - stat_vector_labels: labels for the stat vector dimensions
    """
    league_stats = _get_league_stats()
    if not league_stats:
        return {"error": "Could not compute league statistics"}

    # Get all players
    result = execute_query("""
        SELECT
            player_name, team_abbreviation,
            points_per_game, rebounds_per_game, assists_per_game,
            steals_per_game, blocks_per_game, turnovers_per_game,
            field_goal_pct, three_point_pct,
            games_played, minutes_per_game
        FROM league_leaders
        WHERE games_played >= 20
    """)

    if result["error"]:
        return {"error": result["error"]}

    # Build stat vectors for all players
    players = []
    target_vector = None
    target_info = None

    for row in result["rows"]:
        stats = {
            "pts": row[2], "reb": row[3], "ast": row[4],
            "stl": row[5], "blk": row[6], "tov": row[7],
            "fg_pct": row[8], "three_pct": row[9],
            "min": row[11],
        }
        vector = _build_stat_vector(stats, league_stats)
        info = {
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
            "games_played": row[10],
            "minutes_per_game": row[11],
        }

        if row[0] == player_name:
            target_vector = vector
            target_info = info

        players.append((info, vector))

    if not target_vector:
        return {"error": f"Player '{player_name}' not found"}

    # Compute similarity to all other players
    similarities = []
    for info, vector in players:
        if info["player_name"] == player_name:
            continue
        sim = _cosine_similarity(target_vector, vector)
        similarities.append({**info, "similarity": round(sim, 3)})

    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: -x["similarity"])

    return {
        "player": target_info,
        "similar_players": similarities[:limit],
        "stat_vector_labels": [
            "points", "rebounds", "assists", "steals", "blocks",
            "turnovers_per36", "field_goal_pct", "three_point_pct"
        ],
    }
