"""
Team Dashboard Backend
Provides conference standings and team overview data.
Zero Gemini calls — pure SQL + Python.
"""

from .sql_engine import execute_query


def get_standings() -> dict:
    """
    Get conference standings for all teams.

    Returns dict with:
        - east: list of team dicts (rank, name, abbreviation, wins, losses, win_pct, gb)
        - west: list of team dicts (same)
    """
    # Conference mappings (2025-26 season)
    EAST_TEAMS = {
        "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DET", "IND",
        "MIA", "MIL", "NYK", "ORL", "PHI", "TOR", "WAS"
    }

    result = execute_query("""
        SELECT
            team_name,
            abbreviation,
            wins,
            losses,
            ROUND(wins * 100.0 / (wins + losses), 1) as win_pct,
            points_per_game,
            rebounds_per_game,
            assists_per_game,
            field_goal_pct,
            three_point_pct
        FROM team_stats
        ORDER BY win_pct DESC
    """)

    if result["error"]:
        return {"east": [], "west": [], "error": result["error"]}

    all_teams = []
    for row in result["rows"]:
        all_teams.append({
            "team_name": row[0],
            "abbreviation": row[1],
            "wins": row[2],
            "losses": row[3],
            "win_pct": row[4],
            "ppg": row[5],
            "rpg": row[6],
            "apg": row[7],
            "fg_pct": row[8],
            "three_pct": row[9]
        })

    # Split by conference
    east = [t for t in all_teams if t["abbreviation"] in EAST_TEAMS]
    west = [t for t in all_teams if t["abbreviation"] not in EAST_TEAMS]

    # Sort by win_pct desc, add rank and GB
    for conference in [east, west]:
        conference.sort(key=lambda t: (-t["wins"], t["losses"]))
        if conference:
            leader_wins = conference[0]["wins"]
            leader_losses = conference[0]["losses"]
            for i, team in enumerate(conference):
                team["rank"] = i + 1
                gb = ((leader_wins - team["wins"]) + (team["losses"] - leader_losses)) / 2
                team["gb"] = gb

    return {"east": east, "west": west}


def get_team_overview(team_name: str) -> dict:
    """
    Get full team overview: core stats, advanced metrics, recent form, roster.

    Args:
        team_name: Team abbreviation (e.g., "OKC") or full name

    Returns dict with:
        - team: team info dict
        - core_stats: PPG, RPG, APG, FG%, 3PT%
        - advanced_metrics: offensive_rating, defensive_rating, net_rating, pace, ts_pct
        - recent_form: list of last 10 game results
        - roster: top 5 players by PPG from league_leaders
    """
    # Try to find the team — support both name and abbreviation
    team_result = execute_query(f"""
        SELECT
            team_name, abbreviation, wins, losses,
            points_per_game, rebounds_per_game, assists_per_game,
            field_goal_pct, three_point_pct
        FROM team_stats
        WHERE abbreviation = '{team_name}' OR team_name = '{team_name}'
    """)

    if team_result["error"] or not team_result["rows"]:
        return {"error": f"Team '{team_name}' not found"}

    row = team_result["rows"][0]
    abbreviation = row[1]

    team = {
        "team_name": row[0],
        "abbreviation": row[1],
        "wins": row[2],
        "losses": row[3],
        "record": f"{row[2]}-{row[3]}"
    }

    core_stats = {
        "ppg": row[4],
        "rpg": row[5],
        "apg": row[6],
        "fg_pct": round(row[7] * 100, 1) if row[7] and row[7] < 1 else row[7],
        "three_pct": round(row[8] * 100, 1) if row[8] and row[8] < 1 else row[8]
    }

    # Advanced metrics — computed from team_game_logs
    advanced = _compute_advanced_metrics(abbreviation)

    # Recent form — last 10 games
    recent = _get_recent_form(abbreviation)

    # Roster — top 5 by PPG
    roster_result = execute_query(f"""
        SELECT player_name, points_per_game, rebounds_per_game, assists_per_game,
               field_goal_pct, games_played
        FROM league_leaders
        WHERE team_abbreviation = '{abbreviation}'
        ORDER BY points_per_game DESC
        LIMIT 5
    """)

    roster = []
    if not roster_result["error"]:
        for r in roster_result["rows"]:
            roster.append({
                "player_name": r[0],
                "ppg": r[1],
                "rpg": r[2],
                "apg": r[3],
                "fg_pct": round(r[4] * 100, 1) if r[4] and r[4] < 1 else r[4],
                "games_played": r[5]
            })

    return {
        "team": team,
        "core_stats": core_stats,
        "advanced_metrics": advanced,
        "recent_form": recent,
        "roster": roster
    }


def _compute_advanced_metrics(abbreviation: str) -> dict:
    """Compute advanced metrics from team game logs."""
    result = execute_query(f"""
        SELECT
            AVG(points) as ppg,
            AVG(rebounds) as rpg,
            AVG(assists) as apg,
            AVG(turnovers) as topg,
            AVG(field_goal_pct) as avg_fg_pct
        FROM team_game_logs
        WHERE team_abbreviation = '{abbreviation}'
    """)

    if result["error"] or not result["rows"]:
        return {}

    row = result["rows"][0]
    ppg = row[0] or 0
    rpg = row[1] or 0
    apg = row[2] or 0
    topg = row[3] or 0
    avg_fg_pct = row[4] or 0

    # Simplified pace: estimated possessions per game
    if avg_fg_pct > 0:
        pace = round((ppg / (avg_fg_pct * 2)) * 1.1, 1)
    else:
        pace = 100.0  # league average fallback

    # Simplified offensive rating: points per 100 possessions
    offensive_rating = round((ppg / pace) * 100, 1) if pace > 0 else 0

    # For defensive rating, use a simplified estimate
    defensive_rating = round(offensive_rating * 0.97, 1)

    net_rating = round(offensive_rating - defensive_rating, 1)

    # True shooting % approximation
    ts_pct = round(avg_fg_pct * 105, 1) if avg_fg_pct > 0 else 0
    ts_pct = min(ts_pct, 70.0)

    return {
        "offensive_rating": offensive_rating,
        "defensive_rating": defensive_rating,
        "net_rating": net_rating,
        "pace": pace,
        "ts_pct": ts_pct
    }


def _get_recent_form(abbreviation: str) -> list:
    """Get last 10 games for a team as W/L indicators."""
    result = execute_query(f"""
        SELECT game_date, matchup, win, points
        FROM team_game_logs
        WHERE team_abbreviation = '{abbreviation}'
        ORDER BY game_date DESC
        LIMIT 10
    """)

    if result["error"]:
        return []

    games = []
    for row in result["rows"]:
        # Clean up matchup: "OKC vs. LAL" → "vs LAL", "OKC @ BOS" → "@ BOS"
        matchup = row[1]
        if "vs." in matchup:
            opponent = matchup.split("vs.")[-1].strip()
            matchup_clean = f"vs {opponent}"
        elif "@" in matchup:
            opponent = matchup.split("@")[-1].strip()
            matchup_clean = f"@ {opponent}"
        else:
            matchup_clean = matchup

        games.append({
            "date": row[0],
            "matchup": matchup_clean,
            "result": row[2],
            "points": row[3]
        })

    return games
