# NBA Operations AI Assistant

A **RAG-powered basketball analytics platform** demonstrating SQL analytics, spatiotemporal data visualization, and AI-powered question answering for NBA basketball operations.

## Project Overview

This project combines three core capabilities into a single interactive dashboard:

- **SQL Analytics** — Query NBA data with complex SQL (JOINs, aggregations, window functions)
- **Spatiotemporal Visualization** — Analyze shot locations and patterns over time
- **RAG Chatbot** — Ask natural language questions about players and teams

Built with Python, FastAPI, Streamlit, SQLite, FAISS, and sentence-transformers.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Fetch NBA Data

```bash
python data_pipeline.py
```

### 3. Run the App

```bash
# Terminal 1: Start backend
python -m backend.main

# Terminal 2: Start frontend
streamlit run app.py
```

Then open http://localhost:8501

## Features

### 1. SQL Analytics Dashboard
- Pre-built queries (top scorers, efficiency, home/away splits)
- Custom SQL input for advanced users
- Interactive result tables with sorting and filtering

### 2. Spatiotemporal Shot Charts
- Interactive shot location visualization (made vs missed)
- Zone efficiency breakdown by shot area
- Temporal trends showing shot patterns over time

### 3. Team Dashboard
- Conference standings (East/West) with win% and games behind
- Team overview with core stats (PPG, RPG, APG, FG%, 3PT%)
- Advanced metrics (offensive/defensive rating, pace, true shooting)
- Recent form (last 10 games) and top roster players

### 4. Game Log Explorer
- Filterable table of all game results
- Filter by team and W/L
- Box-score style data: points, rebounds, assists, +/-

### 5. RAG AI Assistant
- Natural language questions ("Who are the top scorers?")
- Context-aware answers powered by FAISS vector search
- Chat history with example prompts

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit Frontend (UI)                              │
│  ┌──────────┬──────────────┬──────────┬──────────┬────────────┐ │
│  │ SQL Tab  │ Charts Tab   │ Teams Tab│ Games Tab│ Chatbot    │ │
│  └────┬─────┴──────┬───────┴────┬─────┴────┬─────┴─────┬──────┘ │
├───────┴────────────┴────────────┴──────────┴───────────┴────────┤
│              FastAPI Backend (API)                               │
│  ┌─────────────┬──────────────┬────────┬────────┬────────────┐  │
│  │ /sql/query  │ /shots/      │ /teams │ /games │ /chat/ask  │  │
│  └──────┬──────┴──────┬───────┴────┬───┴────┬───┴─────┬──────┘  │
├─────────┴──────────────┴─────────────────┴──────────────┤
│              Data Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ SQLite   │  │ FAISS    │  │ NBA API              │   │
│  └──────────┘  └──────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Category | Tech | Why |
|----------|------|-----|
| **Backend** | FastAPI | Modern, fast, auto-generates API docs |
| **Frontend** | Streamlit | No HTML/CSS/JS, fast to build |
| **Database** | SQLite | Zero-config, file-based |
| **Vector DB** | FAISS | Free, local, fast similarity search |
| **Embeddings** | sentence-transformers | Free, no API key |
| **Charts** | Plotly | Interactive, web-native |
| **Data Source** | NBA API | Free, no API key |

## Project Structure

```
nba-ops-ai/
├── app.py                    # Streamlit frontend
├── data_pipeline.py          # Fetch NBA data to SQLite
├── requirements.txt          # Python dependencies
├── Makefile                  # Launch commands
├── README.md                 # This file
├── backend/
│   ├── __init__.py
│   ├── main.py               # FastAPI app
│   ├── sql_engine.py         # SQL execution
│   ├── shot_charts.py        # Shot chart logic
│   ├── teams.py              # Team dashboard logic
│   ├── games.py              # Game log explorer logic
│   └── rag_chat.py           # RAG chatbot
├── data/
│   └── nba_data.db           # SQLite database (generated)
└── tests/
    ├── test_sql_engine.py
    ├── test_shot_charts.py
    └── test_rag_chat.py
```

## Key Technical Decisions

1. **SQLite over PostgreSQL**: Zero-config, file-based, perfect for demos. SQL syntax transfers directly to production databases.
2. **FAISS over Pinecone**: No API keys required, runs locally, free forever.
3. **sentence-transformers over OpenAI**: No API costs, runs locally, full control.
4. **FastAPI backend**: Separation of concerns — backend logic independent of UI.
5. **Plotly over Matplotlib**: Interactive visualizations for web, not static images.

## Sample SQL Queries

```sql
-- Most efficient scorers (PPG × FG%)
SELECT 
    player_name,
    points_per_game,
    field_goal_pct,
    ROUND(points_per_game * field_goal_pct, 2) as efficiency
FROM league_leaders
WHERE games_played >= 40
ORDER BY efficiency DESC
LIMIT 10;

-- Home vs away performance
SELECT 
    player_name,
    CASE WHEN matchup LIKE '%vs%' THEN 'Home' ELSE 'Away' END as location,
    AVG(points) as avg_points
FROM player_game_logs
GROUP BY player_name, location;
```

## How It Works

### Data Pipeline
1. Fetches player stats, team records, game logs, and shot locations from the NBA API
2. Stores everything in SQLite with proper schema and indexes
3. Run once: `python data_pipeline.py`

### SQL Analytics
1. User selects a pre-built query or enters custom SQL
2. Streamlit sends request to FastAPI backend
3. Backend executes query against SQLite, returns results as JSON
4. Frontend displays results in interactive table

### Shot Charts
1. User selects a player from dropdown
2. Backend retrieves shot locations (x, y coordinates) from SQLite
3. Plotly renders shot chart with court outline, made/missed distinction
4. Zone efficiency bar chart shows shooting by area

### RAG Chatbot
1. On startup, backend builds FAISS index from NBA data
2. User asks a question in natural language
3. Sentence-transformers encodes question to vector
4. FAISS finds most similar documents (semantic search)
5. Backend formats response with retrieved context

## Running Tests

```bash
pytest tests/ -v
```

## License

This project is for educational and portfolio purposes.
