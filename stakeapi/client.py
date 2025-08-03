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
        access_token: Optional[str] = None,
        session_cookie: Optional[str] = None,
        base_url: str = "https://stake.com",
        timeout: int = 30,
        rate_limit: int = 10,
    ):
        """
        Initialize the StakeAPI client.
        
        Args:
            access_token: Your stake.com access token (x-access-token header)
            session_cookie: Session cookie for authentication
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            rate_limit: Maximum requests per second
        """
        self.access_token = access_token
        self.session_cookie = session_cookie
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limit = rate_limit
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_manager = AuthManager(access_token)
        
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "application/graphql+json, application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://stake.com",
            "Referer": "https://stake.com/",
            "Sec-Ch-Ua": '"Chromium";v="135", "Not-A.Brand";v="8"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Language": "en",
        }
        
        if self.access_token:
            headers["X-Access-Token"] = self.access_token
            
        # Set up cookies if session cookie is provided
        jar = None
        if self.session_cookie:
            jar = aiohttp.CookieJar()
            jar.update_cookies({"session": self.session_cookie})
            
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            cookie_jar=jar
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
                    raise AuthenticationError("Invalid access token or unauthorized access")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    raise StakeAPIError(f"API error: {response.status} - {response_data}")
                    
                return response_data
                
        except aiohttp.ClientError as e:
            raise StakeAPIError(f"Request failed: {e}")
    
    async def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> Dict[Any, Any]:
        """
        Make a GraphQL request to the stake.com API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            operation_name: Operation name
            
        Returns:
            GraphQL response data
            
        Raises:
            StakeAPIError: For API errors
            AuthenticationError: For authentication errors
        """
        payload = {
            "query": query,
        }
        
        if variables:
            payload["variables"] = variables
            
        if operation_name:
            payload["operationName"] = operation_name
            
        response = await self._request("POST", "/_api/graphql", data=payload)
        
        # Check for GraphQL errors
        if "errors" in response:
            error_messages = [error.get("message", "Unknown error") for error in response["errors"]]
            raise StakeAPIError(f"GraphQL errors: {', '.join(error_messages)}")
            
        return response.get("data", {})
            
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
        
    async def get_user_balance(self) -> Dict[str, Dict[str, float]]:
        """
        Get user account balance using GraphQL.
        
        Returns:
            Balance information by currency with available and vault amounts
            Format: {
                "available": {"btc": 0.001, "usd": 100.0},
                "vault": {"btc": 0.0, "usd": 0.0}
            }
        """
        query = """
        query UserBalances {
          user {
            id
            balances {
              available {
                amount
                currency
                __typename
              }
              vault {
                amount
                currency
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """
        
        data = await self._graphql_request(query, operation_name="UserBalances")
        
        # Process the response to create a more convenient format
        result = {
            "available": {},
            "vault": {}
        }
        
        if "user" in data and data["user"] and "balances" in data["user"]:
            balances = data["user"]["balances"]
            
            # Process available balances
            if "available" in balances:
                for balance in balances["available"]:
                    currency = balance.get("currency", "").lower()
                    amount = float(balance.get("amount", 0))
                    result["available"][currency] = amount
            
            # Process vault balances
            if "vault" in balances:
                for balance in balances["vault"]:
                    currency = balance.get("currency", "").lower()
                    amount = float(balance.get("amount", 0))
                    result["vault"][currency] = amount
        
        return result
        
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
