"""Test configuration and fixtures."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from stakeapi import StakeAPI


@pytest.fixture
def api_key():
    """Test API key."""
    return "test_api_key_12345"


@pytest.fixture
def mock_session():
    """Mock aiohttp session."""
    session = Mock()
    session.request = AsyncMock()
    return session


@pytest.fixture
async def stake_client(api_key):
    """StakeAPI client for testing."""
    client = StakeAPI(api_key=api_key)
    yield client
    await client.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "verified": True,
        "created_at": "2025-01-01T00:00:00Z",
        "country": "US",
        "currency": "USD"
    }


@pytest.fixture
def sample_game_data():
    """Sample game data for testing."""
    return {
        "id": "game123",
        "name": "Test Slot",
        "category": "slots",
        "provider": "Test Provider",
        "description": "A test slot game",
        "min_bet": "0.01",
        "max_bet": "100.00",
        "rtp": 96.5,
        "volatility": "medium",
        "features": ["free_spins", "wilds"],
        "thumbnail_url": "https://example.com/thumb.jpg"
    }


@pytest.fixture
def sample_sport_event_data():
    """Sample sport event data for testing."""
    return {
        "id": "event123",
        "sport": "football",
        "league": "Premier League",
        "home_team": "Team A",
        "away_team": "Team B",
        "start_time": "2025-01-15T15:00:00Z",
        "status": "upcoming",
        "odds": {"home": 2.5, "away": 3.2, "draw": 3.0},
        "live": False
    }
