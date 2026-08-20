# NBA Operations AI — Feature Roadmap Design Spec

**Date:** 2026-08-18
**Author:** Buffy (Codebuff)
**Status:** Approved

## Overview

Enhance the NBA Operations AI dashboard with new analytical features while minimizing Gemini API usage. The project serves as both a portfolio piece and an open-source tool for NBA data exploration.

**Key constraint:** Gemini free tier has a 20 requests/day (RPD) limit. All features outside the chatbot must use zero Gemini calls — pure SQL + Python + Plotly.

## Current State

- **Backend:** FastAPI on port 8000
- **Frontend:** Streamlit on port 8501
- **Database:** SQLite with 4 tables: `league_leaders`, `team_stats`, `player_game_logs`, `shot_chart`
- **AI Chatbot:** Text-to-SQL via Gemini (currently 2 API calls per question)
- **Known issues:** Pre-built SQL queries fixed, chatbot now works with Gemini

---

## Phase 1: Foundation

### 1A. Single-Purpose Gemini Prompt (Rate Limit Fix)

**Problem:** Each chatbot question costs 2 Gemini API calls (SQL generation + answer formatting), limiting users to ~10 questions/day.

**Solution:** Combine into a single multi-turn conversation:
1. System message: schema + rules
2. User message: the question
3. Model generates SQL
4. User provides query results
5. Model generates natural language answer

**Implementation:**
- Modify `backend/text_to_sql.py`:
  - New function `answer_question_single_call()` using `client.models.generate_content()` with `types.GenerateContentConfig` and multi-turn `contents` list
- Keep `generate_sql()` and `generate_natural_answer()` as fallbacks
- Update `backend/main.py` `/chat/ask` endpoint to use the new single-call flow

**Expected impact:** Doubles daily capacity from ~10 to ~20 questions.

### 1B. Auto-Insights Dashboard

**Problem:** App feels static — users must ask questions to get value.

**Solution:** Proactively surface surprising stats on load.

**Backend:**
- New endpoint: `GET /insights`
- Runs 4-5 predefined analytical queries:
  - Most efficient high-volume scorer (points × FG%, min 40 games)
  - Biggest home vs away performance gap
  - Player closest to triple-double average
  - Team with best record but worst FG%
  - Player with highest 3PT% on high volume
- Returns pre-formatted insight cards (no Gemini — string templates)

**Frontend:**
- New section at top of SQL Analytics tab (or dedicated "Discoveries" section)
- Row of 4-5 styled metric cards with icons
- Clicking a card populates the SQL query in the text area

**Implementation:**
- New file: `backend/insights.py` — query functions
- Update `backend/main.py` — add `/insights` endpoint
- Update `app.py` — add insights section

---

## Phase 2: Core Features

### 2A. Player Comparison Tool

**Problem:** No way to compare players side-by-side.

**Solution:** Select two players and see radar charts + stat tables.

**Backend:**
- New endpoint: `GET /compare?player1={name}&player2={name}`
- Pulls from `league_leaders` table
- Returns both players' stats

**Frontend:**
- New tab or section: "Compare Players"
- Two selectboxes for player selection
- When both selected:
  - **Radar chart** (Plotly): PPG, RPG, APG, SPG, BPG, FG%, 3PT%, FT%
  - **Head-to-head stat table** — side-by-side columns
  - **"Verdict" card** — Python logic showing who leads in each category

**Design decisions:**
- All computation is SQL + Python — zero Gemini calls
- Uses existing `league_leaders` table
- Radar chart normalized to 0-100 scale for visual comparison

**Implementation:**
- Update `backend/main.py` — add `/compare` endpoint
- Update `app.py` — add comparison tab/section

### 2B. Shot Chart Enhancements

**Problem:** Basic shot chart lacks analytical depth.

**Solution:** Add heatmap overlay and zone analysis.

**Enhancements:**
1. **Heatmap overlay** — density visualization using Plotly `density_heatmap`
2. **Shot selection analysis** — "Player X takes 40% of shots from mid-range (league avg: 25%), where they shoot 38% (league avg: 42%)"
3. **"Where should they shoot?"** — compare zone efficiency to league averages, highlight underutilized high-efficiency zones

**Backend:**
- New endpoint: `GET /shots/{player_name}/analysis`
- Computes zone efficiency vs league average
- Returns analysis text and zone comparisons

**Frontend:**
- Enhance existing Shot Charts tab
- Add heatmap toggle
- Add "Shot Analysis" section below the chart
- Highlight recommended zones in green

**Implementation:**
- Update `backend/shot_charts.py` — add analysis functions
- Update `backend/main.py` — add `/shots/{player_name}/analysis` endpoint
- Update `app.py` — enhance shot chart UI

---

## Phase 3: Advanced Analytics

### 3A. Season Trends & Analytics

**Problem:** No temporal analysis — can't see how players/teams perform over time.

**Solution:** Show scoring trends, win/loss patterns, and momentum.

**Enhancements:**
1. **Scoring trend chart** — rolling average of PPG over season (from `player_game_logs`)
2. **Win/loss trend** — team-level win percentage over time
3. **Momentum indicator** — "Player X is averaging 35 PPG in last 10 games vs 28 PPG season average"
4. **Consistency score** — standard deviation of game-to-game points (lower = more consistent)

**Backend:**
- New endpoints:
  - `GET /trends/player/{player_name}` — scoring trends
  - `GET /trends/team/{team_name}` — win/loss trends
- SQL window functions for rolling averages

**Frontend:**
- New tab or section: "Trends"
- Interactive Plotly line charts
- Player/team selector
- Date range filter

**Implementation:**
- New file: `backend/trends.py` — trend calculation functions
- Update `backend/main.py` — add trend endpoints
- Update `app.py` — add trends tab/section

---

## Architecture

### Backend Changes

**New files:**
- `backend/insights.py` — auto-insight queries
- `backend/trends.py` — trend calculations

**Modified files:**
- `backend/text_to_sql.py` — single-call flow
- `backend/main.py` — new endpoints
- `backend/shot_charts.py` — analysis functions

**New endpoints:**
- `GET /insights` — auto-insights
- `GET /compare?player1=&player2=` — player comparison
- `GET /shots/{player_name}/analysis` — shot analysis
- `GET /trends/player/{player_name}` — scoring trends
- `GET /trends/team/{team_name}` — win/loss trends

### Frontend Changes

**Modified file:** `app.py`

**New sections:**
- Auto-insights cards at top of SQL Analytics tab
- Player Comparison tab (or section)
- Enhanced Shot Charts with heatmap
- Trends tab with interactive charts

### Data Flow

```
User Request
    ↓
Streamlit Frontend
    ↓ (HTTP)
FastAPI Backend
    ↓ (SQL)
SQLite Database
    ↓ (Results)
Backend Processing (Python)
    ↓ (JSON)
Frontend Visualization (Plotly)
```

**Gemini usage:** Only in chatbot, reduced from 2→1 calls per question.

---

## Error Handling

- All new endpoints return structured error responses
- Frontend handles 4xx/5xx with user-friendly messages
- Insights gracefully degrade if queries fail (show partial results)
- Shot analysis handles edge cases (no shots, single zone)

## Testing

- Unit tests for new backend functions
- Integration tests for new endpoints
- Frontend smoke tests for new UI sections

---

## Success Criteria

1. **Rate limit:** Chatbot uses ≤1 Gemini call per question
2. **Auto-insights:** Load time <2 seconds, shows 4-5 insights
3. **Player comparison:** Radar chart renders in <1 second
4. **Shot analysis:** Heatmap and recommendations display correctly
5. **Trends:** Charts render with real data from `player_game_logs`
6. **Zero Gemini calls** for all features except chatbot

---

## Out of Scope

- Authentication/user accounts
- Multi-season historical data (current DB is single season)
- Real-time data updates
- Mobile-responsive design (Streamlit handles this)
- Deployment/CI/CD setup
