"""
NBA Operations AI Assistant — Streamlit Frontend
Interactive dashboard for SQL analytics, shot charts, and RAG chatbot.
"""

import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="NBA Operations AI Assistant",
    page_icon="basketball",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
    }
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
    st.header("About")
    st.markdown("""
    This demo showcases:
    - **SQL Analytics** — querying NBA data
    - **Spatiotemporal Viz** — shot charts
    - **RAG Chatbot** — natural language Q&A

    Built for: OKC Thunder Applied AI Engineer Intern
    """)

    st.header("Tech Stack")
    st.markdown("""
    - Python, FastAPI, Streamlit
    - SQLite (SQL)
    - FAISS (vector DB)
    - sentence-transformers
    - NBA API
    - Plotly (visualization)
    """)

    st.header("Backend Status")
    if check_backend():
        st.success("Backend connected")
    else:
        st.error("Backend not running")
        st.code("make backend", language="bash")


# Main content
st.markdown('<div class="main-header">NBA Operations AI Assistant</div>', unsafe_allow_html=True)
st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["SQL Analytics", "Shot Charts", "AI Assistant"])


# Tab 1: SQL Analytics
with tab1:
    st.header("SQL Analytics Dashboard")

    # Get pre-built queries
    try:
        response = httpx.get(f"{BACKEND_URL}/sql/prebuilt", timeout=10)
        queries = response.json()["queries"]

        selected = st.selectbox(
            "Select a pre-built query:",
            options=[q["key"] for q in queries],
            format_func=lambda x: next(q["name"] for q in queries if q["key"] == x)
        )

        desc = next(q["description"] for q in queries if q["key"] == selected)
        st.info(desc)
    except:
        st.warning("Could not load pre-built queries")
        selected = None

    # Custom SQL input
    st.subheader("Or enter your own SQL:")
    custom_sql = st.text_area(
        "SQL Query",
        value="SELECT * FROM league_leaders ORDER BY points_per_game DESC LIMIT 10",
        height=100
    )

    # Execute button
    if st.button("Run Query", type="primary"):
        with st.spinner("Executing query..."):
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
                    st.success(f"Query returned {result['row_count']} rows")

                    df = pd.DataFrame(result["rows"], columns=result["columns"])
                    st.dataframe(df, use_container_width=True)

                    with st.expander("View SQL Query"):
                        st.code(custom_sql, language="sql")
            except Exception as e:
                st.error(f"Connection error: {e}")


# Tab 2: Shot Charts
with tab2:
    st.header("Spatiotemporal Shot Analysis")

    # Get available players
    try:
        response = httpx.get(f"{BACKEND_URL}/shots/players", timeout=10)
        players = response.json()["players"]

        selected_player = st.selectbox("Select player:", players, key="shot_player")

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
                st.metric("Total Attempts", summary["total_attempts"])
            with col2:
                st.metric("Makes", summary["makes"])
            with col3:
                st.metric("FG%", summary["fg_pct"])
            with col4:
                st.metric("Avg Distance", f"{summary['avg_distance']} ft")

            # Shot chart visualization
            st.subheader("Shot Chart")

            shots = data["shots"]

            fig = go.Figure()

            # Court outline
            fig.add_shape(
                type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5,
                line=dict(color="black", width=2)
            )

            # Paint
            fig.add_shape(
                type="rect", x0=-80, y0=-47.5, x1=80, y1=143.5,
                line=dict(color="black", width=2)
            )

            # Three-point line
            fig.add_shape(
                type="path",
                path="M -220 -47.5 L -220 90 A 237.5 237.5 0 0 1 220 90 L 220 -47.5",
                line=dict(color="black", width=2)
            )

            # Made shots (green)
            made = [s for s in shots if s["shot_made"] == 1]
            if made:
                fig.add_trace(go.Scatter(
                    x=[s["x_coord"] for s in made],
                    y=[s["y_coord"] for s in made],
                    mode="markers",
                    marker=dict(size=8, color="green", opacity=0.7),
                    name="Made"
                ))

            # Missed shots (red)
            missed = [s for s in shots if s["shot_made"] == 0]
            if missed:
                fig.add_trace(go.Scatter(
                    x=[s["x_coord"] for s in missed],
                    y=[s["y_coord"] for s in missed],
                    mode="markers",
                    marker=dict(size=8, color="red", opacity=0.5),
                    name="Missed"
                ))

            fig.update_layout(
                title=f"{selected_player} - Shot Chart ({summary['fg_pct']}% FG)",
                xaxis=dict(range=[-250, 250], showgrid=False, zeroline=False),
                yaxis=dict(range=[-47.5, 422.5], showgrid=False, zeroline=False),
                width=700, height=600,
                plot_bgcolor="white",
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)

            # Zone breakdown
            st.subheader("Shot Zone Efficiency")
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
                        marker_color="steelblue"
                    )
                ])
                fig_zones.update_layout(
                    title="FG% by Shot Zone",
                    xaxis_title="Shot Zone",
                    yaxis_title="FG%",
                    height=400
                )
                st.plotly_chart(fig_zones, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load shot data: {e}")


# Tab 3: AI Chatbot
with tab3:
    st.header("AI Analytics Assistant")
    st.markdown("*Ask questions about NBA players and teams — powered by RAG*")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if query := st.chat_input("Ask about NBA players, teams, or stats..."):
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("assistant"):
            with st.spinner("Searching NBA knowledge base..."):
                try:
                    response = httpx.post(
                        f"{BACKEND_URL}/chat/ask",
                        json={"question": query},
                        timeout=30
                    )
                    answer = response.json()["answer"]
                    st.markdown(answer)
                except Exception as e:
                    answer = f"Error: {e}"
                    st.error(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

    # Example questions
    with st.expander("Example Questions"):
        examples = [
            "Who are the top 5 scorers?",
            "Compare team records",
            "How does Shai perform in away games?",
            "Which players have the best FG%?"
        ]
        for ex in examples:
            st.markdown(f"- {ex}")
