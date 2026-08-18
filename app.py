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
st.markdown('<div class="sub-header">SQL Analytics • Shot Charts • AI Assistant</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 SQL Analytics", "🎯 Shot Charts", "💬 AI Assistant"])


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


# Tab 3: AI Chatbot
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
