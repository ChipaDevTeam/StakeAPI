"""Main client for StakeAPI."""

import asyncio
from typing import Optional, Dict, Any, List
import aiohttp
import json
from urllib.parse import urljoin

from .exceptions import StakeAPIError, AuthenticationError, RateLimitError
from .models import User, Game, SportEvent, Bet
from .endpoints import Endpoints
from .auth import AuthManager


class StakeAPI:
    """Main client for interacting with stake.com API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://stake.com",
        timeout: int = 30,
        rate_limit: int = 10,
    ):
        """
        Initialize the StakeAPI client.
        
        Args:
            api_key: Your stake.com API key
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            rate_limit: Maximum requests per second
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limit = rate_limit
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_manager = AuthManager(api_key)
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def _create_session(self):
        """Create aiohttp session with proper headers."""
        headers = {
            "User-Agent": "StakeAPI/1.0.0",
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers.update(await self._auth_manager.get_auth_headers())
            
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout
        )
        
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
            
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[Any, Any]:
        """
        Make an authenticated request to the API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            StakeAPIError: For API errors
            AuthenticationError: For authentication errors
            RateLimitError: For rate limit errors
        """
        if not self._session:
            await self._create_session()
            
        url = urljoin(self.base_url, endpoint)
        
        try:
            async with self._session.request(
                method, url, params=params, json=data
            ) as response:
                response_data = await response.json()
                
                if response.status == 401:
                    raise AuthenticationError("Invalid API key or unauthorized access")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    raise StakeAPIError(f"API error: {response.status} - {response_data}")
                    
                return response_data
                
        except aiohttp.ClientError as e:
            raise StakeAPIError(f"Request failed: {e}")
            
    # Casino Methods
    async def get_casino_games(self, category: Optional[str] = None) -> List[Game]:
        """
        Get available casino games.
        
        Args:
            category: Filter by game category
            
        Returns:
            List of casino games
        """
        params = {}
        if category:
            params["category"] = category
            
        data = await self._request("GET", Endpoints.CASINO_GAMES, params=params)
        return [Game.from_dict(game) for game in data.get("games", [])]
        
    async def get_game_details(self, game_id: str) -> Game:
        """
        Get details for a specific game.
        
        Args:
            game_id: The game identifier
            
        Returns:
            Game details
        """
        endpoint = Endpoints.CASINO_GAME_DETAILS.format(game_id=game_id)
        data = await self._request("GET", endpoint)
        return Game.from_dict(data)
        
    # Sports Methods
    async def get_sports_events(self, sport: Optional[str] = None) -> List[SportEvent]:
        """
        Get available sports events.
        
        Args:
            sport: Filter by sport type
            
        Returns:
            List of sports events
        """
        params = {}
        if sport:
            params["sport"] = sport
            
        data = await self._request("GET", Endpoints.SPORTS_EVENTS, params=params)
        return [SportEvent.from_dict(event) for event in data.get("events", [])]
        
    # User Methods
    async def get_user_profile(self) -> User:
        """
        Get current user profile.
        
        Returns:
            User profile information
        """
        data = await self._request("GET", Endpoints.USER_PROFILE)
        return User.from_dict(data)
        
    async def get_user_balance(self) -> Dict[str, float]:
        """
        Get user account balance.
        
        Returns:
            Balance information by currency
        """
        data = await self._request("GET", Endpoints.USER_BALANCE)
        return data.get("balances", {})
        
    # Betting Methods
    async def place_bet(self, bet_data: Dict[str, Any]) -> Bet:
        """
        Place a bet.
        
        Args:
            bet_data: Bet information
            
        Returns:
            Bet confirmation
        """
        data = await self._request("POST", Endpoints.PLACE_BET, data=bet_data)
        return Bet.from_dict(data)
        
    async def get_bet_history(self, limit: int = 50) -> List[Bet]:
        """
        Get user bet history.
        
        Args:
            limit: Maximum number of bets to return
            
        Returns:
            List of bets
        """
        params = {"limit": limit}
        data = await self._request("GET", Endpoints.BET_HISTORY, params=params)
        return [Bet.from_dict(bet) for bet in data.get("bets", [])]
