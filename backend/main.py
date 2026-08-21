"""
FastAPI Backend
Serves SQL queries, shot visualizations, and Text-to-SQL chatbot endpoints.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .sql_engine import execute_query, get_prebuilt_queries, get_table_info
from .shot_charts import get_available_players, get_shot_data, get_zone_stats
from .text_to_sql import answer_question
from .teams import get_standings, get_team_overview
from .games import get_game_logs, get_available_teams
from .ratings import get_player_ratings, get_player_rating_detail
from .compare import get_player_stats, compare_players
from .matches import get_match_list, get_match_detail
from .lineups import get_team_lineups, get_league_best_lineups

app = FastAPI(
    title="NBA Operations AI Assistant",
    description="Backend API for NBA analytics dashboard",
    version="1.0.0"
)

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class SQLQueryRequest(BaseModel):
    query: str

class SQLQueryResponse(BaseModel):
    columns: list
    rows: list
    row_count: int
    error: Optional[str] = None

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sql: str
    columns: list
    rows: list


@app.on_event("startup")
async def startup_event():
    """Check for Gemini API key on startup."""
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not set. Chatbot will not work.")
        print("Set it with: export GEMINI_API_KEY=your_key_here")
    else:
        print("Gemini API key found. Chatbot ready.")


# SQL Endpoints
@app.get("/sql/tables")
async def list_tables():
    """List all tables in the database."""
    return {"tables": get_table_info()}


@app.get("/sql/prebuilt")
async def list_prebuilt_queries():
    """List all pre-built queries."""
    queries = get_prebuilt_queries()
    return {
        "queries": [
            {
                "key": key,
                "name": value["name"],
                "description": value["description"],
                "sql": value["sql"]
            }
            for key, value in queries.items()
        ]
    }


@app.post("/sql/execute", response_model=SQLQueryResponse)
async def run_sql_query(request: SQLQueryRequest):
    """Execute a SQL query and return results."""
    # Only allow SELECT queries
    if not request.query.strip().upper().startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed"
        )

    result = execute_query(request.query)
    return SQLQueryResponse(**result)


# Shot Chart Endpoints
@app.get("/shots/players")
async def list_shot_players():
    """Get list of players with shot chart data."""
    return {"players": get_available_players()}


@app.get("/shots/{player_name}")
async def get_player_shots(player_name: str):
    """Get shot chart data for a player."""
    data = get_shot_data(player_name)
    if not data["shots"]:
        raise HTTPException(
            status_code=404,
            detail=f"No shot data found for {player_name}"
        )
    return data


@app.get("/shots/{player_name}/zones")
async def get_player_zones(player_name: str):
    """Get shot zone statistics for a player."""
    zones = get_zone_stats(player_name)
    return {"zones": zones}


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


# Game Log Explorer Endpoints
@app.get("/games/teams")
async def list_game_teams():
    """Get list of teams available in game logs."""
    return {"teams": get_available_teams()}


@app.get("/games")
async def list_games(team: Optional[str] = None, result: Optional[str] = None):
    """Get game logs with optional team and result filters."""
    data = get_game_logs(team=team, result=result)
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data



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



# Match Dashboard Endpoints
@app.get("/matches")
async def list_matches(team: str = None, date_from: str = None, date_to: str = None):
    """Get list of games with scores and basic stats."""
    result = get_match_list(team=team, date_from=date_from, date_to=date_to)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/matches/{game_id}")
async def get_match(game_id: str):
    """Get full match detail: box scores, quarter scoring, player stats."""
    result = get_match_detail(game_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result



# Lineup Optimizer Endpoints
@app.get("/lineups/{team_name}")
async def get_team_lineup_stats(team_name: str, min_minutes: float = 50):
    """Get lineup stats for a team."""
    result = get_team_lineups(team_name, min_minutes=min_minutes)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/lineups/league/best")
async def get_best_lineups(min_minutes: float = 100, limit: int = 20):
    """Get the best lineups in the league by plus/minus."""
    result = get_league_best_lineups(min_minutes=min_minutes, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# Text-to-SQL Chat Endpoints
@app.post("/chat/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """Ask a natural language question about NBA data."""
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY not configured. Please set the environment variable."
        )
    
    try:
        result = answer_question(request.question)
        return ChatResponse(
            answer=result["answer"],
            sql=result["sql"],
            columns=result["columns"],
            rows=result["rows"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


@app.get("/chat/health")
async def chat_health():
    """Check if Text-to-SQL system is ready."""
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    return {
        "status": "ready" if api_key else "missing_api_key",
        "provider": "gemini" if api_key else None
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
