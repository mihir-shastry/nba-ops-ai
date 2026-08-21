"""
Player Rating System
Z-score based player ratings (0-100 scale) computed from season averages.
Normalizes each stat to standard deviations from the mean, then combines
with weights. Uses TOV per 36 minutes to normalize for playing time.
Incorporates lineup-based impact (simplified RAPM) for on-court value.
Zero Gemini calls — pure SQL + Python.
"""

import math
from .sql_engine import execute_query


def _make_short_name(name):
    """Convert 'Stephen Curry' to 'S. Curry' for lineup name matching."""
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name


def _get_lineup_impact():
    """
    Compute per-player lineup impact (simplified RAPM) from 5-man lineup data.
    Returns dict of player_name -> (z_score, lineup_minutes).
    Players with < 100 lineup minutes get z_score = 0 (neutral).
    """
    # Get all lineups
    result = execute_query("""
        SELECT team_abbreviation, lineup, games, minutes, plus_minus
        FROM lineup_stats
        WHERE games >= 5
    """)
    if result["error"] or not result["rows"]:
        return {}

    # Build name mapping (short -> full)
    name_result = execute_query("SELECT player_name FROM league_leaders")
    if name_result["error"] or not name_result["rows"]:
        return {}
    full_names = [r[0] for r in name_result["rows"]]
    short_to_full = {}
    for fn in full_names:
        short = _make_short_name(fn)
        if short not in short_to_full:
            short_to_full[short] = fn

    # Build team baselines (+/- per minute)
    team_stats = {}  # team -> [total_pm, total_minutes]
    for row in result["rows"]:
        team, lineup, games, minutes, pm = row[0], row[1], row[2], row[3], row[4]
        if team not in team_stats:
            team_stats[team] = [0, 0]
        team_stats[team][0] += (pm or 0)
        team_stats[team][1] += (minutes or 0)

    team_baselines = {}
    for team, (pm, mins) in team_stats.items():
        team_baselines[team] = pm / mins if mins > 0 else 0

    # Get player teams
    team_result = execute_query("SELECT player_name, team_abbreviation FROM league_leaders")
    player_teams = {r[0]: r[1] for r in team_result["rows"]} if not team_result["error"] else {}

    # Compute per-player impact
    player_lineups = {}  # player -> [(pm_per_min, minutes)]
    for row in result["rows"]:
        team, lineup, games, minutes, pm = row[0], row[1], row[2], row[3], row[4]
        if not minutes or minutes <= 0:
            continue
        pm_per_min = (pm or 0) / minutes
        for short_name in lineup.split(' - '):
            short_name = short_name.strip()
            full_name = short_to_full.get(short_name)
            if full_name:
                if full_name not in player_lineups:
                    player_lineups[full_name] = []
                player_lineups[full_name].append((pm_per_min, minutes))

    # Compute weighted average +/- per minute, relative to team baseline
    player_relative = {}  # player -> (relative_impact, total_minutes)
    for player, lineups_data in player_lineups.items():
        total_pm = sum(pm * mins for pm, mins in lineups_data)
        total_mins = sum(mins for _, mins in lineups_data)
        if total_mins >= 100:  # Minimum 100 minutes for reliability
            team = player_teams.get(player)
            if team and team in team_baselines:
                abs_impact = total_pm / total_mins
                player_relative[player] = (abs_impact - team_baselines[team], total_mins)

    if not player_relative:
        return {}

    # Z-score normalize
    impacts = [v[0] for v in player_relative.values()]
    mean_imp = sum(impacts) / len(impacts)
    std_imp = math.sqrt(sum((x - mean_imp) ** 2 for x in impacts) / len(impacts))
    if std_imp <= 0:
        std_imp = 1

    return {
        player: ((impact - mean_imp) / std_imp, mins)
        for player, (impact, mins) in player_relative.items()
    }


def _compute_rating(row, league_stats=None, lineup_z=0):
    """
    Compute a player rating using z-score normalization.
    
    Args:
        row: dict with pts, reb, ast, stl, blk, tov, min, fg_pct, three_pct, ft_pct, gp
        league_stats: dict with mean and std for each stat (precomputed)
        lineup_z: z-score of player's lineup impact (simplified RAPM), default 0
    
    Returns:
        float: rating on 0-100 scale
    """
    pts = row.get("pts", 0) or 0
    reb = row.get("reb", 0) or 0
    ast = row.get("ast", 0) or 0
    stl = row.get("stl", 0) or 0
    blk = row.get("blk", 0) or 0
    tov = row.get("tov", 0) or 0
    min_played = row.get("min", 36) or 36
    gp = row.get("gp", 82) or 82
    
    # Normalize turnovers to per-36 minutes for fair comparison across roles
    tov_per_36 = (tov / min_played) * 36
    
    # Z-score normalization for each stat
    if league_stats:
        z_pts = (pts - league_stats["pts_mean"]) / league_stats["pts_std"] if league_stats["pts_std"] > 0 else 0
        z_reb = (reb - league_stats["reb_mean"]) / league_stats["reb_std"] if league_stats["reb_std"] > 0 else 0
        z_ast = (ast - league_stats["ast_mean"]) / league_stats["ast_std"] if league_stats["ast_std"] > 0 else 0
        z_stl = (stl - league_stats["stl_mean"]) / league_stats["stl_std"] if league_stats["stl_std"] > 0 else 0
        z_blk = (blk - league_stats["blk_mean"]) / league_stats["blk_std"] if league_stats["blk_std"] > 0 else 0
        z_tov = (tov_per_36 - league_stats["tov_mean"]) / league_stats["tov_std"] if league_stats["tov_std"] > 0 else 0
    else:
        # Fallback: use rough league averages
        z_pts = (pts - 12) / 6
        z_reb = (reb - 4.5) / 2.5
        z_ast = (ast - 3) / 2
        z_stl = (stl - 1) / 0.5
        z_blk = (blk - 0.5) / 0.5
        z_tov = (tov_per_36 - 2) / 1
    
    # Weighted combination
    # Scoring and playmaking are primary drivers; steals/blocks are supplementary;
    # turnovers penalized mildly (ball-handlers inherently have higher volume)
    # lineup_z is computed but reserved for future use with play-by-play data
    raw_z = (z_pts * 1.5 + z_reb * 0.8 + z_ast * 1.2 + z_stl * 1.0 + z_blk * 1.0
             - z_tov * 0.5)
    
    # Sigmoid scaling: maps raw_z to 0-100 with natural clustering
    # raw_z=0 → 50, raw_z=5 → ~82, raw_z=10 → ~98
    rating = 100 / (1 + math.exp(-raw_z / 3))
    rating = min(100, max(0, rating))
    
    return round(rating, 1)


def _get_league_stats():
    """Compute league-wide mean and std for each stat using actual standard deviation.
    Turnovers are normalized to per-36 minutes for fair comparison."""
    result = execute_query("""
        SELECT
            points_per_game, rebounds_per_game, assists_per_game,
            steals_per_game, blocks_per_game, turnovers_per_game,
            minutes_per_game
        FROM league_leaders
        WHERE games_played >= 20
    """)

    if result["error"] or not result["rows"]:
        return None

    rows = result["rows"]
    n = len(rows)
    if n < 2:
        return None

    # Compute actual mean and std for each stat
    stats = {"pts": [], "reb": [], "ast": [], "stl": [], "blk": []}
    tov_per_36_vals = []
    for row in rows:
        stats["pts"].append(row[0] or 0)
        stats["reb"].append(row[1] or 0)
        stats["ast"].append(row[2] or 0)
        stats["stl"].append(row[3] or 0)
        stats["blk"].append(row[4] or 0)
        raw_tov = row[5] or 0
        minutes = row[6] or 36
        tov_per_36_vals.append((raw_tov / minutes) * 36)

    def mean(vals):
        return sum(vals) / len(vals) if vals else 0

    def stddev(vals):
        m = mean(vals)
        variance = sum((x - m) ** 2 for x in vals) / len(vals)
        return math.sqrt(variance) if variance > 0 else 1

    return {
        "pts_mean": mean(stats["pts"]), "pts_std": max(stddev(stats["pts"]), 1),
        "reb_mean": mean(stats["reb"]), "reb_std": max(stddev(stats["reb"]), 0.5),
        "ast_mean": mean(stats["ast"]), "ast_std": max(stddev(stats["ast"]), 0.5),
        "stl_mean": mean(stats["stl"]), "stl_std": max(stddev(stats["stl"]), 0.1),
        "blk_mean": mean(stats["blk"]), "blk_std": max(stddev(stats["blk"]), 0.1),
        "tov_mean": mean(tov_per_36_vals), "tov_std": max(stddev(tov_per_36_vals), 0.3),
    }


def get_player_ratings(sort_by="rating", limit=50) -> dict:
    """
    Get all player ratings using z-score normalization.
    
    Returns dict with:
        - players: list of player dicts with name, team, rating, stats
        - columns: list of column names
    """
    league_stats = _get_league_stats()
    lineup_impact = _get_lineup_impact()

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
        lineup_z = lineup_impact.get(row[0], (0, 0))[0]
        rating = _compute_rating(stats, league_stats, lineup_z)

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
            "lineup_impact": round(lineup_z, 2),
            "scoring": min(100, max(0, 50 + ((row[2] - (league_stats["pts_mean"] if league_stats else 12)) / (league_stats["pts_std"] if league_stats else 6)) * 25)),
            "rebounding": min(100, max(0, 50 + ((row[3] - (league_stats["reb_mean"] if league_stats else 4.5)) / (league_stats["reb_std"] if league_stats else 2.5)) * 25)),
            "playmaking": min(100, max(0, 50 + ((row[4] - (league_stats["ast_mean"] if league_stats else 3)) / (league_stats["ast_std"] if league_stats else 2)) * 25)),
            "defense": min(100, max(0, 50 + (((row[5] + row[6]) - ((league_stats["stl_mean"] if league_stats else 1) + (league_stats["blk_mean"] if league_stats else 0.5))) / ((league_stats["stl_std"] if league_stats else 0.5) + (league_stats["blk_std"] if league_stats else 0.5))) * 25)),
            "efficiency": min(100, max(0, 50 + (((row[8] or 0.45) - 0.45) / 0.08) * 50))
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
    lineup_impact = _get_lineup_impact()

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
    lineup_z = lineup_impact.get(row[0], (0, 0))[0]
    rating = _compute_rating(stats, league_stats, lineup_z)

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
        "minutes_per_game": row[12],
        "lineup_impact": round(lineup_z, 2)
    }

    breakdown = {
        "scoring": min(100, max(0, 50 + ((row[2] - (league_stats["pts_mean"] if league_stats else 12)) / (league_stats["pts_std"] if league_stats else 6)) * 25)),
        "rebounding": min(100, max(0, 50 + ((row[3] - (league_stats["reb_mean"] if league_stats else 4.5)) / (league_stats["reb_std"] if league_stats else 2.5)) * 25)),
        "playmaking": min(100, max(0, 50 + ((row[4] - (league_stats["ast_mean"] if league_stats else 3)) / (league_stats["ast_std"] if league_stats else 2)) * 25)),
        "defense": min(100, max(0, 50 + (((row[5] + row[6]) - ((league_stats["stl_mean"] if league_stats else 1) + (league_stats["blk_mean"] if league_stats else 0.5))) / ((league_stats["stl_std"] if league_stats else 0.5) + (league_stats["blk_std"] if league_stats else 0.5))) * 25)),
        "efficiency": min(100, max(0, 50 + (((row[8] or 0.45) - 0.45) / 0.08) * 50))
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
