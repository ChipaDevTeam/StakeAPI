"""Tests for StakeAPI client."""

import pytest
from unittest.mock import AsyncMock, patch
from stakeapi import StakeAPI
from stakeapi.exceptions import AuthenticationError, RateLimitError
from stakeapi.models import User, Game, SportEvent


class TestStakeAPI:
    """Test cases for StakeAPI client."""
    
    def test_init(self, api_key):
        """Test client initialization."""
        client = StakeAPI(api_key=api_key)
        assert client.api_key == api_key
        assert client.base_url == "https://stake.com"
        assert client.timeout == 30
        assert client.rate_limit == 10
        
    def test_init_with_custom_params(self):
        """Test client initialization with custom parameters."""
        client = StakeAPI(
            api_key="test",
            base_url="https://custom.com",
            timeout=60,
            rate_limit=5
        )
        assert client.base_url == "https://custom.com"
        assert client.timeout == 60
        assert client.rate_limit == 5
        
    @pytest.mark.asyncio
    async def test_context_manager(self, api_key):
        """Test client as async context manager."""
        async with StakeAPI(api_key=api_key) as client:
            assert client._session is not None
            
    @pytest.mark.asyncio
    async def test_authentication_error(self, stake_client):
        """Test authentication error handling."""
        with patch.object(stake_client, '_request') as mock_request:
            mock_request.side_effect = AuthenticationError("Invalid API key")
            
            with pytest.raises(AuthenticationError):
                await stake_client.get_user_profile()
                
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, stake_client):
        """Test rate limit error handling."""
        with patch.object(stake_client, '_request') as mock_request:
            mock_request.side_effect = RateLimitError("Rate limit exceeded")
            
            with pytest.raises(RateLimitError):
                await stake_client.get_casino_games()
                
    @pytest.mark.asyncio
    async def test_get_casino_games(self, stake_client, sample_game_data):
        """Test getting casino games."""
        mock_response = {"games": [sample_game_data]}
        
        with patch.object(stake_client, '_request', return_value=mock_response):
            games = await stake_client.get_casino_games()
            
            assert len(games) == 1
            assert isinstance(games[0], Game)
            assert games[0].name == "Test Slot"
            
    @pytest.mark.asyncio
    async def test_get_casino_games_with_category(self, stake_client, sample_game_data):
        """Test getting casino games with category filter."""
        mock_response = {"games": [sample_game_data]}
        
        with patch.object(stake_client, '_request', return_value=mock_response) as mock_request:
            await stake_client.get_casino_games(category="slots")
            
            # Verify the request was made with correct parameters
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            assert kwargs['params'] == {"category": "slots"}
            
    @pytest.mark.asyncio
    async def test_get_user_profile(self, stake_client, sample_user_data):
        """Test getting user profile."""
        with patch.object(stake_client, '_request', return_value=sample_user_data):
            user = await stake_client.get_user_profile()
            
            assert isinstance(user, User)
            assert user.username == "testuser"
            assert user.verified is True
            
    @pytest.mark.asyncio
    async def test_get_user_balance(self, stake_client):
        """Test getting user balance."""
        mock_response = {"balances": {"USD": 100.50, "BTC": 0.001}}
        
        with patch.object(stake_client, '_request', return_value=mock_response):
            balance = await stake_client.get_user_balance()
            
            assert balance == {"USD": 100.50, "BTC": 0.001}
            
    @pytest.mark.asyncio
    async def test_get_sports_events(self, stake_client, sample_sport_event_data):
        """Test getting sports events."""
        mock_response = {"events": [sample_sport_event_data]}
        
        with patch.object(stake_client, '_request', return_value=mock_response):
            events = await stake_client.get_sports_events()
            
            assert len(events) == 1
            assert isinstance(events[0], SportEvent)
            assert events[0].home_team == "Team A"
