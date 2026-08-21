"""Tests for shot chart functionality."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.shot_charts import get_available_players, get_shot_data, get_zone_stats


def test_get_available_players():
    """Test retrieving available players."""
    players = get_available_players()
    assert len(players) > 0
    assert isinstance(players, list)


def test_players_are_sorted():
    """Test that player list is sorted alphabetically."""
    players = get_available_players()
    assert players == sorted(players)


def test_get_shot_data():
    """Test shot data retrieval."""
    players = get_available_players()
    if players:
        data = get_shot_data(players[0])
        assert "shots" in data
        assert "summary" in data
        assert "total_attempts" in data["summary"]
        assert "makes" in data["summary"]
        assert "fg_pct" in data["summary"]
        assert "avg_distance" in data["summary"]


def test_get_shot_data_structure():
    """Test that shot data has correct structure."""
    players = get_available_players()
    if players:
        data = get_shot_data(players[0])
        assert len(data["shots"]) > 0
        shot = data["shots"][0]
        assert "loc_x" in shot
        assert "loc_y" in shot
        assert "shot_made_flag" in shot
        assert "shot_distance" in shot
        assert "shot_zone_basic" in shot


def test_shot_made_flag_values():
    """Test that shot_made_flag is 0 or 1."""
    players = get_available_players()
    if players:
        data = get_shot_data(players[0])
        for shot in data["shots"][:10]:  # Check first 10
            assert shot["shot_made_flag"] in (0, 1)


def test_get_shot_data_nonexistent_player():
    """Test shot data for non-existent player."""
    data = get_shot_data("Nonexistent Player XYZ")
    assert data["shots"] == []
    assert data["summary"] == {}


def test_get_zone_stats():
    """Test zone statistics."""
    players = get_available_players()
    if players:
        zones = get_zone_stats(players[0])
        assert len(zones) > 0
        assert "shot_zone_basic" in zones[0]
        assert "attempts" in zones[0]
        assert "makes" in zones[0]
        assert "fg_pct" in zones[0]


def test_zone_stats_fg_pct_range():
    """Test that FG% is between 0 and 100."""
    players = get_available_players()
    if players:
        zones = get_zone_stats(players[0])
        for zone in zones:
            assert 0 <= zone["fg_pct"] <= 100


def test_zone_stats_nonexistent_player():
    """Test zone stats for non-existent player."""
    zones = get_zone_stats("Nonexistent Player XYZ")
    assert zones == []


def test_shot_summary_fg_pct():
    """Test that FG% calculation matches makes/attempts."""
    players = get_available_players()
    if players:
        data = get_shot_data(players[0])
        summary = data["summary"]
        if summary["total_attempts"] > 0:
            expected_pct = round(
                summary["makes"] / summary["total_attempts"] * 100, 1
            )
            assert summary["fg_pct"] == expected_pct
