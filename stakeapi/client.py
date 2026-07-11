"""Main client for StakeAPI."""

import asyncio
from typing import Optional, Dict, Any, List
import aiohttp
import json
from urllib.parse import urljoin

from .exceptions import (
    StakeAPIError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    GraphQLError,
    PermissionDeniedError,
    ValidationError,
)
from .models import User, Game, SportEvent, Bet
from .endpoints import Endpoints, GraphQLQueries
from .auth import AuthManager


def _parse_datetime(value):
    """Parse the RFC 1123 dates the API returns (e.g. 'Sat, 11 Jul 2026 07:41:10 GMT')."""
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value  # let pydantic try ISO formats


class StakeAPI:
    """Main client for interacting with stake.com API."""
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        session_cookie: Optional[str] = None,
        cf_clearance: Optional[str] = None,
        user_agent: Optional[str] = None,
        base_url: str = "https://stake.com",
        timeout: int = 30,
        rate_limit: int = 10,
        cookie_file: Optional[str] = None,
        cookie_string: Optional[str] = None,
    ):
        """
        Initialize the StakeAPI client.

        Args:
            access_token: Your stake.com access token (x-access-token header).
                If omitted but cookies are provided, the 'session' cookie value
                is used as the access token (they are the same value on stake).
            session_cookie: Session cookie for authentication
            cf_clearance: Cloudflare clearance cookie (required to bypass Cloudflare protection)
            user_agent: Your browser's User-Agent (must match the one used to obtain cf_clearance)
            base_url: Base URL for the API. Use this to point at a regional
                mirror, e.g. "https://stake1017.com" or "https://stake.bet".
                Your cookies (session, cf_clearance) must come from the SAME
                domain you set here.
            timeout: Request timeout in seconds
            rate_limit: Maximum requests per second
            cookie_file: Path to a file (e.g. "cookie.txt") containing the
                entire Cookie header copied from your browser (DevTools →
                Network tab → any request → 'cookie' header). All cookies are
                sent as-is, and session/cf_clearance/access token are extracted
                automatically. Takes precedence over cookie_string.
            cookie_string: The same raw cookie string, passed directly instead
                of via a file.

        Raises:
            ValidationError: If base_url is not a valid http(s) URL, or the
                cookie file is missing/empty/unreadable.
        """
        if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://")):
            raise ValidationError(
                f"Invalid base_url: {base_url!r}. It must start with http:// or https://, "
                "e.g. 'https://stake.com' or a mirror like 'https://stake1017.com'."
            )

        # Load cookies from file/string if provided
        self._cookie_header: Optional[str] = None
        if cookie_file:
            try:
                self._cookie_header = AuthManager.load_cookie_file(cookie_file)
            except OSError as e:
                raise ValidationError(
                    f"Could not read cookie file {cookie_file!r}: {e}. "
                    "Create it by copying the entire 'cookie' request header from "
                    "your browser (DevTools → Network tab → any request → Headers)."
                )
            except ValueError as e:
                raise ValidationError(str(e))
        elif cookie_string:
            self._cookie_header = " ".join(cookie_string.split())

        if self._cookie_header:
            parsed = AuthManager.parse_cookie_string(self._cookie_header)
            if not parsed:
                raise ValidationError(
                    "No cookies could be parsed from the provided cookie data. "
                    "Expected format: 'name1=value1; name2=value2; ...'"
                )
            session_cookie = session_cookie or parsed.get("session")
            cf_clearance = cf_clearance or parsed.get("cf_clearance")
            # On stake, the x-access-token header carries the same value
            # as the 'session' cookie
            access_token = access_token or parsed.get("session")

        self.access_token = access_token
        self.session_cookie = session_cookie
        self.cf_clearance = cf_clearance
        self.user_agent = user_agent
        self.base_url = base_url.rstrip("/")
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
        ua = self.user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        headers = {
            "User-Agent": ua,
            "Accept": "application/graphql+json, application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Language": "en",
        }
        
        if self.access_token:
            headers["X-Access-Token"] = self.access_token

        # Set up cookies. When a full cookie string was provided (cookie_file /
        # cookie_string), send it verbatim as the Cookie header — the cookie
        # jar would mangle values containing commas or quotes (e.g. session_info).
        cookies = None
        if self._cookie_header:
            headers["Cookie"] = self._cookie_header
        else:
            cookies = {}
            if self.session_cookie:
                cookies["session"] = self.session_cookie
            if self.cf_clearance:
                cookies["cf_clearance"] = self.cf_clearance

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            cookies=cookies or None,
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
            NetworkError: For connection failures, timeouts, and non-JSON responses
        """
        if not self._session:
            await self._create_session()

        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            async with self._session.request(
                method, url, params=params, json=data
            ) as response:
                if response.status == 403:
                    raise StakeAPIError(
                        f"403 Forbidden — Cloudflare is blocking the request to {self.base_url}. "
                        "Make sure you provide a valid 'cf_clearance' cookie obtained from "
                        f"the SAME domain ({self.base_url}). "
                        f"To get it: open {self.base_url} in your browser → DevTools (F12) → "
                        "Application tab → Cookies → copy the 'cf_clearance' value. "
                        "Then pass it as: StakeAPI(access_token=..., cf_clearance='...')"
                    )
                elif response.status == 401:
                    raise AuthenticationError("Invalid access token or unauthorized access")
                elif response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    message = "Rate limit exceeded"
                    if retry_after:
                        message += f" — retry after {retry_after} seconds"
                    raise RateLimitError(message)
                elif response.status >= 500:
                    raise StakeAPIError(
                        f"Server error {response.status} from {self.base_url}. "
                        "The site may be down or the mirror may be unavailable — "
                        "try again later or switch base_url to another mirror."
                    )

                try:
                    response_data = await response.json(content_type=None)
                except (json.JSONDecodeError, aiohttp.ContentTypeError, ValueError):
                    body_preview = (await response.text())[:200]
                    raise NetworkError(
                        f"Expected JSON but got a non-JSON response (status {response.status}) "
                        f"from {url}. This usually means a Cloudflare challenge page or a "
                        f"redirect to a login page. Response starts with: {body_preview!r}"
                    )

                if response.status >= 400:
                    raise StakeAPIError(f"API error: {response.status} - {response_data}")

                return response_data

        except StakeAPIError:
            raise
        except asyncio.TimeoutError:
            raise NetworkError(
                f"Request to {url} timed out after {self.timeout}s. "
                "Check your connection, or the domain may be blocked/unreachable "
                "from your network — try another mirror via base_url."
            )
        except aiohttp.ClientConnectorError as e:
            raise NetworkError(
                f"Could not connect to {self.base_url}: {e}. "
                "The domain may be blocked in your region or does not exist — "
                "you can pass a different mirror, e.g. StakeAPI(base_url='https://stake1017.com')."
            )
        except aiohttp.ClientError as e:
            raise NetworkError(f"Request failed: {e}")
    
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
            GraphQLError: When the API returns GraphQL-level errors
            PermissionDeniedError: When the API rejects the request as unauthorized
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

        if not isinstance(response, dict):
            raise GraphQLError(
                f"Unexpected GraphQL response type: {type(response).__name__} - {response!r}"
            )

        # Check for GraphQL errors
        errors = response.get("errors")
        if errors:
            error_messages = [error.get("message", "Unknown error") for error in errors]
            error_types = [
                error.get("errorType") or error.get("extensions", {}).get("code", "")
                for error in errors
            ]
            joined = ", ".join(error_messages)

            permission_markers = ("not allowed", "unauthorized", "permission", "forbidden")
            if any(
                marker in msg.lower()
                for msg in error_messages + error_types
                for marker in permission_markers
            ):
                raise PermissionDeniedError(
                    f"GraphQL permission error: {joined}. This usually means: "
                    "1) your access token is invalid or expired — get a fresh one from "
                    f"{self.base_url} (DevTools → any GraphQL request → 'x-access-token' header); "
                    "2) your session/cf_clearance cookies were obtained from a different domain "
                    f"than base_url ({self.base_url}) — token and cookies must all come from the "
                    "same mirror; or 3) your account lacks permission for this operation.",
                    errors=errors,
                )

            raise GraphQLError(f"GraphQL errors: {joined}", errors=errors)

        data = response.get("data")
        if data is None:
            raise GraphQLError(
                "GraphQL response contained no data and no errors — "
                f"raw response: {response!r}"
            )

        return data
            
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
            for entry in data["user"]["balances"]:
                if "available" in entry:
                    currency = entry["available"].get("currency", "").lower()
                    amount = float(entry["available"].get("amount", 0))
                    result["available"][currency] = amount
                if "vault" in entry:
                    currency = entry["vault"].get("currency", "").lower()
                    amount = float(entry["vault"].get("amount", 0))
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
