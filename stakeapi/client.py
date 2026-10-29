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
from .websocket import StakeWebSocket


def _parse_datetime(value):
    """Parse the RFC 1123 dates the API returns (e.g. 'Sat, 11 Jul 2026 07:41:10 GMT')."""
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
            amount=str(bet.get("amount") or 0),
            currency=bet.get("currency"),
            potential_payout=str(payout),
            odds=bet.get("payoutMultiplier"),
            status=status,
            placed_at=_parse_datetime(bet.get("createdAt") or bet.get("updatedAt")),
            settled_at=_parse_datetime(bet.get("updatedAt")) if not active else None,
        )
    except Exception:
        return None


def _event_from_fixture(
    fixture: Dict[str, Any], sport: Dict[str, Any], tournament: Dict[str, Any]
) -> Optional[SportEvent]:
    """Map a SportIndex fixture to a SportEvent model (None if unmappable)."""
    data = fixture.get("data") or {}
    teams = {t.get("qualifier"): t.get("name") for t in data.get("teams") or []}
    start = _parse_datetime(data.get("startTime"))
    if not start:
        return None

    odds: Dict[str, float] = {}
    for group in fixture.get("groups") or []:
        for template in group.get("templates") or []:
            for market in template.get("markets") or []:
                for outcome in market.get("outcomes") or []:
                    if outcome.get("active") and outcome.get("odds") is not None:
                        odds[outcome.get("name", "")] = float(outcome["odds"])

    status = fixture.get("status") or ""
    try:
        return SportEvent(
            id=str(fixture.get("id")),
            sport=sport.get("name", ""),
            league=tournament.get("name", ""),
            home_team=teams.get("home") or fixture.get("name", ""),
            away_team=teams.get("away") or "",
            start_time=start,
            status=status,
            odds=odds,
            live=status == "live",
        )
    except Exception:
        return None


def _game_from_kurator(game: Dict[str, Any]) -> Optional[Game]:
    """Map a GameKuratorGame (lobby, search or detail query) to a Game model."""
    if not game.get("id"):
        return None
    groups = [g.get("group") or {} for g in game.get("groupGames") or []]
    categories = [g.get("translation") for g in groups if g.get("type") == "category"]
    provider = (game.get("providerGroup") or {}).get("name") or next(
        (g.get("translation") for g in groups if g.get("type") == "provider"), ""
    )
    edge = game.get("edge")
    try:
        return Game(
            id=game["id"],
            name=game.get("name", ""),
            slug=game.get("slug"),
            category=categories[0] if categories else (game.get("type") or ""),
            provider=provider or "",
            description=game.get("description"),
            rtp=round((1 - edge) * 100, 4) if edge is not None else None,
            features=[g.get("translation") for g in groups if g.get("translation")],
            thumbnail_url=game.get("thumbnailUrl"),
            player_count=game.get("playerCount"),
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
        
    def _session_headers(self):
        """Build the default headers and cookies sent with every request."""
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
        cookies = {}
        if self._cookie_header:
            headers["Cookie"] = self._cookie_header
        else:
            if self.session_cookie:
                cookies["session"] = self.session_cookie
            if self.cf_clearance:
                cookies["cf_clearance"] = self.cf_clearance
        return headers, cookies

    async def _create_session(self):
        """Create aiohttp session with proper headers."""
        headers, cookies = self._session_headers()
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            cookies=cookies or None,
        )

    def websocket(self, language: str = "en") -> StakeWebSocket:
        """
        Create a WebSocket client for live data (crash, bet feeds, odds, chat).

        It reuses this client's base_url, cookies and access token. Use it as
        an async context manager:

            async with client.websocket() as ws:
                async for bet in ws.highroller_bets():
                    print(bet)
        """
        return StakeWebSocket(self, language=language)
        
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
            
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
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
                method, url, params=params, json=data, headers=headers
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

        # The site's own client sends these on every GraphQL call
        extra_headers = None
        if operation_name:
            extra_headers = {
                "X-Operation-Name": operation_name,
                "X-Operation-Type": "mutation" if query.lstrip().startswith("mutation") else "query",
            }

        response = await self._request(
            "POST", "/_api/graphql", data=payload, headers=extra_headers
        )

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

            permission_markers = (
                "not allowed", "unauthorized", "permission", "forbidden",
                "notauthenticated", "please log in",
            )
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
    async def get_casino_games(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "popular7d",
    ) -> List[Game]:
        """
        Get casino games in a lobby group.

        Args:
            category: Group slug as used in site URLs (/casino/group/<slug>),
                e.g. "slots", "stake-originals", "live-casino". Defaults to "slots".
            limit: Maximum number of games to return
            offset: Number of games to skip (for pagination)
            sort: GameKuratorGroupGameSortEnum value, e.g. "popular7d"
        """
        data = await self._graphql_request(
            GraphQLQueries.CASINO_GROUP,
            variables={
                "slug": category or "slots",
                "limit": limit,
                "offset": offset,
                "sort": sort,
            },
            operation_name="SlugKuratorGroup",
        )
        group = data.get("slugKuratorGroup")
        if not group:
            raise StakeAPIError(f"Unknown casino group {category!r}")
        games = (_game_from_kurator(g.get("game") or {}) for g in group.get("groupGamesList") or [])
        return [g for g in games if g]

    async def get_game_details(self, game_id: str) -> Game:
        """
        Get details for a specific game.

        Args:
            game_id: Game slug as used in site URLs (/casino/games/<slug>),
                e.g. "stake-dice"
        """
        data = await self._graphql_request(
            GraphQLQueries.CASINO_GAME,
            variables={"slug": game_id},
            operation_name="SlugKuratorGame",
        )
        game = _game_from_kurator(data.get("slugKuratorGame") or {})
        if not game:
            raise StakeAPIError(f"Unknown game {game_id!r}")
        return game

    async def search_casino_games(self, query: str, limit: int = 20, offset: int = 0) -> List[Game]:
        """Search casino games by name."""
        data = await self._graphql_request(
            GraphQLQueries.SEARCH_CASINO,
            variables={"query": query, "limit": limit, "offset": offset},
            operation_name="searchQueryCasino",
        )
        games = (_game_from_kurator(g) for g in data.get("kuratorGameQuery") or [])
        return [g for g in games if g]

    async def get_casino_collection(
        self, collection_type: str = "provider", sort: str = "popular", filter: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Get a casino lobby collection, e.g. the list of game providers.

        Args:
            collection_type: GameKuratorCollectionEnum value, e.g. "provider"
            sort: GameKuratorCollectionSortEnum value, e.g. "popular"
            filter: GameKuratorCollectionFilterEnum value, e.g. "all"

        Returns:
            Groups with id, slug, translation, gameCount and playerCount.
        """
        data = await self._graphql_request(
            GraphQLQueries.CASINO_COLLECTION,
            variables={"type": collection_type, "sort": sort, "filter": filter},
            operation_name="KuratorCollection",
        )
        return [c["group"] for c in data.get("kuratorCollection") or [] if c.get("group")]

    async def get_game_payouts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get payout tables for Keno, Plinko and Wheel.

        Returns:
            {"keno": [...], "plinko": [...], "wheel": [...]}, each entry with
            "payouts" and "risk" (plus "rows" for Plinko and Wheel).
        """
        data = await self._graphql_request(
            GraphQLQueries.GAME_PAYOUTS, operation_name="GamePayouts"
        )
        info = data.get("info") or {}
        return {
            "keno": info.get("kenoPayouts") or [],
            "plinko": info.get("plinkoPayouts") or [],
            "wheel": info.get("wheelPayouts") or [],
        }

    async def get_crash_history(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent Crash rounds (id, startTime, crashpoint, hash)."""
        data = await self._graphql_request(
            GraphQLQueries.CRASH_HISTORY,
            variables={"limit": limit, "offset": offset},
            operation_name="CrashGameListHistory",
        )
        return data.get("crashGameList") or []

    async def get_crash_game(self, game_id: str) -> Dict[str, Any]:
        """Get one Crash round with its seed, hash and bet leaderboard."""
        data = await self._graphql_request(
            GraphQLQueries.CRASH_GAME,
            variables={"gameId": game_id},
            operation_name="CrashGameLookup",
        )
        game = data.get("crashGame")
        if not game:
            raise StakeAPIError(f"Unknown crash game {game_id!r}")
        return game

    async def get_slide_history(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent Slide rounds (id, multiplier, startTime, hash)."""
        data = await self._graphql_request(
            GraphQLQueries.SLIDE_HISTORY,
            variables={"limit": limit, "offset": offset},
            operation_name="SlideGameListHistory",
        )
        return data.get("slideGameList") or []

    # Sports Methods
    async def get_sport_index(
        self,
        sport: str = "soccer",
        group: str = "winner",
        search_type: str = "popular",
        market_limit: int = 1,
    ) -> Dict[str, Any]:
        """
        Get a sport's landing page: featured fixtures with odds, tournaments
        and categories (the site's own SportIndex query).

        Args:
            sport: Sport slug, e.g. "soccer", "basketball", "tennis"
            group: Market group to include odds for, e.g. "winner"
            search_type: SportSearchEnum value, e.g. "popular", "live", "upcoming"
            market_limit: Maximum markets returned per template

        Returns:
            The raw ``slugSport`` object (id, name, templates, firstTournament,
            tournamentList, categoryList).
        """
        data = await self._graphql_request(
            GraphQLQueries.SPORT_INDEX,
            variables={
                "sport": sport,
                "group": group,
                "type": search_type,
                "marketLimit": market_limit,
            },
            operation_name="SportIndex",
        )
        sport_data = data.get("slugSport")
        if not sport_data:
            raise StakeAPIError(f"Unknown sport {sport!r}: {data!r}")
        return sport_data

    async def get_sports_events(self, sport: Optional[str] = None) -> List[SportEvent]:
        """
        Get popular fixtures for a sport (defaults to soccer) with winner odds.

        Args:
            sport: Sport slug, e.g. "soccer", "basketball"
        """
        sport_data = await self.get_sport_index(sport or "soccer")
        events: List[SportEvent] = []
        for tournament in sport_data.get("firstTournament") or []:
            for fixture in tournament.get("fixtureList") or []:
                event = _event_from_fixture(fixture, sport_data, tournament)
                if event:
                    events.append(event)
        return events

    async def get_sports(
        self, search_type: str = "upcoming", sport_type: str = "sport", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List sports with their fixture counts.

        Args:
            search_type: SportSearchEnum value: "upcoming", "live" or "active"
            sport_type: "sport" or "esport"
            limit: Maximum number of sports to return
        """
        data = await self._graphql_request(
            GraphQLQueries.SPORT_LIST,
            variables={"type": search_type, "sportType": sport_type, "limit": limit},
            operation_name="SportListMenu",
        )
        return data.get("sportList") or []

    async def get_trending_sports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List the most popular sports (id, name, slug, sportType)."""
        data = await self._graphql_request(
            GraphQLQueries.TRENDING_SPORTS,
            variables={"limit": limit},
            operation_name="TrendingSportsQ",
        )
        return data.get("topSportList") or []

    async def get_fixtures(
        self,
        search_type: str = "upcoming",
        sport_type: str = "sport",
        group: str = "winner",
        limit: int = 20,
        offset: int = 0,
        market_limit: int = 1,
    ) -> Dict[str, Any]:
        """
        List fixtures across all sports with odds for one market group.

        Args:
            search_type: SportSearchEnum value: "upcoming", "live" or "active"
            sport_type: "sport" or "esport"
            group: Market group to include odds for, e.g. "winner" or "main"
            limit: Maximum number of fixtures to return
            offset: Number of fixtures to skip (for pagination)
            market_limit: Maximum markets returned per template

        Returns:
            {"count": total matching fixtures, "fixtures": [...]}
        """
        data = await self._graphql_request(
            GraphQLQueries.FIXTURE_LIST,
            variables={
                "type": search_type,
                "sportType": sport_type,
                "groups": group,
                "limit": limit,
                "offset": offset,
                "marketLimit": market_limit,
            },
            operation_name="FixtureList",
        )
        return {
            "count": data.get("fixtureCount", 0),
            "fixtures": data.get("fixtureList") or [],
        }

    async def get_sport_fixtures(
        self,
        sport: str,
        search_type: str = "upcoming",
        group: str = "winner",
        tournament_limit: int = 25,
        tournament_offset: int = 0,
        fixture_limit: int = 20,
        market_limit: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        List a sport's tournaments, each with its fixtures and odds.

        Args:
            sport: Sport slug, e.g. "soccer"
            search_type: SportSearchEnum value: "upcoming", "live" or "active"
            group: Market group to include odds for, e.g. "winner"
        """
        data = await self._graphql_request(
            GraphQLQueries.SPORT_TOURNAMENT_FIXTURES,
            variables={
                "sport": sport,
                "type": search_type,
                "groups": group,
                "tournamentLimit": tournament_limit,
                "tournamentOffset": tournament_offset,
                "fixtureLimit": fixture_limit,
                "marketLimit": market_limit,
            },
            operation_name="SportTournamentFixtureList",
        )
        sport_data = data.get("slugSport")
        if not sport_data:
            raise StakeAPIError(f"Unknown sport {sport!r}")
        return sport_data.get("tournamentList") or []

    async def get_tournament(
        self,
        sport: str,
        category: str,
        tournament: str,
        search_type: str = "upcoming",
        groups: Optional[List[str]] = None,
        limit: int = 10,
        offset: int = 0,
        market_limit: int = 1,
    ) -> Dict[str, Any]:
        """
        Get one tournament and its fixtures, by the slugs in its site URL
        (/sports/<sport>/<category>/<tournament>).

        Example:
            await client.get_tournament("soccer", "england", "premier-league")
        """
        data = await self._graphql_request(
            GraphQLQueries.SLUG_TOURNAMENT,
            variables={
                "sport": sport,
                "category": category,
                "tournament": tournament,
                "type": search_type,
                "groups": groups or ["winner"],
                "limit": limit,
                "offset": offset,
                "marketLimit": market_limit,
            },
            operation_name="SlugTournament",
        )
        result = data.get("slugTournament")
        if not result:
            raise StakeAPIError(f"Unknown tournament {sport}/{category}/{tournament}")
        return result

    async def search_sports(
        self, query: str, group: str = "winner", limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search sport fixtures by team, player or event name."""
        data = await self._graphql_request(
            GraphQLQueries.SEARCH_SPORTS,
            variables={"query": query, "groups": group, "limit": limit, "offset": offset},
            operation_name="searchQuerySports",
        )
        return [
            r["fixture"] for r in data.get("sportFixtureQuery") or []
            if r.get("fixture")
        ]

    async def get_trending_matches(
        self,
        sort_by: str = "totalBetCount",
        sport_id: Optional[str] = None,
        groups: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the matches with the most betting activity.

        Args:
            sort_by: SportHomepageTrendingOrderByEnum value, e.g.
                "totalBetCount" or "totalBetValue"
            sport_id: Restrict to one sport (its id, see get_sports)
            groups: Market groups to include odds for (default ["winner"])
        """
        data = await self._graphql_request(
            GraphQLQueries.TRENDING_MATCHES,
            variables={"sortBy": sort_by, "sportId": sport_id, "groups": groups or ["winner"]},
            operation_name="SportBetTrendingMatches",
        )
        return data.get("sportHomepageTrendingMatches") or []

    async def get_top_picks(
        self, sort_by: str = "totalBetValue", sport_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the most-backed single outcomes, with bet statistics."""
        data = await self._graphql_request(
            GraphQLQueries.TOP_PICKS,
            variables={"sortBy": sort_by, "sportId": sport_id},
            operation_name="SportBetTopPicks",
        )
        return data.get("sportHomepageTrendingTopPicks") or []

    async def get_top_multis(self) -> List[Dict[str, Any]]:
        """Get the most popular multi (accumulator) bets and their legs."""
        data = await self._graphql_request(
            GraphQLQueries.TOP_MULTIS, operation_name="SportBetTopMultis"
        )
        return data.get("sportHomepageTrendingTopMultis") or []

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

        Raises:
            StakeAPIError: Always — stake has no REST API and the GraphQL
                mutations for placing bets have not been mapped.
        """
        raise StakeAPIError(
            "place_bet is not supported yet: stake.com has no REST API and the "
            "GraphQL mutations for placing bets have not been mapped. "
            "Working methods: get_user_balance, get_user_profile, get_bet_history, get_all_house_bets, get_currency_rates,"
            " plus the public casino, sports and promotion methods."
        )

    async def get_bet_history(
        self, limit: int = 50, offset: int = 0, game: Optional[str] = None
    ) -> List[Bet]:
        """
        Get user casino bet history using GraphQL.

        Args:
            limit: Maximum number of bets to return
            offset: Number of bets to skip (for pagination)
            game: Only bets on one Stake Original (BetHouseEnum), e.g. "dice",
                "limbo", "mines", "plinko", "crash", "dragonTower", "videoPoker"

        Returns:
            List of bets, newest first
        """
        data = await self._graphql_request(
            GraphQLQueries.BET_HISTORY,
            variables={"limit": limit, "offset": offset, "game": game},
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

    async def get_highroller_bets(self, limit: int = 10) -> List[Bet]:
        """
        Get the public feed of recent high-roller casino bets.

        Args:
            limit: Maximum number of bets to return
        """
        data = await self._graphql_request(
            GraphQLQueries.HIGHROLLER_HOUSE_BETS,
            variables={"limit": limit},
            operation_name="HighrollerHouseBets",
        )
        entries = data.get("highrollerHouseBets") or []
        return [b for b in (_bet_from_entry(e) for e in entries) if b]

    async def get_currency_limits(self) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Get per-currency bet limits.

        Returns:
            {currency: {"bet_max": ..., "bet_max_profit": ...}}
        """
        data = await self._graphql_request(
            GraphQLQueries.CURRENCY_LIMITS, operation_name="CurrencyLimits"
        )

        def value(field):
            raw = (field or {}).get("value")
            return float(raw) if raw is not None else None

        return {
            c["name"]: {
                "bet_max": value(c.get("betMax")),
                "bet_max_profit": value(c.get("betMaxProfit")),
            }
            for c in (data.get("info") or {}).get("currencies") or []
            if c.get("name")
        }

    # Promotion Methods
    async def get_challenges(
        self, limit: int = 20, offset: int = 0, sort: str = "startAt", direction: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get public casino challenges (multiplier targets with a prize).

        Args:
            sort: ChallengeSort value, e.g. "startAt"
            direction: "asc" or "desc"

        Returns:
            {"count": total challenges, "challenges": [...]}
        """
        data = await self._graphql_request(
            GraphQLQueries.CHALLENGES,
            variables={"limit": limit, "offset": offset, "sort": sort, "direction": direction},
            operation_name="ChallengePublicList",
        )
        return {
            "count": data.get("challengeUnauthenticatedUserCount", 0),
            "challenges": data.get("challengeUnauthenticatedUserList") or [],
        }

    async def get_active_races(self, leaderboard_limit: int = 10) -> List[Dict[str, Any]]:
        """Get the currently running wager races, each with its top leaderboard."""
        data = await self._graphql_request(
            GraphQLQueries.ACTIVE_RACES,
            variables={"limit": leaderboard_limit},
            operation_name="ActiveRaces",
        )
        return data.get("activeRaces") or []

    async def get_public_chats(self) -> List[Dict[str, Any]]:
        """List public chat rooms (id, name, isPublic), e.g. for StakeWebSocket.chat_messages."""
        data = await self._graphql_request(
            GraphQLQueries.PUBLIC_CHATS, operation_name="PublicChats"
        )
        return data.get("publicChats") or []

    # Account Methods
    async def _user_query(
        self,
        query: str,
        operation_name: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a query rooted at ``user`` and return the user object."""
        data = await self._graphql_request(
            query, variables=variables, operation_name=operation_name
        )
        user = data.get("user")
        if not user:
            raise StakeAPIError(
                f"No user data in {operation_name} response: {data!r}. "
                "Your session may have expired — refresh your cookies."
            )
        return user

    async def get_user_stats(self, name: str) -> Dict[str, Any]:
        """
        Get any player's public profile by username: join date, VIP flags,
        high-roller badges and (unless they hide them) bet statistics.

        This works without logging in.

        Returns:
            The user object. ``statisticScoped`` is a list of per-currency
            stats (bets, wins, losses, betAmount, betValue), or None when the
            player hides their stats.
        """
        data = await self._graphql_request(
            GraphQLQueries.USER_STATS, variables={"name": name}, operation_name="UserDetails"
        )
        user = data.get("user")
        if not user:
            raise StakeAPIError(f"Unknown user {name!r}")
        return user

    async def get_account_status(self) -> Dict[str, Any]:
        """
        Get your account's verification and restriction status: kycStatus,
        email/phone verification, ban/suspension flags and self-exclusion.
        """
        return await self._user_query(GraphQLQueries.ACCOUNT_STATUS, "UserKycInfo")

    async def get_vip_info(self) -> Dict[str, Any]:
        """
        Get your VIP data: rank flags, progress to the next rank, rakeback
        balances, reload, daily and top-up bonuses, and your VIP host.

        Returns:
            The user object with ``flags``, ``flagProgress``, ``rakeback``,
            ``reload``, ``dailyBonus``, ``topUpBonus`` and ``vipInfo``
            (each may be None if it does not apply to your account).
        """
        return await self._user_query(GraphQLQueries.VIP_INFO, "VipMeta")

    async def get_claimable_bonuses(self) -> List[Dict[str, Any]]:
        """Get self-serve bonuses you can claim now (bonusCodeId, code, category, availableAt)."""
        data = await self._graphql_request(
            GraphQLQueries.CLAIMABLE_BONUSES, operation_name="ClaimableVipRewards"
        )
        return data.get("claimableSelfServeBonuses") or []

    async def get_unclaimed_bonuses(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get bonus codes credited to you that have not been redeemed."""
        data = await self._graphql_request(
            GraphQLQueries.UNCLAIMED_BONUSES,
            variables={"limit": limit, "offset": offset},
            operation_name="UserBonusUnclaimedList",
        )
        return data.get("userBonusUnclaimedList") or []

    async def get_active_rollovers(self) -> List[Dict[str, Any]]:
        """Get wagering requirements on your bonuses (amount, progress, expectedAmount, maxBet)."""
        user = await self._user_query(GraphQLQueries.ACTIVE_ROLLOVERS, "UserActiveRollovers")
        return user.get("activeRollovers") or []

    async def get_seed_pair(self) -> Dict[str, Any]:
        """
        Get your provably-fair seeds for Stake Originals.

        Returns:
            {"client_seed": ..., "server_seed_hash": ..., "next_server_seed_hash": ...,
             "nonce": ..., "active_bets": [...]}. Bets still in progress
            (e.g. an open Mines round) block seed rotation.
        """
        user = await self._user_query(GraphQLQueries.SEED_PAIR, "UserSeedPair")
        client_seed = user.get("activeClientSeed") or {}
        server_seed = user.get("activeServerSeed") or {}
        return {
            "client_seed": client_seed.get("seed"),
            "server_seed_hash": server_seed.get("seedHash"),
            "next_server_seed_hash": server_seed.get("nextSeedHash"),
            "nonce": server_seed.get("nonce"),
            "active_bets": user.get("activeCasinoBets") or [],
        }

    async def get_sport_bet_history(
        self, limit: int = 20, offset: int = 0, status: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get your sports bets, newest first.

        Args:
            status: Filter by SportBetStatusEnum values: "confirmed" (open),
                "settled", "cashout", "cancelled"

        Returns:
            Bets with amount, currency, payout, potentialMultiplier and
            outcomes (odds, fixtureName). Racing and Swish bets are skipped.
        """
        user = await self._user_query(
            GraphQLQueries.SPORT_BET_HISTORY,
            "SportSportList",
            {"limit": limit, "offset": offset, "status": status},
        )
        return [
            {"iid": entry.get("iid"), **entry["bet"]}
            for entry in user.get("sportBetList") or []
            if (entry.get("bet") or {}).get("__typename") == "SportBet"
        ]

    async def get_active_sport_bets(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get your open sports bets."""
        user = await self._user_query(
            GraphQLQueries.ACTIVE_SPORT_BETS, "ActiveBets_User", {"limit": limit, "offset": offset}
        )
        return user.get("activeSportBets") or []

    async def get_deposits(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get your crypto deposits (amount, currency, chain, status, hash)."""
        user = await self._user_query(
            GraphQLQueries.DEPOSITS, "DepositList", {"limit": limit, "offset": offset}
        )
        return user.get("depositList") or []

    async def get_withdrawals(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get your crypto withdrawals (amount, currency, chain, status, hash, address)."""
        user = await self._user_query(
            GraphQLQueries.WITHDRAWALS, "WithdrawalList", {"limit": limit, "offset": offset}
        )
        return user.get("withdrawalList") or []

    async def get_tip_history(
        self, limit: int = 20, offset: int = 0, name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tips you sent and received.

        Args:
            name: Your username. Looked up from your account when omitted.
        """
        if not name:
            name = (await self.get_account_status()).get("name")
        user = await self._user_query(
            GraphQLQueries.TIP_HISTORY,
            "UserTipHistory",
            {"name": name, "limit": limit, "offset": offset},
        )
        return user.get("tipHistory") or []

    async def get_game_statistics(
        self, period: str = "all", sort: str = "wagered", limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get your per-game totals: bet count, wagered, profit and RTP.

        Args:
            period: "day", "week", "month" or "all"
            sort: "wagered", "profit", "bets" or "rtp"
        """
        data = await self._graphql_request(
            GraphQLQueries.GAME_STATISTICS,
            variables={"period": period, "sort": sort, "limit": limit, "offset": offset},
            operation_name="UserGameStatisticList",
        )
        return data.get("userGameStatisticList") or []

    async def get_favourite_games(self, limit: int = 50, offset: int = 0) -> List[Game]:
        """Get the casino games you marked as favourite."""
        user = await self._user_query(
            GraphQLQueries.FAVOURITE_GAMES, "UserFavouriteGames", {"limit": limit, "offset": offset}
        )
        return [g for g in map(_game_from_kurator, user.get("favouriteGameList") or []) if g]

    async def get_recent_games(self, limit: int = 20, offset: int = 0) -> List[Game]:
        """Get the casino games you played most recently."""
        user = await self._user_query(
            GraphQLQueries.RECENT_GAMES, "UserRecentGameList", {"limit": limit, "offset": offset}
        )
        return [g for g in map(_game_from_kurator, user.get("recentGameList") or []) if g]

    async def get_race_positions(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get your finishing positions and payouts in past and current races."""
        user = await self._user_query(
            GraphQLQueries.RACE_POSITIONS, "UserRacePositionList", {"limit": limit, "offset": offset}
        )
        return user.get("racePositionList") or []

    async def get_notifications(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get your notifications, newest first.

        Each has ``type``, ``createdAt``, ``acknowledged`` and ``data``, whose
        ``__typename`` tells what it is (e.g. "ChatTip", "WalletDeposit",
        "NotificationUserBonus", "RacePosition", "SportBet").
        """
        user = await self._user_query(
            GraphQLQueries.NOTIFICATIONS, "NotificationList", {"limit": limit, "offset": offset}
        )
        return user.get("notificationList") or []

    async def get_gambling_limits(self) -> List[Dict[str, Any]]:
        """Get the responsible-gambling limits set on your account (type, period, value, progress)."""
        user = await self._user_query(
            GraphQLQueries.GAMBLING_LIMITS, "ResponsibleGamblingLimitList"
        )
        return user.get("responsibleGamblingLimits") or []

    async def get_sessions(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get your login sessions (device name, IP, location, active, last seen)."""
        user = await self._user_query(
            GraphQLQueries.SESSIONS, "SessionList", {"limit": limit, "offset": offset}
        )
        return user.get("sessionList") or []
