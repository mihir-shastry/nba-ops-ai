"""
NBA Operations AI Assistant — Streamlit Frontend
Interactive dashboard for SQL analytics, shot charts, and AI chatbot.
"""

import os
import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="NBA Ops AI",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern dark theme styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
    }

    /* Header */
    .main-header {
        font-size: 2.8em;
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        padding: 0.5em 0;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #ff6b35, #f7c948, #ff6b35);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .sub-header {
        font-size: 1.1em;
        color: #a0a0b0;
        text-align: center;
        margin-top: -0.5em;
        margin-bottom: 1em;
    }

    /* Cards and containers */
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1em;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 5px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        color: #a0a0b0;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #ff6b35, #f7c948);
        color: #0f0f23;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #12122a;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #ff6b35;
        font-size: 1.1em;
        font-weight: 700;
    }

    /* SQL code block */
    .stCode {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Input styling */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
    }

    /* Button styling */
    .stButton button {
        background: linear-gradient(90deg, #ff6b35, #f7c948);
        color: #0f0f23;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.5em 2em;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
    }

    /* Success/Error messages */
    .stAlert {
        border-radius: 8px;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #f7c948;
    }

    /* Chat messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def check_backend():
    """Check if backend is running."""
    try:
        response = httpx.get(f"{BACKEND_URL}/chat/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# Sidebar
with st.sidebar:
    st.markdown("## 🏀 NBA Ops AI")
    st.markdown("---")

    st.markdown("### Features")
    st.markdown("""
    - **SQL Analytics** — Query NBA data
    - **Shot Charts** — Visualize shot locations
    - **Teams** — Standings and team overview
    - **Games** — Game log explorer
    - **Ratings** — Player ratings (0-100)
    - **Compare** — Player vs player
    - **Matches** — Game box scores
    - **AI Assistant** — Ask questions in natural language
    """)

    st.markdown("### Tech Stack")
    st.markdown("""
    `Python` `FastAPI` `Streamlit`
    `SQLite` `Gemini AI` `Plotly`
    """)

    st.markdown("---")

    st.markdown("### Status")
    if check_backend():
        st.success("✓ Backend Connected")
    else:
        st.error("✗ Backend Offline")
        st.code("$ make backend", language="bash")


# Main content
st.markdown('<div class="main-header">NBA Operations AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">SQL Analytics • Shot Charts • Teams • Games • Ratings • Compare • Matches • AI Assistant</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab4, tab5, tab6, tab7, tab8, tab3 = st.tabs(["📊 SQL Analytics", "🎯 Shot Charts", "🏆 Teams", "📅 Games", "⭐ Ratings", "🔄 Compare", "🏟️ Matches", "💬 AI Assistant"])


# Tab 1: SQL Analytics
with tab1:
    st.markdown("### Query NBA Data")

    col1, col2 = st.columns([2, 3])

    with col1:
        # Get pre-built queries
        try:
            response = httpx.get(f"{BACKEND_URL}/sql/prebuilt", timeout=10)
            queries = response.json()["queries"]

            # Create a mapping of keys to SQL
            query_map = {q["key"]: q for q in queries}

            selected = st.selectbox(
                "Pre-built Queries",
                options=[q["key"] for q in queries],
                format_func=lambda x: next(q["name"] for q in queries if q["key"] == x)
            )

            if selected:
                desc = query_map[selected]["description"]
                sql = query_map[selected]["sql"]
                st.info(desc)
                
                # Show a preview of the SQL
                with st.expander("👁️ Preview SQL", expanded=False):
                    st.code(sql, language="sql")
                
                # Button to use this query
                if st.button("📝 Use This Query", use_container_width=True):
                    st.session_state.selected_sql = sql
                    st.rerun()
        except Exception as e:
            st.warning(f"Could not load queries: {e}")
            selected = None

    with col2:
        # Get the SQL to display (from prebuilt selection or default)
        default_sql = st.session_state.get("selected_sql", "SELECT * FROM league_leaders ORDER BY points_per_game DESC LIMIT 10")
        
        # Custom SQL input
        custom_sql = st.text_area(
            "SQL Query",
            value=default_sql,
            height=120,
            label_visibility="collapsed"
        )

    # Execute button
    if st.button("▶ Run Query", type="primary", use_container_width=True):
        with st.spinner("Executing..."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/sql/execute",
                    json={"query": custom_sql},
                    timeout=30
                )
                result = response.json()

                if result.get("error"):
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"✓ {result['row_count']} rows returned")

                    df = pd.DataFrame(result["rows"], columns=result["columns"])
                    st.dataframe(df, use_container_width=True, height=400)

                    with st.expander("📋 View SQL"):
                        st.code(custom_sql, language="sql")
            except Exception as e:
                st.error(f"Connection error: {e}")


# Tab 2: Shot Charts
with tab2:
    st.markdown("### Shot Visualization")

    try:
        response = httpx.get(f"{BACKEND_URL}/shots/players", timeout=10)
        players = response.json()["players"]

        selected_player = st.selectbox("Select Player", players, key="shot_player")

        if selected_player:
            response = httpx.get(
                f"{BACKEND_URL}/shots/{selected_player}",
                timeout=30
            )
            data = response.json()

            # Summary stats
            summary = data["summary"]
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Attempts", f"{summary['total_attempts']:,}")
            with col2:
                st.metric("Makes", f"{summary['makes']:,}")
            with col3:
                st.metric("FG%", f"{summary['fg_pct']}%")
            with col4:
                st.metric("Avg Distance", f"{summary['avg_distance']} ft")

            st.markdown("---")

            # Shot chart visualization
            col_chart, col_zones = st.columns([3, 2])

            with col_chart:
                st.markdown("#### Shot Chart")

                shots = data["shots"]
                fig = go.Figure()

                # Court outline
                fig.add_shape(
                    type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5,
                    line=dict(color="#333355", width=2)
                )

                # Paint
                fig.add_shape(
                    type="rect", x0=-80, y0=-47.5, x1=80, y1=143.5,
                    line=dict(color="#333355", width=2)
                )

                # Three-point line
                fig.add_shape(
                    type="path",
                    path="M -220 -47.5 L -220 90 A 237.5 237.5 0 0 1 220 90 L 220 -47.5",
                    line=dict(color="#333355", width=2)
                )

                # Made shots (green)
                made = [s for s in shots if s["shot_made_flag"] == 1]
                if made:
                    fig.add_trace(go.Scatter(
                        x=[s["loc_x"] for s in made],
                        y=[s["loc_y"] for s in made],
                        mode="markers",
                        marker=dict(size=7, color="#00d4aa", opacity=0.8, line=dict(width=1, color="#00a88a")),
                        name="Made"
                    ))

                # Missed shots (red)
                missed = [s for s in shots if s["shot_made_flag"] == 0]
                if missed:
                    fig.add_trace(go.Scatter(
                        x=[s["loc_x"] for s in missed],
                        y=[s["loc_y"] for s in missed],
                        mode="markers",
                        marker=dict(size=7, color="#ff4757", opacity=0.6, line=dict(width=1, color="#cc3344")),
                        name="Missed"
                    ))

                fig.update_layout(
                    xaxis=dict(range=[-250, 250], showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(range=[-47.5, 422.5], showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor="#1a1a3e",
                    paper_bgcolor="#1a1a3e",
                    font=dict(color="white"),
                    legend=dict(
                        bgcolor="rgba(0,0,0,0.3)",
                        bordercolor="rgba(255,255,255,0.1)",
                        borderwidth=1
                    ),
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)

            with col_zones:
                st.markdown("#### Zone Efficiency")

                response = httpx.get(
                    f"{BACKEND_URL}/shots/{selected_player}/zones",
                    timeout=30
                )
                zones = response.json()["zones"]

                if zones:
                    zone_df = pd.DataFrame(zones)
                    fig_zones = go.Figure(data=[
                        go.Bar(
                            x=zone_df["shot_zone_basic"],
                            y=zone_df["fg_pct"],
                            text=zone_df["fg_pct"].apply(lambda x: f"{x}%"),
                            textposition="outside",
                            marker=dict(
                                color=zone_df["fg_pct"],
                                colorscale=[[0, "#ff4757"], [0.5, "#f7c948"], [1, "#00d4aa"]],
                                showscale=False
                            )
                        )
                    ])
                    fig_zones.update_layout(
                        xaxis_title="",
                        yaxis_title="FG%",
                        plot_bgcolor="#1a1a3e",
                        paper_bgcolor="#1a1a3e",
                        font=dict(color="white"),
                        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                        margin=dict(l=20, r=20, t=10, b=80),
                        height=500
                    )
                    st.plotly_chart(fig_zones, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load shot data: {e}")


# Tab 3: Team Dashboard
with tab4:
    st.markdown("### 🏆 Team Dashboard")
    st.markdown("*Conference standings — click a team to see their profile*")

    try:
        standings = httpx.get(f"{BACKEND_URL}/teams", timeout=10).json()

        if standings.get("error"):
            st.error(f"Error: {standings['error']}")
        else:
            # Check if we're viewing a team or the standings
            if "selected_team" not in st.session_state:
                st.session_state.selected_team = None

            if st.session_state.selected_team:
                # Team Overview
                team_name = st.session_state.selected_team

                if st.button("← Back to Standings"):
                    st.session_state.selected_team = None
                    st.rerun()

                team_data = httpx.get(f"{BACKEND_URL}/teams/{team_name}", timeout=10).json()

                if team_data.get("error"):
                    st.error(f"Error: {team_data['error']}")
                else:
                    team = team_data["team"]
                    core = team_data["core_stats"]
                    advanced = team_data["advanced_metrics"]
                    form = team_data["recent_form"]
                    roster = team_data["roster"]

                    # Header
                    st.markdown(f"## {team['team_name']}")
                    st.markdown(f"**Record:** {team['record']}")

                    # Core stats row
                    st.markdown("#### Core Stats")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("PPG", f"{core['ppg']:.1f}")
                    c2.metric("RPG", f"{core['rpg']:.1f}")
                    c3.metric("APG", f"{core['apg']:.1f}")
                    c4.metric("FG%", f"{core['fg_pct']:.1f}%")
                    c5.metric("3PT%", f"{core['three_pct']:.1f}%")

                    # Advanced metrics (expandable)
                    with st.expander("📊 Advanced Metrics", expanded=False):
                        if advanced:
                            a1, a2, a3, a4, a5 = st.columns(5)
                            a1.metric("Off Rating", f"{advanced.get('offensive_rating', 'N/A')}")
                            a2.metric("Def Rating", f"{advanced.get('defensive_rating', 'N/A')}")
                            a3.metric("Net Rating", f"{advanced.get('net_rating', 'N/A')}")
                            a4.metric("Pace", f"{advanced.get('pace', 'N/A')}")
                            a5.metric("TS%", f"{advanced.get('ts_pct', 'N/A')}%")
                        else:
                            st.info("Advanced metrics not available")

                    # Recent form
                    st.markdown("#### Recent Form (Last 10 Games)")
                    if form:
                        form_cols = st.columns(len(form))
                        for i, game in enumerate(form):
                            color = "#00d4aa" if game["result"] == "W" else "#ff4757"
                            form_cols[i].markdown(
                                f"<div style='text-align:center;padding:8px;border-radius:8px;"
                                f"background:rgba(0,180,120,0.15) if game['result']=='W' else rgba(255,71,87,0.15);"
                                f"border:2px solid {color}'>"
                                f"<div style='font-size:1.2em;font-weight:700;color:{color}'>{game['result']}</div>"
                                f"<div style='font-size:0.8em;color:#a0a0b0'>{game['matchup']}</div>"
                                f"<div style='font-size:0.8em;color:#a0a0b0'>{game['points']} pts</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("No recent games data")

                    # Roster
                    st.markdown("#### Top Players")
                    if roster:
                        roster_df = pd.DataFrame(roster)
                        st.dataframe(roster_df, use_container_width=True, hide_index=True)

            else:
                # Conference Standings
                col_east, col_west = st.columns(2)

                with col_east:
                    st.markdown("##### Eastern Conference")
                    east_data = standings.get("east", [])
                    if east_data:
                        east_df = pd.DataFrame(east_data)
                        east_df = east_df[["rank", "team_name", "wins", "losses", "win_pct", "gb"]]
                        east_df.columns = ["#", "Team", "W", "L", "Win%", "GB"]
                        st.dataframe(east_df, use_container_width=True, hide_index=True, height=560)

                        # Team selector
                        east_teams = [t["team_name"] for t in east_data]
                        selected_east = st.selectbox("View team profile", ["Select a team..."] + east_teams, key="east_select")
                        if selected_east != "Select a team...":
                            abbrev = next(t["abbreviation"] for t in east_data if t["team_name"] == selected_east)
                            st.session_state.selected_team = abbrev
                            st.rerun()

                with col_west:
                    st.markdown("##### Western Conference")
                    west_data = standings.get("west", [])
                    if west_data:
                        west_df = pd.DataFrame(west_data)
                        west_df = west_df[["rank", "team_name", "wins", "losses", "win_pct", "gb"]]
                        west_df.columns = ["#", "Team", "W", "L", "Win%", "GB"]
                        st.dataframe(west_df, use_container_width=True, hide_index=True, height=560)

                        # Team selector
                        west_teams = [t["team_name"] for t in west_data]
                        selected_west = st.selectbox("View team profile", ["Select a team..."] + west_teams, key="west_select")
                        if selected_west != "Select a team...":
                            abbrev = next(t["abbreviation"] for t in west_data if t["team_name"] == selected_west)
                            st.session_state.selected_team = abbrev
                            st.rerun()

    except Exception as e:
        st.error(f"Could not load team data: {e}")


# Tab 4: Game Log Explorer
with tab5:
    st.markdown("### 📅 Game Log Explorer")
    st.markdown("*Browse game results — click a game to see the full box score*")

    try:
        teams_data = httpx.get(f"{BACKEND_URL}/games/teams", timeout=10).json()
        available_teams = teams_data.get("teams", [])

        col_team, col_result = st.columns(2)
        with col_team:
            selected_team = st.selectbox("Filter by team", ["All Teams"] + available_teams, key="game_team_filter")
        with col_result:
            selected_result = st.selectbox("Filter by result", ["All", "Wins", "Losses"], key="game_result_filter")

        params = {}
        if selected_team != "All Teams":
            params["team"] = selected_team
        if selected_result == "Wins":
            params["result"] = "W"
        elif selected_result == "Losses":
            params["result"] = "L"

        games_response = httpx.get(f"{BACKEND_URL}/matches", params=params, timeout=15).json()
        matches = games_response.get("matches", [])

        if matches:
            st.markdown(f"**{games_response.get('total_count', 0)} games** found")

            # Show game selector
            game_options = [f"{m['date']} — {m['team']} {m['matchup']} ({m['result']} {m['points']})" for m in matches[:50]]
            game_map = {opt: m for opt, m in zip(game_options, matches[:50])}

            selected_game = st.selectbox("Select a game to view details", game_options, key="game_select")

            if selected_game:
                game = game_map[selected_game]
                detail = httpx.get(f"{BACKEND_URL}/matches/{game['game_id']}", timeout=15).json()

                if "error" not in detail:
                    g = detail["game"]
                    home = detail["home_team"]
                    away = detail["away_team"]
                    player_stats = detail["player_stats"]

                    # Scoreboard
                    sc1, sc_sep, sc2 = st.columns([2, 1, 2])
                    with sc1:
                        home_color = "#00d4aa" if home["result"] == "W" else "#ff4757"
                        st.markdown(f"<div style='text-align:center'><div style='font-size:2em;font-weight:800;color:{home_color}'>{home['points']}</div><div style='font-size:1.2em;font-weight:600'>{home['abbreviation']}</div></div>", unsafe_allow_html=True)
                    with sc_sep:
                        st.markdown("<div style='text-align:center;font-size:1.5em;color:#a0a0b0;padding-top:20px'>vs</div>", unsafe_allow_html=True)
                    with sc2:
                        away_color = "#00d4aa" if away["result"] == "W" else "#ff4757"
                        st.markdown(f"<div style='text-align:center'><div style='font-size:2em;font-weight:800;color:{away_color}'>{away['points']}</div><div style='font-size:1.2em;font-weight:600'>{away['abbreviation']}</div></div>", unsafe_allow_html=True)

                    st.markdown(f"<div style='text-align:center;color:#a0a0b0'>{g['date']}</div>", unsafe_allow_html=True)

                    # Team stats comparison
                    st.markdown("#### Team Stats")
                    tc1, tc2, tc3, tc4 = st.columns(4)
                    with tc1:
                        st.metric(f"{home['abbreviation']} REB", home["rebounds"])
                        st.metric(f"{away['abbreviation']} REB", away["rebounds"])
                    with tc2:
                        st.metric(f"{home['abbreviation']} AST", home["assists"])
                        st.metric(f"{away['abbreviation']} AST", away["assists"])
                    with tc3:
                        st.metric(f"{home['abbreviation']} FG%", f"{home['fg_pct']}%")
                        st.metric(f"{away['abbreviation']} FG%", f"{away['fg_pct']}%")
                    with tc4:
                        st.metric(f"{home['abbreviation']} +/-", f"{home['plus_minus']:+.0f}")
                        st.metric(f"{away['abbreviation']} +/-", f"{away['plus_minus']:+.0f}")

                    # Box scores
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        st.markdown(f"#### {home['abbreviation']} Box Score")
                        if player_stats["home"]:
                            home_df = pd.DataFrame(player_stats["home"])
                            home_df = home_df[["player_name", "minutes", "points", "rebounds", "assists", "steals", "blocks", "turnovers", "rating"]]
                            home_df.columns = ["Player", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "Rating"]
                            st.dataframe(home_df, use_container_width=True, hide_index=True)
                    with bc2:
                        st.markdown(f"#### {away['abbreviation']} Box Score")
                        if player_stats["away"]:
                            away_df = pd.DataFrame(player_stats["away"])
                            away_df = away_df[["player_name", "minutes", "points", "rebounds", "assists", "steals", "blocks", "turnovers", "rating"]]
                            away_df.columns = ["Player", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "Rating"]
                            st.dataframe(away_df, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"Could not load game details: {detail['error']}")
        else:
            st.info("No games found.")

    except Exception as e:
        st.error(f"Could not load games: {e}")

# Tab 5: Player Ratings
with tab6:
    st.markdown("### ⭐ Player Ratings")
    st.markdown("*Context-aware ratings (0-100) based on stats, efficiency, and consistency*")

    try:
        # Sort options
        sort_col, limit_col = st.columns(2)
        with sort_col:
            sort_by = st.selectbox("Sort by", ["rating", "pts", "reb", "ast"], format_func=lambda x: {"rating": "Overall Rating", "pts": "Points", "reb": "Rebounds", "ast": "Assists"}[x], key="rating_sort")
        with limit_col:
            limit = st.slider("Show top N", 10, 100, 50, key="rating_limit")

        ratings_data = httpx.get(f"{BACKEND_URL}/ratings?sort_by={sort_by}&limit={limit}", timeout=15).json()
        players = ratings_data.get("players", [])

        if players:
            # Display as table
            display_df = pd.DataFrame(players)
            display_df = display_df[["player_name", "team_abbreviation", "rating", "points_per_game", "rebounds_per_game", "assists_per_game", "steals_per_game", "blocks_per_game", "field_goal_pct", "three_point_pct"]]
            display_df.columns = ["Player", "Team", "Rating", "PPG", "RPG", "APG", "SPG", "BPG", "FG%", "3PT%"]

            # Color-code rating
            def color_rating(val):
                if val >= 90:
                    return "color: #f7c948; font-weight: bold"
                elif val >= 80:
                    return "color: #00d4aa; font-weight: bold"
                elif val >= 70:
                    return "color: #ffffff"
                return "color: #a0a0b0"

            styled_df = display_df.style.map(color_rating, subset=["Rating"])
            st.dataframe(styled_df, use_container_width=True, height=600)

            # Player detail
            st.markdown("---")
            player_names = [p["player_name"] for p in players]
            selected = st.selectbox("View player detail", ["Select a player..."] + player_names, key="rating_player_select")

            if selected != "Select a player...":
                detail = httpx.get(f"{BACKEND_URL}/ratings/{selected}", timeout=15).json()

                if "error" not in detail:
                    player = detail["player"]
                    rating = detail["rating"]
                    breakdown = detail["breakdown"]
                    game_log = detail["game_log"]

                    col_name, col_rating = st.columns([3, 1])
                    with col_name:
                        st.markdown(f"## {player['player_name']}")
                        st.markdown(f"**{player['team_abbreviation']}** | {player['games_played']} games | {player['minutes_per_game']:.1f} MPG")
                    with col_rating:
                        st.markdown(f"<div style='text-align:center;font-size:4em;font-weight:800;color:#f7c948'>{rating}</div>", unsafe_allow_html=True)
                        st.markdown("<div style='text-align:center;color:#a0a0b0'>RATING</div>", unsafe_allow_html=True)

                    # Radar chart
                    categories = ["Scoring", "Rebounding", "Playmaking", "Defense", "Efficiency"]
                    values = [breakdown["scoring"], breakdown["rebounding"], breakdown["playmaking"], breakdown["defense"], breakdown["efficiency"]]

                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=categories + [categories[0]],
                        fill="toself",
                        fillcolor="rgba(247, 201, 72, 0.2)",
                        line=dict(color="#f7c948", width=2),
                        name=player["player_name"]
                    ))
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
                            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                            bgcolor="#1a1a3e"
                        ),
                        showlegend=False,
                        paper_bgcolor="#1a1a3e",
                        font=dict(color="white"),
                        margin=dict(l=60, r=60, t=30, b=30),
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Game log trend
                    if game_log:
                        st.markdown("#### Rating Trend")
                        trend_df = pd.DataFrame(game_log)
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(
                            x=trend_df["date"], y=trend_df["rating"],
                            mode="lines+markers",
                            line=dict(color="#f7c948", width=2),
                            marker=dict(size=4),
                            name="Rating"
                        ))
                        fig_trend.update_layout(
                            xaxis_title="Game", yaxis_title="Rating",
                            yaxis=dict(range=[0, 100]),
                            plot_bgcolor="#1a1a3e", paper_bgcolor="#1a1a3e",
                            font=dict(color="white"),
                            margin=dict(l=20, r=20, t=10, b=40),
                            height=300
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)

                    # Season stats
                    st.markdown("#### Season Averages")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("PPG", f"{player['points_per_game']:.1f}")
                    c2.metric("RPG", f"{player['rebounds_per_game']:.1f}")
                    c3.metric("APG", f"{player['assists_per_game']:.1f}")
                    c4.metric("FG%", f"{player['field_goal_pct']:.1f}%")
                    c5.metric("3PT%", f"{player['three_point_pct']:.1f}%")
        else:
            st.info("No ratings data available.")

    except Exception as e:
        st.error(f"Could not load ratings: {e}")


# Tab 6: Player Comparison
with tab7:
    st.markdown("### 🔄 Player Comparison")
    st.markdown("*Compare two players head-to-head*")

    try:
        # Get all player names for dropdowns
        ratings_data = httpx.get(f"{BACKEND_URL}/ratings?limit=200", timeout=15).json()
        all_players = [p["player_name"] for p in ratings_data.get("players", [])]

        col1, col2 = st.columns(2)
        with col1:
            player1 = st.selectbox("Player 1", all_players, key="compare_p1")
        with col2:
            player2 = st.selectbox("Player 2", all_players, index=min(1, len(all_players)-1), key="compare_p2")

        if player1 and player2 and player1 != player2:
            comparison = httpx.get(f"{BACKEND_URL}/compare/{player1}/{player2}", timeout=15).json()

            if "error" not in comparison:
                p1 = comparison["player1"]["player"]
                p2 = comparison["player2"]["player"]
                r1 = comparison["player1"]["rating"]
                r2 = comparison["player2"]["rating"]
                rv1 = comparison["player1"]["radar_values"]
                rv2 = comparison["player2"]["radar_values"]
                stat_table = comparison["stat_table"]
                verdicts = comparison["verdicts"]

                # Player headers
                hdr1, hdr2 = st.columns(2)
                with hdr1:
                    st.markdown(f"<div style='text-align:center;font-size:1.8em;font-weight:800;color:#f7c948'>{r1}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;font-size:1.2em;font-weight:600'>{p1['player_name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;color:#a0a0b0'>{p1['team_abbreviation']} | {p1['points_per_game']:.1f} PPG</div>", unsafe_allow_html=True)
                with hdr2:
                    st.markdown(f"<div style='text-align:center;font-size:1.8em;font-weight:800;color:#ff6b35'>{r2}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;font-size:1.2em;font-weight:600'>{p2['player_name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;color:#a0a0b0'>{p2['team_abbreviation']} | {p2['points_per_game']:.1f} PPG</div>", unsafe_allow_html=True)

                # Overlapping radar chart
                categories = ["Scoring", "Rebounding", "Playmaking", "Defense", "Efficiency"]
                vals1 = [rv1[c] for c in categories]
                vals2 = [rv2[c] for c in categories]

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=vals1 + [vals1[0]], theta=categories + [categories[0]],
                    fill="toself", fillcolor="rgba(247, 201, 72, 0.15)",
                    line=dict(color="#f7c948", width=2), name=p1["player_name"]
                ))
                fig.add_trace(go.Scatterpolar(
                    r=vals2 + [vals2[0]], theta=categories + [categories[0]],
                    fill="toself", fillcolor="rgba(255, 107, 53, 0.15)",
                    line=dict(color="#ff6b35", width=2), name=p2["player_name"]
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
                        angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        bgcolor="#1a1a3e"
                    ),
                    showlegend=True,
                    legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(255,255,255,0.1)"),
                    paper_bgcolor="#1a1a3e", font=dict(color="white"),
                    margin=dict(l=60, r=60, t=30, b=30), height=450
                )
                st.plotly_chart(fig, use_container_width=True)

                # Verdict cards
                st.markdown("#### Verdicts")
                v_cols = st.columns(len(verdicts))
                for i, v in enumerate(verdicts):
                    if v["winner"] == "Even":
                        color = "#a0a0b0"
                        text = "Even"
                    elif v["winner"] == p1["player_name"]:
                        color = "#f7c948"
                        text = f"{v['winner']} {v['margin']}"
                    else:
                        color = "#ff6b35"
                        text = f"{v['winner']} {v['margin']}"
                    v_cols[i].markdown(
                        f"<div style='text-align:center;padding:12px;border-radius:8px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1)'>"
                        f"<div style='font-size:0.8em;color:#a0a0b0;margin-bottom:4px'>{v['category']}</div>"
                        f"<div style='font-size:1.1em;font-weight:700;color:{color}'>{text}</div>"
                        f"</div>", unsafe_allow_html=True
                    )

                # Stat comparison table
                st.markdown("#### Head-to-Head Stats")
                stat_df = pd.DataFrame(stat_table)
                stat_df = stat_df.rename(columns={"stat": "Stat", "player1_value": p1["player_name"], "player2_value": p2["player_name"]})
                st.dataframe(stat_df, use_container_width=True, hide_index=True)

            else:
                st.error(f"Error: {comparison['error']}")

    except Exception as e:
        st.error(f"Could not load comparison: {e}")


# Tab 7: Match Dashboard
with tab8:
    st.markdown("### 🏟️ Match Dashboard")
    st.markdown("*Game box scores with player ratings*")

    try:
        # Team filter
        teams_data = httpx.get(f"{BACKEND_URL}/games/teams", timeout=10).json()
        available_teams = teams_data.get("teams", [])

        col_team, col_limit = st.columns(2)
        with col_team:
            match_team = st.selectbox("Filter by team", ["All Teams"] + available_teams, key="match_team_filter")
        with col_limit:
            match_limit = st.slider("Show games", 10, 100, 30, key="match_limit")

        params = {}
        if match_team != "All Teams":
            params["team"] = match_team

        matches_response = httpx.get(f"{BACKEND_URL}/matches", params=params, timeout=15).json()
        matches = matches_response.get("matches", [])

        if matches:
            st.markdown(f"**{matches_response.get('total_count', 0)} games** found")

            # Display matches as clickable cards
            for i, match in enumerate(matches[:match_limit]):
                result_color = "#00d4aa" if match["result"] == "W" else "#ff4757"
                pm_color = "#00d4aa" if match["plus_minus"] >= 0 else "#ff4757"

                col_date, col_matchup, col_score, col_stats, col_detail = st.columns([1.5, 2, 1.5, 3, 1])

                with col_date:
                    st.markdown(f"<div style='color:#a0a0b0;font-size:0.9em'>{match['date']}</div>", unsafe_allow_html=True)
                with col_matchup:
                    st.markdown(f"<div style='font-weight:600'>{match['team']} {match['matchup']}</div>", unsafe_allow_html=True)
                with col_score:
                    st.markdown(f"<div style='color:{result_color};font-weight:700;font-size:1.2em'>{match['result']} {match['points']}</div>", unsafe_allow_html=True)
                with col_stats:
                    st.markdown(f"<div style='color:#a0a0b0'>PTS: {match['points']} | REB: {match['rebounds']} | AST: {match['assists']} | +/-: <span style='color:{pm_color}'>{match['plus_minus']:+.0f}</span></div>", unsafe_allow_html=True)
                with col_detail:
                    if st.button("View", key=f"match_{i}"):
                        st.session_state.selected_match = match["game_id"]
                        st.rerun()

            # Match detail view
            if "selected_match" in st.session_state and st.session_state.selected_match:
                game_id = st.session_state.selected_match

                if st.button("← Back to game list"):
                    st.session_state.selected_match = None
                    st.rerun()

                detail = httpx.get(f"{BACKEND_URL}/matches/{game_id}", timeout=15).json()

                if "error" not in detail:
                    game = detail["game"]
                    home = detail["home_team"]
                    away = detail["away_team"]
                    player_stats = detail["player_stats"]

                    # Scoreboard
                    st.markdown("---")
                    sc1, sc_sep, sc2 = st.columns([2, 1, 2])
                    with sc1:
                        home_color = "#00d4aa" if home["result"] == "W" else "#ff4757"
                        st.markdown(f"<div style='text-align:center'><div style='font-size:2em;font-weight:800;color:{home_color}'>{home['points']}</div><div style='font-size:1.2em;font-weight:600'>{home['abbreviation']}</div></div>", unsafe_allow_html=True)
                    with sc_sep:
                        st.markdown("<div style='text-align:center;font-size:1.5em;color:#a0a0b0;padding-top:20px'>vs</div>", unsafe_allow_html=True)
                    with sc2:
                        away_color = "#00d4aa" if away["result"] == "W" else "#ff4757"
                        st.markdown(f"<div style='text-align:center'><div style='font-size:2em;font-weight:800;color:{away_color}'>{away['points']}</div><div style='font-size:1.2em;font-weight:600'>{away['abbreviation']}</div></div>", unsafe_allow_html=True)

                    st.markdown(f"<div style='text-align:center;color:#a0a0b0'>{game['date']}</div>", unsafe_allow_html=True)

                    # Team stat comparison
                    st.markdown("#### Team Stats")
                    tc1, tc2, tc3 = st.columns(3)
                    with tc1:
                        st.metric(f"{home['abbreviation']} REB", home['rebounds'])
                        st.metric(f"{away['abbreviation']} REB", away['rebounds'])
                    with tc2:
                        st.metric(f"{home['abbreviation']} AST", home['assists'])
                        st.metric(f"{away['abbreviation']} AST", away['assists'])
                    with tc3:
                        st.metric(f"{home['abbreviation']} FG%", f"{home['fg_pct']}%")
                        st.metric(f"{away['abbreviation']} FG%", f"{away['fg_pct']}%")

                    # Box scores
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        st.markdown(f"#### {home['abbreviation']} Box Score")
                        if player_stats["home"]:
                            home_df = pd.DataFrame(player_stats["home"])
                            home_df = home_df[["player_name", "minutes", "points", "rebounds", "assists", "steals", "blocks", "turnovers", "rating"]]
                            home_df.columns = ["Player", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "Rating"]
                            st.dataframe(home_df, use_container_width=True, hide_index=True)
                    with bc2:
                        st.markdown(f"#### {away['abbreviation']} Box Score")
                        if player_stats["away"]:
                            away_df = pd.DataFrame(player_stats["away"])
                            away_df = away_df[["player_name", "minutes", "points", "rebounds", "assists", "steals", "blocks", "turnovers", "rating"]]
                            away_df.columns = ["Player", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "Rating"]
                            st.dataframe(away_df, use_container_width=True, hide_index=True)

        else:
            st.info("No games found.")

    except Exception as e:
        st.error(f"Could not load matches: {e}")


# Tab 8: Lineup Optimizer
with tab8:
    st.markdown("### 🔧 Lineup Optimizer")
    st.markdown("*5-man unit stats — find the best combinations*")

    try:
        teams_data = httpx.get(f"{BACKEND_URL}/games/teams", timeout=10).json()
        available_teams = teams_data.get("teams", [])

        view_mode = st.radio("View", ["League Best", "Team Lineups"], horizontal=True, key="lineup_view")

        if view_mode == "League Best":
            min_min, limit = st.columns(2)
            with min_min:
                min_minutes = st.slider("Min minutes together", 50, 500, 100, key="league_min_min")
            with limit:
                limit_val = st.slider("Show top N", 5, 50, 20, key="league_limit")

            best = httpx.get(f"{BACKEND_URL}/lineups/league/best?min_minutes={min_minutes}&limit={limit_val}", timeout=15).json()
            lineups = best.get("lineups", [])

            if lineups:
                st.markdown(f"**{best.get('total_count', 0)} qualifying lineups**")
                for i, lu in enumerate(lineups):
                    pm = lu["plus_minus"]
                    expander_title = f"#{i+1} {lu['team']} — {lu['lineup'][:60]}... ({pm:+.1f})"
                    with st.expander(expander_title):
                        c1, c2, c3, c4, c5 = st.columns(5)
                        c1.metric("Games", lu["games"])
                        c2.metric("Record", f"{lu['wins']}-{lu['losses']}")
                        c3.metric("Win%", f"{lu['win_pct']:.1%}")
                        c4.metric("Minutes", f"{lu['minutes']:.0f}")
                        c5.metric("+/-", f"{pm:+.1f}")
                        c6, c7, c8 = st.columns(3)
                        c6.metric("PPG", f"{lu['points']:.1f}")
                        c7.metric("RPG", f"{lu['rebounds']:.1f}")
                        c8.metric("APG", f"{lu['assists']:.1f}")
            else:
                st.info("No lineups found with those filters.")

        else:
            selected_team = st.selectbox("Select team", ["Select..."] + available_teams, key="lineup_team_select")
            if selected_team != "Select...":
                team_lineups = httpx.get(f"{BACKEND_URL}/lineups/{selected_team}?min_minutes=50", timeout=15).json()
                lineups = team_lineups.get("lineups", [])
                if lineups:
                    st.markdown(f"**{team_lineups.get('total_lineups', 0)} qualifying lineups for {selected_team}**")
                    for i, lu in enumerate(lineups):
                        pm = lu["plus_minus"]
                        expander_title = f"#{i+1} {lu['lineup'][:70]} ({pm:+.1f})"
                        with st.expander(expander_title):
                            c1, c2, c3, c4, c5 = st.columns(5)
                            c1.metric("Games", lu["games"])
                            c2.metric("Record", f"{lu['wins']}-{lu['losses']}")
                            c3.metric("Win%", f"{lu['win_pct']:.1%}")
                            c4.metric("Minutes", f"{lu['minutes']:.0f}")
                            c5.metric("+/-", f"{pm:+.1f}")
                            c6, c7, c8 = st.columns(3)
                            c6.metric("PPG", f"{lu['points']:.1f}")
                            c7.metric("RPG", f"{lu['rebounds']:.1f}")
                            c8.metric("APG", f"{lu['assists']:.1f}")
                else:
                    st.info(f"No qualifying lineups found for {selected_team}.")

    except Exception as e:
        st.error(f"Could not load lineups: {e}")

# Tab 11: AI Chatbot
with tab3:
    st.markdown("### AI Analytics Assistant")
    st.markdown("*Ask questions about NBA players and teams — powered by Text-to-SQL*")

    # Check if API key is configured
    import os
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.warning("⚠️ GEMINI_API_KEY not configured. Please set it in your environment to use the AI assistant.")
        st.code("export GEMINI_API_KEY=your_key_here", language="bash")
    else:
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sql"):
                    with st.expander("📝 Generated SQL", expanded=False):
                        st.code(msg["sql"], language="sql")

        # Chat input
        if query := st.chat_input("Ask about NBA players, teams, or stats..."):
            with st.chat_message("user"):
                st.markdown(query)
            st.session_state.messages.append({"role": "user", "content": query})

            with st.chat_message("assistant"):
                with st.spinner("Generating SQL and querying database..."):
                    try:
                        response = httpx.post(
                            f"{BACKEND_URL}/chat/ask",
                            json={"question": query},
                            timeout=60
                        )
                        
                        if response.status_code != 200:
                            # Handle error responses
                            error_detail = response.json().get("detail", "Unknown error")
                            answer = f"Error: {error_detail}"
                            st.error(answer)
                            sql = None
                        else:
                            result = response.json()
                            answer = result["answer"]
                            sql = result["sql"]
                            
                            st.markdown(answer)
                            with st.expander("📝 Generated SQL", expanded=False):
                                st.code(sql, language="sql")
                    except Exception as e:
                        answer = f"Error: {e}"
                        st.error(answer)
                        sql = None

            st.session_state.messages.append({"role": "assistant", "content": answer, "sql": sql})

    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            "Who are the top 5 scorers?",
            "Compare team records",
            "How does Shai perform in away games?",
            "Which players have the best FG%?",
            "Who leads the league in assists?",
            "What's the average points per game by team?"
        ]
        for ex in examples:
            st.markdown(f"• {ex}")
