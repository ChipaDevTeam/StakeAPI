"""Main client for StakeAPI."""

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

from .auth import AuthManager
from .endpoints import GraphQLQueries
from .exceptions import (
    AuthenticationError,
    GraphQLError,
    NetworkError,
    PermissionDeniedError,
    RateLimitError,
    StakeAPIError,
    ValidationError,
)
from .models import Bet, Game, SportEvent, User


def _parse_datetime(value: Optional[str]) -> Optional[datetime | str]:
    """Parse the RFC 1123 dates the API returns (e.g. 'Sat, 11 Jul 2026
    07:41:10 GMT')."""
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value  # let pydantic try ISO formats


def _bet_from_entry(entry: Dict[str, Any]) -> Optional[Bet]:
    """Map a house-bet entry (from houseBetList or allHouseBets) to a Bet model.

    Returns None for entries that cannot be mapped (e.g. hidden users or
    bet types missing required fields).
    """
    bet = entry.get("bet") or {}
    if not bet or bet.get("amount") is None:
        return None
    game = entry.get("game") or {}
    payout = float(bet.get("payout") or 0)
    active = bet.get("active", False)
    if active:
        status = "pending"
    else:
        status = "won" if payout > 0 else "lost"

    # CasinoBet.game is an enum string; the outer entry.game is an object
    inner_game = bet.get("game")
    game_id = inner_game if isinstance(inner_game, str) else game.get("slug")

    try:
        return Bet(
            id=str(entry.get("id") or bet.get("id", "")),
            user_id=str((bet.get("user") or {}).get("id") or ""),
            game_id=game_id,
            game_name=game.get("name"),
            bet_type=bet.get("__typename", "CasinoBet"),
            amount=Decimal(str(bet.get("amount") or 0)),
            currency=bet.get("currency"),
            potential_payout=Decimal(str(payout)),
            odds=bet.get("payoutMultiplier"),
            status=status,
            placed_at=_parse_datetime(bet.get("createdAt") or bet.get("updatedAt")),
            settled_at=(_parse_datetime(bet.get("updatedAt")) if not active else None),
        )
    except Exception:
        return None


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
            cf_clearance: Cloudflare clearance cookie (required to bypass
                Cloudflare protection)
            user_agent: Your browser's User-Agent (must match the one used to
                obtain cf_clearance)
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
        if not isinstance(base_url, str) or not base_url.startswith(
            ("http://", "https://")
        ):
            raise ValidationError(
                f"Invalid base_url: {base_url!r}. It must start with "
                "http:// or https://, e.g. 'https://stake.com' or a mirror "
                "like 'https://stake1017.com'."
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

    async def __aenter__(self) -> "StakeAPI":
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def _create_session(self) -> None:
        """Create aiohttp session with proper headers."""
        ua = self.user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        )
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

    async def close(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
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
        if self._session is None:
            await self._create_session()

        session = self._session
        if session is None:
            raise NetworkError("Client session could not be created")

        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            async with session.request(
                method, url, params=params, json=data, headers=headers
            ) as response:
                if response.status == 403:
                    raise StakeAPIError(
                        f"403 Forbidden — Cloudflare is blocking the request to "
                        f"{self.base_url}. Make sure you provide a valid "
                        "'cf_clearance' cookie obtained from the SAME domain "
                        f"({self.base_url}). To get it: open {self.base_url} in "
                        "your browser → DevTools (F12) → Application tab → "
                        "Cookies → copy the 'cf_clearance' value. Then pass it "
                        "as: StakeAPI(access_token=..., cf_clearance='...')"
                    )
                elif response.status == 401:
                    raise AuthenticationError(
                        "Invalid access token or unauthorized access"
                    )
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
                        f"Expected JSON but got a non-JSON response "
                        f"(status {response.status}) from {url}. This usually "
                        "means a Cloudflare challenge page or a redirect to a "
                        f"login page. Response starts with: {body_preview!r}"
                    )

                if response.status >= 400:
                    raise StakeAPIError(
                        f"API error: {response.status} - {response_data}"
                    )

                return response_data  # type: ignore

        except StakeAPIError:
            raise
        except asyncio.TimeoutError:
            raise NetworkError(
                f"Request to {url} timed out after {self.timeout}s. Check "
                "your connection, or the domain may be blocked/unreachable "
                "from your network — try another mirror via base_url."
            )
        except aiohttp.ClientConnectorError as e:
            raise NetworkError(
                f"Could not connect to {self.base_url}: {e}. The domain may "
                "be blocked in your region or does not exist — you can pass "
                "a different mirror, e.g. "
                "StakeAPI(base_url='https://stake1017.com')."
            )
        except aiohttp.ClientError as e:
            raise NetworkError(f"Request failed: {e}")

    async def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        payload: Dict[str, Any] = {
            "query": query,
        }

        if variables:
            payload["variables"] = variables

        if operation_name:
            payload["operationName"] = operation_name

        # The site's own client sends these on every GraphQL call
        extra_headers: Optional[Dict[str, str]] = None
        if operation_name:
            extra_headers = {
                "X-Operation-Name": operation_name,
                "X-Operation-Type": (
                    "mutation" if query.lstrip().startswith("mutation") else "query"
                ),
            }

        response = await self._request(
            "POST", "/_api/graphql", data=payload, headers=extra_headers
        )

        if not isinstance(response, dict):
            raise GraphQLError(
                "Unexpected GraphQL response type: "
                f"{type(response).__name__} - {response!r}"
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

            permission_markers = (
                "not allowed",
                "unauthorized",
                "permission",
                "forbidden",
            )
            if any(
                marker in msg.lower()
                for msg in error_messages + error_types
                for marker in permission_markers
            ):
                raise PermissionDeniedError(
                    f"GraphQL permission error: {joined}. This usually means: "
                    "1) your access token is invalid or expired — get a fresh "
                    f"one from {self.base_url} (DevTools → any GraphQL request "
                    "→ 'x-access-token' header); 2) your session/cf_clearance "
                    "cookies were obtained from a different domain than "
                    f"base_url ({self.base_url}) — token and cookies must all "
                    "come from the same mirror; or 3) your account lacks "
                    "permission for this operation.",
                    errors=errors,
                )

            raise GraphQLError(f"GraphQL errors: {joined}", errors=errors)

        data = response.get("data")
        if data is None:
            raise GraphQLError(
                "GraphQL response contained no data and no errors — "
                f"raw response: {response!r}"
            )

        return data  # type: ignore

    # Casino Methods
    async def get_casino_games(self, category: Optional[str] = None) -> List[Game]:
        """
        Get available casino games.

        Raises:
            StakeAPIError: Always — stake has no REST API and the GraphQL
                query for game lists has not been mapped yet.
        """
        raise StakeAPIError(
            "get_casino_games is not supported yet: stake.com has no REST API "
            "and the GraphQL query for game lists has not been mapped. "
            "Working methods: get_user_balance, get_user_profile, "
            "get_bet_history, get_all_house_bets, get_currency_rates."
        )

    async def get_game_details(self, game_id: str) -> Game:
        """
        Get details for a specific game.

        Raises:
            StakeAPIError: Always — see get_casino_games.
        """
        raise StakeAPIError(
            "get_game_details is not supported yet: stake.com has no REST API "
            "and the GraphQL query for game details has not been mapped. "
            "Working methods: get_user_balance, get_user_profile, "
            "get_bet_history, get_all_house_bets, get_currency_rates."
        )

    # Sports Methods
    async def get_sports_events(self, sport: Optional[str] = None) -> List[SportEvent]:
        """
        Get available sports events.

        Raises:
            StakeAPIError: Always — see get_casino_games.
        """
        raise StakeAPIError(
            "get_sports_events is not supported yet: stake.com has no REST API "
            "and the GraphQL query for sports events has not been mapped. "
            "Working methods: get_user_balance, get_user_profile, "
            "get_bet_history, get_all_house_bets, get_currency_rates."
        )

    # User Methods
    async def get_user_profile(self) -> User:
        """
        Get current user profile using GraphQL.

        Returns:
            User profile information
        """
        data = await self._graphql_request(
            GraphQLQueries.USER_PROFILE, operation_name="UserProfile"
        )
        user = data.get("user")
        if not user:
            raise StakeAPIError(
                f"No user data in profile response: {data!r}. "
                "Your session may have expired — refresh your cookies."
            )
        return User(
            id=user["id"],
            username=user.get("name", ""),
            email=user.get("email"),
            verified=bool(user.get("hasEmailVerified")),
            created_at=_parse_datetime(user.get("createdAt")),
        )

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
        result: Dict[str, Dict[str, float]] = {"available": {}, "vault": {}}

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

        Raises:
            StakeAPIError: Always — stake has no REST API and the GraphQL
                mutations for placing bets have not been mapped.
        """
        raise StakeAPIError(
            "place_bet is not supported yet: stake.com has no REST API and "
            "the GraphQL mutations for placing bets have not been mapped. "
            "Working methods: get_user_balance, get_user_profile, "
            "get_bet_history, get_all_house_bets, get_currency_rates."
        )

    async def get_bet_history(self, limit: int = 50, offset: int = 0) -> List[Bet]:
        """
        Get user casino bet history using GraphQL.

        Args:
            limit: Maximum number of bets to return
            offset: Number of bets to skip (for pagination)

        Returns:
            List of bets, newest first
        """
        data = await self._graphql_request(
            GraphQLQueries.BET_HISTORY,
            variables={"limit": limit, "offset": offset},
            operation_name="BetHistory",
        )
        entries = (data.get("user") or {}).get("houseBetList") or []
        return [b for b in (_bet_from_entry(e) for e in entries) if b]

    async def get_all_house_bets(self, limit: int = 10) -> List[Bet]:
        """
        Get the public realtime feed of recent house bets across all players.

        This is the same data shown in the site's live bets board. Bets by
        users who hide their bets have an empty user_id.

        Args:
            limit: Maximum number of bets to return

        Returns:
            List of recent bets across all bet types
        """
        data = await self._graphql_request(
            GraphQLQueries.ALL_HOUSE_BETS,
            variables={"limit": limit},
            operation_name="AllHouseBets",
        )
        entries = data.get("allHouseBets") or []
        return [b for b in (_bet_from_entry(e) for e in entries) if b]

    # Currency Methods
    async def get_currency_rates(self) -> Dict[str, Any]:
        """
        Get currency configuration: exchange rates and fiat currency lists.

        Returns:
            Dictionary with:
                base_rates: {currency: rate_in_usd}, e.g. {"btc": 64226.07, ...}
                launched_fiat: fiat currencies available on the site
                display_fiat: fiat currencies available for display
        """
        data = await self._graphql_request(
            GraphQLQueries.CURRENCY_CONFIGURATION,
            variables={"isAcp": False},
            operation_name="CurrencyConfiguration",
        )
        config = data.get("currencyConfiguration") or {}
        rates = {
            r["currency"]: r["baseRate"]
            for r in config.get("baseRates") or []
            if r.get("currency") is not None
        }
        return {
            "base_rates": rates,
            "launched_fiat": config.get("launchedFiatCurrencies") or [],
            "display_fiat": config.get("displayFiatCurrencies") or [],
        }
