"""Tests for SQL engine."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.sql_engine import execute_query, get_prebuilt_queries, get_table_info


def test_execute_query():
    """Test basic SQL query execution."""
    result = execute_query("SELECT * FROM league_leaders LIMIT 3")
    assert result["row_count"] == 3
    assert len(result["columns"]) > 0
    assert result["error"] is None


def test_execute_query_returns_columns():
    """Test that query results include expected columns."""
    result = execute_query(
        "SELECT player_name, points_per_game FROM league_leaders LIMIT 1"
    )
    assert result["row_count"] == 1
    assert "player_name" in result["columns"]
    assert "points_per_game" in result["columns"]


def test_execute_invalid_query():
    """Test error handling for invalid SQL."""
    result = execute_query("SELECT * FROM nonexistent_table")
    assert result["error"] is not None


def test_execute_query_empty_result():
    """Test query that returns no rows."""
    result = execute_query(
        "SELECT * FROM league_leaders WHERE points_per_game > 999"
    )
    assert result["row_count"] == 0
    assert result["error"] is None


def test_prebuilt_queries():
    """Test pre-built queries exist."""
    queries = get_prebuilt_queries()
    assert len(queries) >= 5
    assert "top_scorers" in queries
    assert "efficient_scorers" in queries
    assert "home_vs_away" in queries
    assert "team_standings" in queries
    assert "triple_double_watch" in queries


def test_prebuilt_query_structure():
    """Test that each pre-built query has required fields."""
    queries = get_prebuilt_queries()
    for key, query in queries.items():
        assert "name" in query, f"Query '{key}' missing 'name'"
        assert "description" in query, f"Query '{key}' missing 'description'"
        assert "sql" in query, f"Query '{key}' missing 'sql'"
        assert query["sql"].strip().upper().startswith("SELECT"), (
            f"Query '{key}' doesn't start with SELECT"
        )


def test_execute_prebuilt_query():
    """Test executing a pre-built query."""
    queries = get_prebuilt_queries()
    result = execute_query(queries["top_scorers"]["sql"])
    assert result["row_count"] > 0
    assert result["error"] is None


def test_table_info():
    """Test table information retrieval."""
    tables = get_table_info()
    assert len(tables) >= 4
    table_names = [t["name"] for t in tables]
    assert "league_leaders" in table_names
    assert "team_stats" in table_names
    assert "player_game_logs" in table_names
    assert "shot_chart" in table_names


def test_table_info_structure():
    """Test that table info has required fields."""
    tables = get_table_info()
    for table in tables:
        assert "name" in table
        assert "columns" in table
        assert "row_count" in table
        assert isinstance(table["columns"], list)
        assert isinstance(table["row_count"], int)


def test_league_leaders_has_data():
    """Test that league_leaders table has data."""
    result = execute_query("SELECT COUNT(*) as count FROM league_leaders")
    assert result["row_count"] == 1
    assert result["rows"][0][0] > 0


def test_team_stats_has_data():
    """Test that team_stats table has data."""
    result = execute_query("SELECT COUNT(*) as count FROM team_stats")
    assert result["row_count"] == 1
    assert result["rows"][0][0] > 0
