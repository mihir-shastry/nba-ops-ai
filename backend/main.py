"""
FastAPI Backend
Serves NBA player evaluation, comparison, and team analytics.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .teams import get_standings, get_team_overview
from .ratings import get_player_ratings, get_player_rating_detail
from .compare import get_player_stats, compare_players
from .matches import get_match_list
from .similarity import get_similar_players

app = FastAPI(
    title="NBA Player Evaluation System",
    description="Backend API for NBA analytics - ratings, comparison, and similarity",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Team Dashboard Endpoints
@app.get("/teams")
async def list_team_standings():
    """Get conference standings for all teams."""
    result = get_standings()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/teams/{team_name}")
async def get_team_detail(team_name: str):
    """Get full team overview including stats, advanced metrics, form, and roster."""
    result = get_team_overview(team_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# Player Rating Endpoints
@app.get("/ratings")
async def list_player_ratings(sort_by: str = "rating", limit: int = 50):
    """Get player ratings sorted by the rating formula."""
    result = get_player_ratings(sort_by=sort_by, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/ratings/{player_name}")
async def get_player_rating(player_name: str):
    """Get detailed rating breakdown for a single player."""
    result = get_player_rating_detail(player_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/ratings/{player_name}/matches")
async def get_player_matches(player_name: str, limit: int = 10):
    """Get recent matches for the player's team."""
    from .sql_engine import execute_query
    # First get the player's team
    result = execute_query(f"""
        SELECT team_abbreviation FROM league_leaders 
        WHERE player_name = '{player_name}'
    """)
    if result["error"] or not result["rows"]:
        raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
    
    team = result["rows"][0][0]
    matches = get_match_list(team=team)
    # Return only the most recent games
    matches["matches"] = matches["matches"][:limit]
    return matches


# Player Comparison Endpoints
@app.get("/compare/stats/{player_name}")
async def get_comparison_stats(player_name: str):
    """Get all stats for a player for comparison."""
    result = get_player_stats(player_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/compare/{player1}/{player2}")
async def compare_two_players(player1: str, player2: str):
    """Compare two players head-to-head."""
    result = compare_players(player1, player2)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# Player Similarity Endpoints
@app.get("/similar/{player_name}")
async def get_similar(player_name: str, limit: int = 5):
    """Find the most similar players using cosine distance on stat vectors."""
    result = get_similar_players(player_name, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
