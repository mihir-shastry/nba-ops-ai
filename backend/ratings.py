"""
Player Rating System
Hybrid percentile-rank + advanced metrics rating (0-100 scale).
Combines box score stats (PTS, REB, AST, STL, BLK, TOV) with advanced metrics
(TS%, USG%, NET_RATING, PIE) for a more complete player evaluation.
Zero Gemini calls — pure SQL + Python.
"""

import math
from .sql_engine import execute_query


def _percentile_rank(value, sorted_values):
    """
    Compute percentile rank (0-100) for a value within a sorted list.
    Returns the percentage of players this value exceeds.
    """
    if not sorted_values:
        return 50.0
    n = len(sorted_values)
    below = sum(1 for v in sorted_values if v < value)
    equal = sum(1 for v in sorted_values if v == value)
    return (below + 0.5 * equal) / n * 100


def _make_short_name(name):
    """Convert 'Stephen Curry' to 'S. Curry' for lineup name matching."""
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name


def _get_lineup_impact():
    """
    Compute per-player lineup impact (simplified RAPM) from 5-man lineup data.
    Returns dict of player_name -> (percentile, lineup_minutes).
    Players with < 100 lineup minutes get percentile = 50 (neutral).
    """
    result = execute_query("""
        SELECT team_abbreviation, lineup, games, minutes, plus_minus
        FROM lineup_stats
        WHERE games >= 5
    """)
    if result["error"] or not result["rows"]:
        return {}

    name_result = execute_query("SELECT player_name FROM league_leaders")
    if name_result["error"] or not name_result["rows"]:
        return {}
    full_names = [r[0] for r in name_result["rows"]]
    short_to_full = {}
    for fn in full_names:
        short = _make_short_name(fn)
        if short not in short_to_full:
            short_to_full[short] = fn

    team_stats = {}
    for row in result["rows"]:
        team, lineup, games, minutes, pm = row[0], row[1], row[2], row[3], row[4]
        if team not in team_stats:
            team_stats[team] = [0, 0]
        team_stats[team][0] += (pm or 0)
        team_stats[team][1] += (minutes or 0)

    team_baselines = {}
    for team, (pm, mins) in team_stats.items():
        team_baselines[team] = pm / mins if mins > 0 else 0

    team_result = execute_query("SELECT player_name, team_abbreviation FROM league_leaders")
    player_teams = {r[0]: r[1] for r in team_result["rows"]} if not team_result["error"] else {}

    player_lineups = {}
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

    player_relative = {}
    for player, lineups_data in player_lineups.items():
        total_pm = sum(pm * mins for pm, mins in lineups_data)
        total_mins = sum(mins for _, mins in lineups_data)
        if total_mins >= 100:
            team = player_teams.get(player)
            if team and team in team_baselines:
                abs_impact = total_pm / total_mins
                player_relative[player] = (abs_impact - team_baselines[team], total_mins)

    if not player_relative:
        return {}

    impacts = sorted(player_relative.values(), key=lambda x: x[0])
    impact_vals = [v[0] for v in impacts]

    return {
        player: (_percentile_rank(impact, impact_vals), mins)
        for player, (impact, mins) in player_relative.items()
    }


def _compute_rating(row, league_stats=None, advanced_stats=None, lineup_pct=50):
    """
    Compute a player rating using hybrid percentile ranks + advanced metrics.

    Args:
        row: dict with pts, reb, ast, stl, blk, tov, min, gp
        league_stats: dict with sorted value lists for each stat
        advanced_stats: dict with ts_pct, usg_pct, net_rating, pie
        lineup_pct: percentile of player's lineup impact (0-100), default 50

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

    # Normalize turnovers to per-36 minutes
    tov_per_36 = (tov / min_played) * 36

    if league_stats and "pts_sorted" in league_stats:
        # Box score percentile ranks (0-100)
        p_pts = _percentile_rank(pts, league_stats["pts_sorted"])
        p_reb = _percentile_rank(reb, league_stats["reb_sorted"])
        p_ast = _percentile_rank(ast, league_stats["ast_sorted"])
        p_stl = _percentile_rank(stl, league_stats["stl_sorted"])
        p_blk = _percentile_rank(blk, league_stats["blk_sorted"])
        p_tov = 100 - _percentile_rank(tov_per_36, league_stats["tov_sorted"])
    else:
        p_pts = min(100, max(0, pts / 35 * 100))
        p_reb = min(100, max(0, reb / 14 * 100))
        p_ast = min(100, max(0, ast / 12 * 100))
        p_stl = min(100, max(0, stl / 2.5 * 100))
        p_blk = min(100, max(0, blk / 3.0 * 100))
        p_tov = min(100, max(0, (4 - tov_per_36) / 4 * 100))

    # Advanced metric percentile ranks (0-100)
    if advanced_stats and league_stats:
        p_ts = _percentile_rank(advanced_stats.get("ts_pct", 0.5), league_stats.get("ts_sorted", [0.5]))
        p_usg = _percentile_rank(advanced_stats.get("usg_pct", 0.2), league_stats.get("usg_sorted", [0.2]))
        p_net = _percentile_rank(advanced_stats.get("net_rating", 0), league_stats.get("net_sorted", [0]))
        p_pie = _percentile_rank(advanced_stats.get("pie", 0.1), league_stats.get("pie_sorted", [0.1]))
    else:
        p_ts = 50
        p_usg = 50
        p_net = 50
        p_pie = 50

    # WEIGHTED COMBINATION
    # Box score components (counting stats)
    box_raw = (p_pts * 2.0 + p_reb * 0.6 + p_ast * 0.8 + p_stl * 0.2 + p_blk * 0.2 + p_tov * 0.3)
    
    # Advanced components (efficiency + impact)
    adv_raw = (p_ts * 1.5 + p_usg * 1.0 + p_net * 0.8 + p_pie * 0.5)
    
    # Combined raw score
    raw = box_raw + adv_raw

    # Sigmoid normalization
    # Mean raw ~550, scale factor controls spread
    rating = 100 / (1 + math.exp(-(raw - 550) / 100))
    rating = min(100, max(0, rating))

    return round(rating, 1)


def _get_league_stats():
    """
    Compute league-wide percentile distributions for box score + advanced stats.
    """
    # Box score stats
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
    if len(rows) < 2:
        return None

    pts_vals = sorted([r[0] or 0 for r in rows])
    reb_vals = sorted([r[1] or 0 for r in rows])
    ast_vals = sorted([r[2] or 0 for r in rows])
    stl_vals = sorted([r[3] or 0 for r in rows])
    blk_vals = sorted([r[4] or 0 for r in rows])
    tov_per_36_vals = sorted([
        ((r[5] or 0) / (r[6] or 36)) * 36 for r in rows
    ])

    # Advanced stats
    adv_result = execute_query("""
        SELECT true_shooting_pct, usage_pct, net_rating, pie
        FROM advanced_stats
    """)

    ts_vals = []
    usg_vals = []
    net_vals = []
    pie_vals = []

    if not adv_result["error"] and adv_result["rows"]:
        ts_vals = sorted([r[0] or 0.5 for r in adv_result["rows"]])
        usg_vals = sorted([r[1] or 0.2 for r in adv_result["rows"]])
        net_vals = sorted([r[2] or 0 for r in adv_result["rows"]])
        pie_vals = sorted([r[3] or 0.1 for r in adv_result["rows"]])

    return {
        # Box score sorted lists
        "pts_sorted": pts_vals,
        "reb_sorted": reb_vals,
        "ast_sorted": ast_vals,
        "stl_sorted": stl_vals,
        "blk_sorted": blk_vals,
        "tov_sorted": tov_per_36_vals,
        # Advanced sorted lists
        "ts_sorted": ts_vals if ts_vals else [0.5],
        "usg_sorted": usg_vals if usg_vals else [0.2],
        "net_sorted": net_vals if net_vals else [0],
        "pie_sorted": pie_vals if pie_vals else [0.1],
        # Keep mean/std for backwards compatibility
        "pts_mean": sum(pts_vals) / len(pts_vals),
        "pts_std": max(math.sqrt(sum((x - sum(pts_vals)/len(pts_vals))**2 for x in pts_vals) / len(pts_vals)), 1),
        "reb_mean": sum(reb_vals) / len(reb_vals),
        "reb_std": max(math.sqrt(sum((x - sum(reb_vals)/len(reb_vals))**2 for x in reb_vals) / len(reb_vals)), 0.5),
        "ast_mean": sum(ast_vals) / len(ast_vals),
        "ast_std": max(math.sqrt(sum((x - sum(ast_vals)/len(ast_vals))**2 for x in ast_vals) / len(ast_vals)), 0.5),
        "stl_mean": sum(stl_vals) / len(stl_vals),
        "stl_std": max(math.sqrt(sum((x - sum(stl_vals)/len(stl_vals))**2 for x in stl_vals) / len(stl_vals)), 0.1),
        "blk_mean": sum(blk_vals) / len(blk_vals),
        "blk_std": max(math.sqrt(sum((x - sum(blk_vals)/len(blk_vals))**2 for x in blk_vals) / len(blk_vals)), 0.1),
        "tov_mean": sum(tov_per_36_vals) / len(tov_per_36_vals),
        "tov_std": max(math.sqrt(sum((x - sum(tov_per_36_vals)/len(tov_per_36_vals))**2 for x in tov_per_36_vals) / len(tov_per_36_vals)), 0.3),
    }


def _component_percentile(value, sorted_vals):
    """Get percentile for a component score (for radar chart)."""
    return min(100, max(0, _percentile_rank(value, sorted_vals)))


def get_player_ratings(sort_by="rating", limit=50) -> dict:
    """
    Get all player ratings using hybrid percentile + advanced metrics.
    """
    league_stats = _get_league_stats()
    lineup_impact = _get_lineup_impact()

    result = execute_query("""
        SELECT
            l.player_name,
            l.team_abbreviation,
            l.points_per_game,
            l.rebounds_per_game,
            l.assists_per_game,
            l.steals_per_game,
            l.blocks_per_game,
            l.turnovers_per_game,
            l.field_goal_pct,
            l.three_point_pct,
            l.free_throw_pct,
            l.games_played,
            l.minutes_per_game,
            a.true_shooting_pct,
            a.usage_pct,
            a.net_rating,
            a.pie
        FROM league_leaders l
        LEFT JOIN advanced_stats a ON l.player_name = a.player_name
        WHERE l.games_played >= 20
        ORDER BY l.points_per_game DESC
    """)

    if result["error"]:
        return {"players": [], "columns": [], "error": result["error"]}

    players = []
    for row in result["rows"]:
        stats = {
            "pts": row[2], "reb": row[3], "ast": row[4],
            "stl": row[5], "blk": row[6], "tov": row[7],
            "min": row[12], "gp": row[11]
        }
        advanced = {
            "ts_pct": row[13] or 0.5,
            "usage_pct": row[14] or 0.2,
            "net_rating": row[15] or 0,
            "pie": row[16] or 0.1
        }
        lineup_pct = lineup_impact.get(row[0], (50, 0))[0]
        rating = _compute_rating(stats, league_stats, advanced, lineup_pct)

        # Component percentiles for radar chart
        scoring = _component_percentile(row[2], league_stats["pts_sorted"]) if league_stats else 50
        rebounding = _component_percentile(row[3], league_stats["reb_sorted"]) if league_stats else 50
        playmaking = _component_percentile(row[4], league_stats["ast_sorted"]) if league_stats else 50
        defense = _component_percentile(row[5] + row[6],
                    sorted([a + b for a, b in zip(league_stats["stl_sorted"], league_stats["blk_sorted"])])
                    ) if league_stats else 50
        efficiency = _component_percentile((row[13] or 0.5) * 100,
                     league_stats.get("ts_sorted", [0.5])
                     ) if league_stats else 50

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
            "lineup_impact": round(lineup_pct - 50, 1),
            "scoring": round(scoring, 1),
            "rebounding": round(rebounding, 1),
            "playmaking": round(playmaking, 1),
            "defense": round(defense, 1),
            "efficiency": round(efficiency, 1),
            # Advanced stats for display
            "true_shooting_pct": round((row[13] or 0) * 100, 1),
            "usage_pct": round((row[14] or 0) * 100, 1),
            "net_rating": round(row[15] or 0, 1),
        })

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
            l.player_name, l.team_abbreviation,
            l.points_per_game, l.rebounds_per_game, l.assists_per_game,
            l.steals_per_game, l.blocks_per_game, l.turnovers_per_game,
            l.field_goal_pct, l.three_point_pct, l.free_throw_pct,
            l.games_played, l.minutes_per_game,
            a.true_shooting_pct, a.usage_pct, a.net_rating, a.pie
        FROM league_leaders l
        LEFT JOIN advanced_stats a ON l.player_name = a.player_name
        WHERE l.player_name = '{player_name}'
    """)

    if result["error"] or not result["rows"]:
        return {"error": f"Player '{player_name}' not found"}

    row = result["rows"][0]
    stats = {
        "pts": row[2], "reb": row[3], "ast": row[4],
        "stl": row[5], "blk": row[6], "tov": row[7],
        "min": row[12], "gp": row[11]
    }
    advanced = {
        "ts_pct": row[13] or 0.5,
        "usage_pct": row[14] or 0.2,
        "net_rating": row[15] or 0,
        "pie": row[16] or 0.1
    }
    lineup_pct = lineup_impact.get(row[0], (50, 0))[0]
    rating = _compute_rating(stats, league_stats, advanced, lineup_pct)

    # Component percentiles
    scoring = _component_percentile(row[2], league_stats["pts_sorted"]) if league_stats else 50
    rebounding = _component_percentile(row[3], league_stats["reb_sorted"]) if league_stats else 50
    playmaking = _component_percentile(row[4], league_stats["ast_sorted"]) if league_stats else 50
    defense = _component_percentile(row[5] + row[6],
                sorted([a + b for a, b in zip(league_stats["stl_sorted"], league_stats["blk_sorted"])])
                ) if league_stats else 50
    efficiency = _component_percentile((row[13] or 0.5) * 100,
                 league_stats.get("ts_sorted", [0.5])
                 ) if league_stats else 50

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
        "lineup_impact": round(lineup_pct - 50, 1),
        "true_shooting_pct": round((row[13] or 0) * 100, 1),
        "usage_pct": round((row[14] or 0) * 100, 1),
        "net_rating": round(row[15] or 0, 1),
    }

    breakdown = {
        "scoring": round(scoring, 1),
        "rebounding": round(rebounding, 1),
        "playmaking": round(playmaking, 1),
        "defense": round(defense, 1),
        "efficiency": round(efficiency, 1),
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
