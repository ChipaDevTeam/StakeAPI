"""Tests for data models."""

import pytest
from datetime import datetime
from decimal import Decimal
from stakeapi.models import User, Game, SportEvent, Bet, Transaction, Statistics


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation(self, sample_user_data):
        """Test user creation from data."""
        user = User.from_dict(sample_user_data)
        
        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.verified is True
        assert user.currency == "USD"
        
    def test_user_minimal_data(self):
        """Test user creation with minimal data."""
        data = {
            "id": "user456",
            "username": "minimal_user",
            "verified": False,
            "created_at": "2025-01-01T00:00:00Z",
            "currency": "EUR"
        }
        
        user = User.from_dict(data)
        assert user.id == "user456"
        assert user.email is None
        assert user.country is None


class TestGameModel:
    """Test cases for Game model."""
    
    def test_game_creation(self, sample_game_data):
        """Test game creation from data."""
        game = Game.from_dict(sample_game_data)
        
        assert game.id == "game123"
        assert game.name == "Test Slot"
        assert game.category == "slots"
        assert game.provider == "Test Provider"
        assert game.min_bet == Decimal("0.01")
        assert game.max_bet == Decimal("100.00")
        assert game.rtp == 96.5
        assert "free_spins" in game.features
        
    def test_game_minimal_data(self):
        """Test game creation with minimal data."""
        data = {
            "id": "game456",
            "name": "Simple Game",
            "category": "table",
            "provider": "Simple Provider"
        }
        
        game = Game.from_dict(data)
        assert game.id == "game456"
        assert game.min_bet == Decimal("0.01")  # default value
        assert game.features == []  # default empty list


class TestSportEventModel:
    """Test cases for SportEvent model."""
    
    def test_sport_event_creation(self, sample_sport_event_data):
        """Test sport event creation from data."""
        event = SportEvent.from_dict(sample_sport_event_data)
        
        assert event.id == "event123"
        assert event.sport == "football"
        assert event.home_team == "Team A"
        assert event.away_team == "Team B"
        assert event.odds["home"] == 2.5
        assert event.live is False


class TestBetModel:
    """Test cases for Bet model."""
    
    def test_bet_creation(self):
        """Test bet creation from data."""
        data = {
            "id": "bet123",
            "user_id": "user123",
            "game_id": "game123",
            "bet_type": "win",
            "amount": "10.00",
            "potential_payout": "20.00",
            "odds": 2.0,
            "status": "pending",
            "placed_at": "2025-01-01T12:00:00Z"
        }
        
        bet = Bet.from_dict(data)
        assert bet.id == "bet123"
        assert bet.amount == Decimal("10.00")
        assert bet.potential_payout == Decimal("20.00")
        assert bet.status == "pending"


class TestStatisticsModel:
    """Test cases for Statistics model."""
    
    def test_statistics_creation(self):
        """Test statistics creation."""
        data = {
            "total_bets": 100,
            "total_wagered": "1000.00",
            "total_won": "950.00",
            "total_lost": "50.00",
            "win_rate": 85.5,
            "biggest_win": "500.00",
            "favorite_game": "Mega Slots"
        }
        
        stats = Statistics.from_dict(data)
        assert stats.total_bets == 100
        assert stats.total_wagered == Decimal("1000.00")
        assert stats.win_rate == 85.5
        assert stats.favorite_game == "Mega Slots"
        
    def test_statistics_defaults(self):
        """Test statistics with default values."""
        stats = Statistics()
        assert stats.total_bets == 0
        assert stats.total_wagered == Decimal("0")
        assert stats.win_rate == 0.0
        assert stats.favorite_game is None
