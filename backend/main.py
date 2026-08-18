"""
FastAPI Backend
Serves SQL queries, shot visualizations, and RAG chatbot endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from .sql_engine import execute_query, get_prebuilt_queries, get_table_info
from .shot_charts import get_available_players, get_shot_data, get_zone_stats
from .rag_chat import get_knowledge_base, generate_response

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
    sources: list


# Knowledge base singleton
knowledge_base = None


@app.on_event("startup")
async def startup_event():
    """Build RAG knowledge base on startup."""
    global knowledge_base
    print("Building RAG knowledge base...")
    knowledge_base = get_knowledge_base()
    print(f"Knowledge base ready: {len(knowledge_base.documents)} documents")


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
                "description": value["description"]
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


# RAG Chat Endpoints
@app.post("/chat/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """Ask a natural language question about NBA data."""
    if not knowledge_base:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not initialized"
        )

    answer = generate_response(request.question, knowledge_base)
    results = knowledge_base.search(request.question, k=3)
    sources = [r["metadata"] for r in results]

    return ChatResponse(answer=answer, sources=sources)


@app.get("/chat/health")
async def chat_health():
    """Check if RAG system is ready."""
    return {
        "status": "ready" if knowledge_base else "initializing",
        "documents": len(knowledge_base.documents) if knowledge_base else 0
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
