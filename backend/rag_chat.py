"""
RAG (Retrieval-Augmented Generation) Chatbot
Uses FAISS for vector search and sentence-transformers for embeddings.
"""

import faiss
import numpy as np
import sqlite3
import os
from sentence_transformers import SentenceTransformer

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nba_data.db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class NBAKnowledgeBase:
    """Vector knowledge base for NBA data using FAISS."""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.index = None
        self.documents = []
        self.doc_metadata = []

    def build_from_database(self):
        """Build knowledge base from SQLite database."""
        conn = sqlite3.connect(DB_PATH)

        # Create documents from player stats
        players = conn.execute("""
            SELECT player_name, team_abbreviation, points_per_game,
                   rebounds_per_game, assists_per_game, field_goal_pct,
                   three_point_pct, games_played
            FROM league_leaders
            ORDER BY points_per_game DESC
        """).fetchall()

        for p in players:
            doc = (
                f"{p[0]} plays for {p[1]}. "
                f"He averages {p[2]} points, {p[3]} rebounds, and {p[4]} assists per game. "
                f"He shoots {p[5]*100:.1f}% from the field and {p[6]*100:.1f}% from three. "
                f"He has played {p[7]} games this season."
            )
            self.documents.append(doc)
            self.doc_metadata.append({
                "type": "player_stats",
                "player_name": p[0],
                "team": p[1]
            })

        # Create documents from team stats
        teams = conn.execute("""
            SELECT team_name, abbreviation, wins, losses, points_per_game,
                   rebounds_per_game, assists_per_game, field_goal_pct
            FROM team_stats
            ORDER BY wins DESC
        """).fetchall()

        for t in teams:
            win_pct = t[2] / (t[2] + t[3]) * 100 if (t[2] + t[3]) > 0 else 0
            doc = (
                f"{t[0]} ({t[1]}) has a record of {t[2]}-{t[3]} "
                f"({win_pct:.1f}% win rate). "
                f"They average {t[4]} points, {t[5]} rebounds, and {t[6]} assists per game."
            )
            self.documents.append(doc)
            self.doc_metadata.append({
                "type": "team_stats",
                "team_name": t[0],
                "team": t[1]
            })

        # Create documents from game logs
        game_logs = conn.execute("""
            SELECT gl.player_name, gl.game_date, gl.matchup, gl.win,
                   gl.points, gl.rebounds, gl.assists
            FROM player_game_logs gl
            ORDER BY gl.game_date DESC
            LIMIT 100
        """).fetchall()

        for g in game_logs:
            result = "won" if g[3] == "W" else "lost"
            doc = (
                f"On {g[1]}, {g[0]} {result} against {g[2]}. "
                f"He had {g[4]} points, {g[5]} rebounds, and {g[6]} assists."
            )
            self.documents.append(doc)
            self.doc_metadata.append({
                "type": "game_log",
                "player_name": g[0],
                "date": g[1]
            })

        conn.close()

        # Build FAISS index
        if self.documents:
            embeddings = self.model.encode(self.documents, show_progress_bar=False)
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(np.array(embeddings, dtype=np.float32))

        return len(self.documents)

    def search(self, query: str, k: int = 5) -> list:
        """
        Search the knowledge base for relevant documents.

        Returns list of dicts with:
            - document: matched text
            - distance: similarity score (lower = more similar)
            - metadata: type, player_name, team, etc.
        """
        if not self.index:
            return []

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding, dtype=np.float32), k
        )

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    "document": self.documents[idx],
                    "distance": float(dist),
                    "metadata": self.doc_metadata[idx]
                })

        return results


def generate_response(query: str, knowledge_base: NBAKnowledgeBase) -> str:
    """
    Generate a response using RAG approach.

    1. Search for relevant documents
    2. Format them into a readable answer
    """
    results = knowledge_base.search(query, k=3)

    if not results:
        return "I don't have enough information to answer that question. Try asking about specific players or teams."

    response = "**Based on the latest NBA data:**\n\n"
    for i, r in enumerate(results, 1):
        response += f"{i}. {r['document']}\n\n"

    response += "---\n*Sources: NBA database with player stats, team stats, and game logs*"
    return response


# Singleton instance
_knowledge_base = None


def get_knowledge_base() -> NBAKnowledgeBase:
    """Get or initialize the knowledge base singleton."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = NBAKnowledgeBase()
        _knowledge_base.build_from_database()
    return _knowledge_base
