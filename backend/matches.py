"""
Match Dashboard Backend
Provides match detail: box scores, team stats, quarter scoring.
Zero Gemini calls — pure SQL + Python.
"""

from .sql_engine import execute_query
from .ratings import _compute_rating


def get_match_list(team: str = None, date_from: str = None, date_to: str = None) -> dict:
    """
    Get list of games with scores and basic stats.
    
    Returns dict with:
        - matches: list of match dicts
        - total_count: number of matches
    """
    conditions = []
    if team:
        conditions.append(f"team_abbreviation = '{team.upper()}'")
    if date_from:
        conditions.append(f"game_date >= '{date_from}'")
    if date_to:
        conditions.append(f"game_date <= '{date_to}'")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            game_id,
            team_abbreviation,
            game_date,
            matchup,
            win,
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

    result = execute_query(query)

    if result["error"]:
        return {"matches": [], "total_count": 0, "error": result["error"]}

    matches = []
    for row in result["rows"]:
        # Clean matchup
        matchup = row[3]
        if "vs." in matchup:
            opponent = matchup.split("vs.")[-1].strip()
            display = f"vs {opponent}"
        elif "@" in matchup:
            opponent = matchup.split("@")[-1].strip()
            display = f"@ {opponent}"
        else:
            display = matchup

        matches.append({
            "game_id": row[0],
            "team": row[1],
            "date": row[2],
            "matchup": display,
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

    return {
        "matches": matches,
        "total_count": len(matches)
    }


def get_match_detail(game_id: str) -> dict:
    """
    Get full match detail: box scores for both teams, quarter scoring, player stats.
    
    Returns dict with:
        - game: game info (date, matchup, final score)
        - home_team: team stats
        - away_team: team stats
        - player_stats: player-level stats for both teams
    """
    # Get both teams for this game
    result = execute_query(f"""
        SELECT
            team_abbreviation, game_date, matchup, win,
            points, rebounds, assists, steals, blocks, turnovers,
            field_goal_pct, three_point_pct, plus_minus
        FROM team_game_logs
        WHERE game_id = '{game_id}'
    """)

    if result["error"] or not result["rows"]:
        return {"error": f"Game '{game_id}' not found"}

    rows = result["rows"]
    if len(rows) < 2:
        return {"error": "Incomplete game data"}

    # Determine home and away teams
    team1 = rows[0]
    team2 = rows[1]

    matchup = team1[2]
    if "vs." in matchup:
        home_abbr = matchup.split("vs.")[0].strip()[-3:]
        away_abbr = team2[0]
    else:
        home_abbr = team1[0]
        away_abbr = team2[0]

    # Find which row is home vs away
    if team1[0] == home_abbr:
        home_row, away_row = team1, team2
    else:
        home_row, away_row = team2, team1

    def parse_team(row):
        return {
            "abbreviation": row[0],
            "date": row[1],
            "matchup": row[2],
            "result": row[3],
            "points": row[4],
            "rebounds": row[5],
            "assists": row[6],
            "steals": row[7],
            "blocks": row[8],
            "turnovers": row[9],
            "fg_pct": round(row[10] * 100, 1) if row[10] and row[10] < 1 else row[10],
            "three_pct": round(row[11] * 100, 1) if row[11] and row[11] < 1 else row[11],
            "plus_minus": row[12]
        }

    home_team = parse_team(home_row)
    away_team = parse_team(away_row)

    # Get player stats for this game (via game_date and matchup)
    game_date = team1[1]
    player_result = execute_query(f"""
        SELECT
            player_name, team_abbreviation,
            points, rebounds, assists, steals, blocks, turnovers,
            minutes, field_goal_pct, three_point_pct, plus_minus
        FROM player_game_logs
        WHERE game_date = '{game_date}'
        AND (team_abbreviation = '{home_abbr}' OR team_abbreviation = '{away_abbr}')
        ORDER BY team_abbreviation, points DESC
    """)

    player_stats = {"home": [], "away": []}
    if not player_result["error"]:
        for p in player_result["rows"]:
            stats = {
                "player_name": p[0],
                "team": p[1],
                "points": p[2],
                "rebounds": p[3],
                "assists": p[4],
                "steals": p[5],
                "blocks": p[6],
                "turnovers": p[7],
                "minutes": p[8],
                "fg_pct": round(p[9] * 100, 1) if p[9] and p[9] < 1 else p[9],
                "three_pct": round(p[10] * 100, 1) if p[10] and p[10] < 1 else p[10],
                "plus_minus": p[11]
            }
            # Compute per-game rating
            rating_stats = {
                "pts": p[2], "reb": p[3], "ast": p[4],
                "stl": p[5], "blk": p[6], "tov": p[7],
                "fg_pct": p[9], "three_pct": p[10], "ft_pct": 0,
                "min": p[8] or 36
            }
            stats["rating"] = _compute_rating(rating_stats)

            if p[1] == home_abbr:
                player_stats["home"].append(stats)
            else:
                player_stats["away"].append(stats)

    return {
        "game": {
            "game_id": game_id,
            "date": team1[1],
            "home_team": home_team,
            "away_team": away_team
        },
        "home_team": home_team,
        "away_team": away_team,
        "player_stats": player_stats
    }
