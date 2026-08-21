"""Tests for RAG chatbot."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.rag_chat import get_knowledge_base, generate_response


def test_knowledge_base_build():
    """Test knowledge base construction."""
    kb = get_knowledge_base()
    assert len(kb.documents) > 0
    assert kb.index is not None


def test_knowledge_base_has_player_docs():
    """Test that knowledge base contains player stat documents."""
    kb = get_knowledge_base()
    player_docs = [
        m for m in kb.doc_metadata if m["type"] == "player_stats"
    ]
    assert len(player_docs) > 0


def test_knowledge_base_has_team_docs():
    """Test that knowledge base contains team stat documents."""
    kb = get_knowledge_base()
    team_docs = [
        m for m in kb.doc_metadata if m["type"] == "team_stats"
    ]
    assert len(team_docs) > 0


def test_knowledge_base_has_game_log_docs():
    """Test that knowledge base contains game log documents."""
    kb = get_knowledge_base()
    game_docs = [
        m for m in kb.doc_metadata if m["type"] == "game_log"
    ]
    assert len(game_docs) > 0


def test_search():
    """Test vector search."""
    kb = get_knowledge_base()
    results = kb.search("top scorers", k=3)
    assert len(results) > 0
    assert "document" in results[0]
    assert "distance" in results[0]
    assert "metadata" in results[0]


def test_search_returns_different_results():
    """Test that different queries return different results."""
    kb = get_knowledge_base()
    r1 = kb.search("three point shooting", k=3)
    r2 = kb.search("rebounding leaders", k=3)
    # At least one result should differ
    docs1 = [r["document"] for r in r1]
    docs2 = [r["document"] for r in r2]
    assert docs1 != docs2


def test_generate_response():
    """Test response generation."""
    kb = get_knowledge_base()
    response = generate_response("Who are the best players?", kb)
    assert len(response) > 0
    assert "NBA" in response or "player" in response.lower()


def test_generate_response_with_no_results():
    """Test response when search returns nothing."""
    kb = get_knowledge_base()
    # Use a very obscure query that shouldn't match
    response = generate_response(
        "quantum physics string theory", kb
    )
    # Should still return a response (either results or fallback)
    assert len(response) > 0


def test_knowledge_base_singleton():
    """Test that get_knowledge_base returns the same instance."""
    kb1 = get_knowledge_base()
    kb2 = get_knowledge_base()
    assert kb1 is kb2


def test_search_k_parameter():
    """Test that search respects k parameter."""
    kb = get_knowledge_base()
    r3 = kb.search("best scorer", k=3)
    r5 = kb.search("best scorer", k=5)
    assert len(r3) <= 3
    assert len(r5) <= 5
    # The first 3 results should be the same
    for i in range(min(len(r3), len(r5))):
        assert r3[i]["document"] == r5[i]["document"]
