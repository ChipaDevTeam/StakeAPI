"""Main client for StakeAPI."""

import asyncio
import json
import uuid
from dataclasses import dataclass
from decimal import Decimal
from types import TracebackType
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, cast
from urllib.parse import urljoin, urlparse

import aiohttp

from .auth import AuthManager
from .endpoints import GraphQLMutations, GraphQLQueries
from .exceptions import (
    AuthenticationError,
    BettingDisabledError,
    GraphQLError,
    NetworkError,
    PermissionDeniedError,
    RateLimitError,
    StakeAPIError,
    ValidationError,
)
from .models import Bet, Game, SportEvent, User
from .websocket import StakeWebSocket

if TYPE_CHECKING:
    from .browser import BrowserSession


def _parse_datetime(value: Optional[str]) -> Any:
    """Parse the RFC 1123 dates the API returns.

    Example: 'Sat, 11 Jul 2026 07:41:10 GMT'.
    """
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
    categories = [
        str(g["translation"])
        for g in groups
        if g.get("type") == "category" and g.get("translation")
    ]
    provider = (game.get("providerGroup") or {}).get("name") or next(
        (g.get("translation") for g in groups if g.get("type") == "provider"), ""
    )
    edge = game.get("edge")
    try:
        return Game(
            id=game["id"],
            name=game.get("name", ""),
            slug=game.get("slug"),
            category=categories[0] if categories else str(game.get("type") or ""),
            provider=provider or "",
            description=game.get("description"),
            rtp=round((1 - edge) * 100, 4) if edge is not None else None,
            features=[str(g["translation"]) for g in groups if g.get("translation")],
            thumbnail_url=game.get("thumbnailUrl"),
            player_count=game.get("playerCount"),
        )
    except Exception:
        return None


@dataclass
class _Reply:
    """An HTTP response from either transport (aiohttp or the browser)."""

    status: int
    headers: Dict[str, str]  # header names are lower-case
    text: str


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
        allow_betting: bool = False,
        browser: Optional["BrowserSession"] = None,
    ):
        """
        Initialize the StakeAPI client.

        Args:
            access_token: Your stake.com access token (x-access-token header).
                If omitted but cookies are provided, the 'session' cookie value
                is used as the access token (they are the same value on stake).
            session_cookie: Session cookie for authentication
            cf_clearance: Cloudflare clearance cookie (required to get past
                Cloudflare protection)
            user_agent: Your browser's User-Agent (must match the one used to
                obtain cf_clearance)
            base_url: Base URL for the API. Use this to point at a regional
                mirror, e.g. "https://stake1017.com" or "https://stake.bet".
                Your cookies (session, cf_clearance) must come from the SAME
                domain you set here.
            timeout: Request timeout in seconds
            rate_limit: Maximum requests per second
            cookie_file: Path to a cookie file: either the entire Cookie header
                copied from your browser (DevTools → Network tab → any request
                → 'cookie' header), e.g. "cookie.txt", or a JSON export from a
                cookie extension, e.g. "cookies.json" (only cookies for
                base_url's domain are used; expired ones are skipped). All
                cookies are sent as-is, and session/cf_clearance/access token
                are extracted automatically. Takes precedence over
                cookie_string.
            cookie_string: The same raw cookie string, passed directly instead
                of via a file.
            browser: A BrowserSession. When given, requests are sent from inside
                that logged-in Chrome window instead of over plain HTTP; see
                StakeAPI.with_browser().
            allow_betting: Must be True for any method that places or cashes
                out a real-money bet. Off by default so a script cannot bet by
                accident; every bet method also supports dry_run=True.

        Raises:
            ValidationError: If base_url is not a valid http(s) URL, or the
                cookie file is missing/empty/unreadable.
        """
        if not isinstance(base_url, str) or not base_url.startswith(
            ("http://", "https://")
        ):
            raise ValidationError(
                f"Invalid base_url: {base_url!r}. "
                "It must start with http:// or https://, "
                "e.g. 'https://stake.com' or a mirror like 'https://stake1017.com'."
            )

        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.allow_betting = allow_betting
        self.cf_clearance = cf_clearance

        # Credentials live in the AuthManager; access_token and session_cookie
        # are properties on it, so changing them takes effect on the next request
        self._auth_manager = AuthManager(access_token, session_cookie)
        self._explicit_token = access_token is not None
        self._cookie_file = cookie_file
        self._cookie_header: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._browser = browser
        self._browser_login_timeout = 300.0
        self._load_cookies(cookie_file, cookie_string)

    @property
    def access_token(self) -> Optional[str]:
        """The x-access-token sent with every request."""
        return self._auth_manager.access_token

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        self._auth_manager.access_token = value

    @property
    def session_cookie(self) -> Optional[str]:
        """The 'session' cookie value."""
        return self._auth_manager.session_cookie

    @session_cookie.setter
    def session_cookie(self, value: Optional[str]) -> None:
        self._auth_manager.session_cookie = value

    def _load_cookies(
        self,
        cookie_file: Optional[str],
        cookie_string: Optional[str],
        refresh: bool = False,
    ) -> None:
        """
        Read cookies from a file or string and derive the credentials from them.

        At construction, values passed explicitly win over the cookies. On a
        refresh the cookies win, except an access token that was set explicitly.
        """
        if cookie_file:
            try:
                header: Optional[str] = AuthManager.load_cookie_file(
                    cookie_file, domain=urlparse(self.base_url).hostname
                )
            except OSError as e:
                raise ValidationError(
                    f"Could not read cookie file {cookie_file!r}: {e}. "
                    "Create it by copying the entire 'cookie' request header from "
                    "your browser (DevTools → Network tab → any request → Headers)."
                )
            except ValueError as e:
                raise ValidationError(str(e))
        elif cookie_string:
            header = " ".join(cookie_string.split())
        else:
            return

        parsed = AuthManager.parse_cookie_string(header or "")
        if not parsed:
            raise ValidationError(
                "No cookies could be parsed from the provided cookie data. "
                "Expected format: 'name1=value1; name2=value2; ...'"
            )
        self._cookie_header = header
        if refresh:
            self.session_cookie = parsed.get("session", self.session_cookie)
            self.cf_clearance = parsed.get("cf_clearance", self.cf_clearance)
            if not self._explicit_token:
                self.access_token = parsed.get("session", self.access_token)
        else:
            self.session_cookie = self.session_cookie or parsed.get("session")
            self.cf_clearance = self.cf_clearance or parsed.get("cf_clearance")
            # On stake, the x-access-token header carries the same value
            # as the 'session' cookie
            self.access_token = self.access_token or parsed.get("session")

    def set_access_token(self, access_token: str) -> None:
        """
        Replace the access token. It is used from the next request on.

        Use this when the token is refreshed while the client is running.
        """
        self._explicit_token = True
        self._auth_manager.set_access_token(access_token)

    async def reload_cookies(self) -> None:
        """
        Re-read the cookie file and use the new cookies from the next request on.

        Use this in a long-running script after you re-export cookies from your
        browser, instead of recreating the client. An access token that was
        passed explicitly is kept.

        Raises:
            ValidationError: If the client was not created with cookie_file, or
                the file is unreadable or has no usable cookies.
        """
        if not self._cookie_file:
            raise ValidationError(
                "reload_cookies() needs the client to be created with cookie_file=..."
            )
        self._load_cookies(self._cookie_file, None, refresh=True)
        await self._reset_session()

    async def __aenter__(self) -> "StakeAPI":
        """Async context manager entry."""
        if self._browser is not None:
            await self._start_browser()
        else:
            await self._create_session()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def _session_headers(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Build the default headers and cookies sent with every request."""
        ua = (
            self.user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
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
        cookies = {}
        if self._cookie_header:
            headers["Cookie"] = self._cookie_header
        else:
            if self.session_cookie:
                cookies["session"] = self.session_cookie
            if self.cf_clearance:
                cookies["cf_clearance"] = self.cf_clearance
        return headers, cookies

    async def _create_session(self) -> None:
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

    async def _reset_session(self) -> None:
        """Drop the HTTP session; the next request opens a new one."""
        if self._session:
            await self._session.close()
            self._session = None

    async def close(self) -> None:
        """Close the session and the browser window, if any.

        An HTTP client reconnects on the next request.
        """
        await self._reset_session()
        if self._browser is not None and self._browser.started:
            await asyncio.to_thread(self._browser.close)

    @classmethod
    def with_browser(
        cls,
        base_url: str = "https://stake.com",
        *,
        login_timeout: float = 300.0,
        **browser_options: Any,
    ) -> "StakeAPI":
        """
        A client that sends every request from inside a real Chrome window.

        Entering ``async with`` opens Chrome at the login page and waits for you
        to log in (nothing is typed for you). After that the library works,
        because the site sees ordinary requests from a logged-in browser tab.
        The login is kept in a Chrome profile folder, so later runs skip it.

        Needs ``pip install "stakeapi[browser]"`` and Chrome.

        Args:
            base_url: The site or mirror, e.g. "https://stake1017.com"
            login_timeout: Seconds to wait for you to log in. 0 skips the wait,
                which is enough for public data.
            **browser_options: Passed to BrowserSession (profile_dir, headless,
                chrome_binary, chromedriver_path, import_cookies_from, ...)

        Example:
            async with StakeAPI.with_browser("https://stake1017.com") as client:
                print(await client.get_account_status())
        """
        from .browser import BrowserSession

        client = cls(
            base_url=base_url, browser=BrowserSession(base_url, **browser_options)
        )
        client._browser_login_timeout = login_timeout
        return client

    @classmethod
    def from_chrome(
        cls,
        base_url: str = "https://stake.com",
        *,
        browser: str = "chrome",
        profile: Optional[str] = None,
        **kwargs: Any,
    ) -> "StakeAPI":
        """
        A plain HTTP client that uses the cookies of your own Chrome.

        Reads the Stake cookies from Chrome's profile on this computer (only
        for ``base_url``'s domain). Because the requests are not made by a
        browser, the site's bot protection may still refuse logged-in calls;
        use with_browser() if it does.

        Needs ``pip install "stakeapi[browser]"``.

        Args:
            browser: "chrome", "chromium", "brave", "edge", ...
            profile: Profile folder name such as "Profile 2". By default the
                profile that is logged in to the site is used.
        """
        from .chrome_cookies import load_chrome_cookies

        imported = load_chrome_cookies(
            urlparse(base_url).hostname or "", browser=browser, profile=profile
        )
        header = "; ".join(f"{c['name']}={c['value']}" for c in imported.cookies)
        return cls(base_url=base_url, cookie_string=header, **kwargs)

    async def _start_browser(self) -> None:
        """Open the browser if needed and wait until you are logged in."""
        browser = cast("BrowserSession", self._browser)
        if not browser.started:
            await asyncio.to_thread(browser.start)
        if self._browser_login_timeout > 0:
            await asyncio.to_thread(browser.wait_for_login, self._browser_login_timeout)
        await self._refresh_credentials()

    async def _refresh_credentials(self) -> None:
        """Copy the login, Cloudflare cookie and User-Agent from the browser."""
        if self._browser is None or not self._browser.started:
            return
        browser = self._browser

        def read() -> Tuple[List[Dict[str, Any]], str, str]:
            return browser.cookies(), browser.cookie_header(), browser.user_agent()

        cookies, header, user_agent = await asyncio.to_thread(read)
        values = {c["name"]: c["value"] for c in cookies}
        self._cookie_header = header or None
        self.user_agent = user_agent or self.user_agent
        self.session_cookie = values.get("session", self.session_cookie)
        self.cf_clearance = values.get("cf_clearance", self.cf_clearance)
        if not self._explicit_token:
            self.access_token = values.get("session", self.access_token)

    def _forbidden_error(self, reply: _Reply) -> StakeAPIError:
        """Build a 403 error that says who blocked the request and what to check."""
        body = reply.text[:3000].lower()
        headers = reply.headers
        if any(m in body for m in ("cf-error-details", "attention required")):
            source = "a Cloudflare block page"
        elif "just a moment" in body or "cf-mitigated" in headers:
            source = "a Cloudflare challenge"
        elif "kpsdk" in body or any(k.startswith("x-kpsdk") for k in headers):
            source = "Kasada bot protection"
        else:
            source = "the site's bot protection"

        if self._browser is not None:
            hints = [
                "The request was made from the automated Chrome window and was "
                "still refused: the site may block automated browsers or this "
                "network. Make sure the window shows the site logged in, or try "
                "once in a normal Chrome. This library adds no stealth."
            ]
            return StakeAPIError(
                f"403 Forbidden from {self.base_url}: blocked by {source}. "
                + " ".join(hints)
            )

        hints = []
        if not self._cookie_header and not self.cf_clearance:
            hints.append(
                "No cookies were sent. Pass cookie_file= with the cookies of a "
                f"browser that is logged in to {self.base_url}."
            )
        elif (
            "cf_clearance" not in (self._cookie_header or "") and not self.cf_clearance
        ):
            hints.append(
                "Your cookies have no cf_clearance. If the block is Cloudflare's, "
                "copy it from DevTools → Application → Cookies."
            )
        hints.append(
            "Cookies must come from the SAME domain as base_url, and some are "
            "short-lived (re-copy them if they are old)."
        )
        hints.append(
            "The protection also checks that the request looks like the browser "
            "that earned the cookies: use the same network, and pass "
            f"user_agent= with that browser's exact User-Agent (now: "
            f"{self.user_agent or 'library default'!r}). A script can still be "
            "refused even with valid cookies. Use StakeAPI.with_browser() to send "
            "requests from a real logged-in Chrome window; this library does not "
            "work around bot protection."
        )
        return StakeAPIError(
            f"403 Forbidden from {self.base_url}: blocked by {source}. "
            + " ".join(hints)
        )

    async def _send(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
        headers: Dict[str, str],
    ) -> _Reply:
        """Send one request over the active transport and return the raw reply."""
        if self._browser is not None:
            browser = self._browser
            if not browser.started:
                await self._start_browser()
            status, reply_headers, text = await asyncio.to_thread(
                browser.fetch, method, url, params, data, headers
            )
            return _Reply(
                status, {k.lower(): v for k, v in reply_headers.items()}, text
            )

        if not self._session:
            await self._create_session()
        session = cast(aiohttp.ClientSession, self._session)
        async with session.request(
            method, url, params=params, json=data, headers=headers
        ) as response:
            text = await response.text(errors="replace")
            return _Reply(
                response.status,
                {k.lower(): v for k, v in response.headers.items()},
                text,
            )

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

        The request goes over plain HTTP, or through the browser window when the
        client was created with a browser.

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
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        # Sent per request, not baked into the session, so set_access_token()
        # and reload_cookies() apply immediately
        request_headers = dict(headers or {})
        if self.access_token and "x-access-token" not in {
            k.lower() for k in request_headers
        }:
            request_headers["X-Access-Token"] = self.access_token

        try:
            reply = await self._send(method, url, params, data, request_headers)
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
                "you can pass a different mirror, e.g. "
                "StakeAPI(base_url='https://stake1017.com')."
            )
        except aiohttp.ClientError as e:
            raise NetworkError(f"Request failed: {e}")

        if reply.status == 403:
            raise self._forbidden_error(reply)
        elif reply.status == 401:
            raise AuthenticationError(
                "Invalid access token or unauthorized access (401). "
                "Your token may have expired: copy a fresh one, then call "
                "set_access_token() or reload_cookies()."
            )
        elif reply.status == 429:
            retry_after = reply.headers.get("retry-after")
            message = "Rate limit exceeded"
            if retry_after:
                message += f" — retry after {retry_after} seconds"
            raise RateLimitError(message)
        elif reply.status >= 500:
            raise StakeAPIError(
                f"Server error {reply.status} from {self.base_url}. "
                "The site may be down or the mirror may be unavailable — "
                "try again later or switch base_url to another mirror."
            )

        try:
            response_data = json.loads(reply.text)
        except ValueError:
            raise NetworkError(
                "Expected JSON but got a non-JSON response "
                f"(status {reply.status}) from {url}. This usually "
                "means a Cloudflare challenge page or a redirect to a "
                f"login page. Response starts with: {reply.text[:200]!r}"
            )

        if reply.status >= 400:
            raise StakeAPIError(f"API error: {reply.status} - {response_data}")

        return cast(Dict[Any, Any], response_data)

    async def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        allow_partial: bool = False,
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
        payload: Dict[str, Any] = {
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

        errors = response.get("errors")
        if errors:
            # Some fields come back null with an error (e.g. a bonus that is
            # disabled for the account) next to otherwise valid data. With
            # allow_partial that data is returned, unless the API refused the
            # request for permission reasons.
            if not (
                allow_partial
                and response.get("data")
                and not self._is_permission_error(errors)
            ):
                self._raise_for_errors(errors)

        data = response.get("data")
        if data is None:
            raise GraphQLError(
                "GraphQL response contained no data and no errors — "
                f"raw response: {response!r}"
            )

        return cast(Dict[str, Any], data)

    @staticmethod
    def _is_permission_error(errors: List[Dict[str, Any]]) -> bool:
        """True if any API error says the caller is not allowed or not logged in."""
        permission_markers = (
            "not allowed",
            "unauthorized",
            "permission",
            "forbidden",
            "notauthenticated",
            "please log in",
        )
        texts = [error.get("message", "Unknown error") for error in errors]
        texts += [
            error.get("errorType") or error.get("extensions", {}).get("code", "")
            for error in errors
        ]
        return any(
            marker in text.lower() for text in texts for marker in permission_markers
        )

    def _raise_for_errors(self, errors: List[Dict[str, Any]]) -> None:
        """Raise PermissionDeniedError or GraphQLError for an API error list."""
        error_messages = [error.get("message", "Unknown error") for error in errors]
        joined = ", ".join(error_messages)

        if self._is_permission_error(errors):
            raise PermissionDeniedError(
                f"GraphQL permission error: {joined}. This usually means: "
                "1) your access token is invalid or expired — get a fresh one "
                f"from {self.base_url} (DevTools → any GraphQL request → "
                "'x-access-token' header); 2) your session/cf_clearance cookies "
                "were obtained from a different domain than base_url "
                f"({self.base_url}) — token and cookies must all come from the "
                "same mirror; or 3) your account lacks permission for this "
                "operation.",
                errors=errors,
            )

        raise GraphQLError(f"GraphQL errors: {joined}", errors=errors)

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
        games = (
            _game_from_kurator(g.get("game") or {})
            for g in group.get("groupGamesList") or []
        )
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

    async def search_casino_games(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> List[Game]:
        """Search casino games by name."""
        data = await self._graphql_request(
            GraphQLQueries.SEARCH_CASINO,
            variables={"query": query, "limit": limit, "offset": offset},
            operation_name="searchQueryCasino",
        )
        games = (_game_from_kurator(g) for g in data.get("kuratorGameQuery") or [])
        return [g for g in games if g]

    async def get_casino_collection(
        self,
        collection_type: str = "provider",
        sort: str = "popular",
        filter: str = "all",
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
        return [
            c["group"] for c in data.get("kuratorCollection") or [] if c.get("group")
        ]

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

    async def get_crash_history(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
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
        return cast(Dict[str, Any], game)

    async def get_slide_history(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
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
        return cast(Dict[str, Any], sport_data)

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
        return cast(Dict[str, Any], result)

    async def search_sports(
        self, query: str, group: str = "winner", limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search sport fixtures by team, player or event name."""
        data = await self._graphql_request(
            GraphQLQueries.SEARCH_SPORTS,
            variables={
                "query": query,
                "groups": group,
                "limit": limit,
                "offset": offset,
            },
            operation_name="searchQuerySports",
        )
        return [
            r["fixture"]
            for r in data.get("sportFixtureQuery") or []
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
            variables={
                "sortBy": sort_by,
                "sportId": sport_id,
                "groups": groups or ["winner"],
            },
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
        Not supported: stake has no single bet endpoint. Use the per-game
        methods instead (dice_roll, casino_bet, crash_bet, slide_bet,
        flip_bet, zoo_bet, place_sport_bet).
        """
        raise StakeAPIError(
            "place_bet is not supported: stake has a separate bet call per game. "
            "Use dice_roll, casino_bet, crash_bet, slide_bet, flip_bet, zoo_bet "
            "or place_sport_bet (all need StakeAPI(allow_betting=True))."
        )

    # Real-money betting. UNVALIDATED: built from the site's own code but never
    # sent to the live API. Every method needs allow_betting=True on the client
    # and supports dry_run=True, which returns the request instead of sending it.
    def _check_betting(self, method: str) -> None:
        if not self.allow_betting:
            raise BettingDisabledError(
                f"{method} places a real-money bet. Create the client with "
                "StakeAPI(..., allow_betting=True) to enable betting, or pass "
                "dry_run=True to see the request without sending it."
            )

    @staticmethod
    def _check_amount(amount: float, currency: str) -> None:
        if amount is None or amount < 0:
            raise ValidationError(
                f"Bet amount must be zero or positive, got {amount!r}"
            )
        if not currency or not isinstance(currency, str):
            raise ValidationError(
                f"currency must be a currency code such as 'btc', got {currency!r}"
            )

    async def _bet_mutation(
        self,
        method: str,
        query: str,
        operation_name: str,
        field: str,
        variables: Dict[str, Any],
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Send (or with dry_run, describe) a betting GraphQL mutation."""
        variables = {k: v for k, v in variables.items() if v is not None}
        if dry_run:
            return {
                "dry_run": True,
                "endpoint": "/_api/graphql",
                "operation_name": operation_name,
                "variables": variables,
            }
        self._check_betting(method)
        data = await self._graphql_request(
            query, variables=variables, operation_name=operation_name
        )
        return cast(Dict[str, Any], data.get(field) or {})

    async def casino_bet(
        self, path: str, variables: Dict[str, Any], dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Call a Stake Originals bet endpoint directly.

        Stake Originals (Dice, Limbo, Mines, ...) are not GraphQL: the site
        POSTs the bet variables as JSON to ``/_api/casino/<path>`` and gets
        back an object keyed by the action, e.g. ``{"diceRoll": {...}}``.

        Known paths from the site's code: "dice/roll", "limbo/bet",
        "mines/bet", "mines/next". Only Dice's variables are known; for the
        others, copy them from your browser's DevTools Network tab.

        Args:
            path: Endpoint path after /_api/casino/, e.g. "limbo/bet"
            variables: JSON body. An ``identifier`` is added if missing.
            dry_run: Return the request instead of sending it.

        Returns:
            The result object (the response's single top-level value).
        """
        path = path.strip("/")
        body = {"identifier": uuid.uuid4().hex, **variables}
        if dry_run:
            return {
                "dry_run": True,
                "endpoint": f"/_api/casino/{path}",
                "variables": body,
            }
        self._check_betting("casino_bet")
        response = await self._request("POST", f"/_api/casino/{path}", data=body)
        if not isinstance(response, dict):
            raise StakeAPIError(
                f"Unexpected response from /_api/casino/{path}: {response!r}"
            )
        if response.get("errors"):
            self._raise_for_errors(response["errors"])
        results = [v for v in response.values() if isinstance(v, dict)]
        if len(results) != 1:
            raise StakeAPIError(
                f"Unexpected response from /_api/casino/{path}: {response!r}"
            )
        return results[0]

    async def dice_roll(
        self,
        amount: float,
        currency: str,
        target: float,
        condition: str = "above",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Roll Stake Dice.

        Args:
            amount: Stake in ``currency`` (0 for a free roll)
            currency: Currency code, e.g. "btc", "usdt"
            target: Roll target between 2 and 98
            condition: "above" or "below" the target
            dry_run: Return the request instead of sending it

        Returns:
            The diceRoll result: amount, payout, payoutMultiplier, state, ...
        """
        self._check_amount(amount, currency)
        if condition not in ("above", "below"):
            raise ValidationError(
                f"condition must be 'above' or 'below', got {condition!r}"
            )
        if not 2 <= target <= 98:
            raise ValidationError(
                f"Dice target must be between 2 and 98, got {target!r}"
            )
        return await self.casino_bet(
            "dice/roll",
            {
                "target": target,
                "condition": condition,
                "amount": amount,
                "currency": currency,
            },
            dry_run=dry_run,
        )

    async def crash_bet(
        self, amount: float, currency: str, cashout_at: float, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Join the next Crash round with an automatic cashout.

        Args:
            cashout_at: Auto-cashout multiplier, e.g. 2.0
        """
        self._check_amount(amount, currency)
        if cashout_at is None or cashout_at <= 1:
            raise ValidationError(f"cashout_at must be above 1, got {cashout_at!r}")
        return await self._bet_mutation(
            "crash_bet",
            GraphQLMutations.CRASH_BET,
            "MultiplayerCrashBet",
            "multiplayerCrashBet",
            {"amount": amount, "currency": currency, "cashoutAt": cashout_at},
            dry_run,
        )

    async def crash_cashout(self, dry_run: bool = False) -> Dict[str, Any]:
        """Cash out your bet in the running Crash round now."""
        return await self._bet_mutation(
            "crash_cashout",
            GraphQLMutations.CRASH_CASHOUT,
            "MultiplayerCrashCashout",
            "multiplayerCrashCashout",
            {},
            dry_run,
        )

    async def slide_bet(
        self,
        currency: str,
        bets: List[Dict[str, Any]],
        identifier: Optional[str] = None,
        dry_run: bool = False,
    ) -> Any:
        """
        Place bets on the next Slide round.

        Returns the list of placed bets (or the request dict with dry_run).

        Args:
            bets: SlideBetsBetsInput objects, passed through as given. Their
                fields are not confirmed; copy one from DevTools first.
        """
        self._check_amount(0, currency)
        result = await self._bet_mutation(
            "slide_bet",
            GraphQLMutations.SLIDE_BETS,
            "SlideBets",
            "slideBets",
            {
                "currency": currency,
                "bets": bets,
                "identifier": identifier or uuid.uuid4().hex,
            },
            dry_run,
        )
        return result or []

    async def flip_bet(
        self,
        amount: float,
        currency: str,
        guesses: List[str],
        identifier: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Start a Flip game.

        Args:
            guesses: FlipConditionEnum values, one per coin (values not
                confirmed; copy them from DevTools first)
        """
        self._check_amount(amount, currency)
        return await self._bet_mutation(
            "flip_bet",
            GraphQLMutations.FLIP_BET,
            "FlipBet",
            "flipBet",
            {
                "amount": amount,
                "currency": currency,
                "guesses": guesses,
                "identifier": identifier or uuid.uuid4().hex,
            },
            dry_run,
        )

    async def flip_next(self, condition: str, dry_run: bool = False) -> Dict[str, Any]:
        """Flip the next coin in your active Flip game."""
        return await self._bet_mutation(
            "flip_next",
            GraphQLMutations.FLIP_NEXT,
            "FlipNext",
            "flipNext",
            {"condition": condition},
            dry_run,
        )

    async def flip_cashout(
        self, identifier: str, dry_run: bool = False
    ) -> Dict[str, Any]:
        """Cash out your active Flip game."""
        return await self._bet_mutation(
            "flip_cashout",
            GraphQLMutations.FLIP_CASHOUT,
            "FlipCashout",
            "flipCashout",
            {"identifier": identifier},
            dry_run,
        )

    async def zoo_bet(
        self,
        currency: str,
        animals: List[Dict[str, Any]],
        identifier: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Place bets on the next Zoo round.

        Args:
            animals: ZooBetAnimalsInput objects, passed through as given
                (results show ``{"animal", "amount"}`` pairs; confirm the
                input shape in DevTools first)
        """
        self._check_amount(0, currency)
        return await self._bet_mutation(
            "zoo_bet",
            GraphQLMutations.ZOO_BET,
            "ZooBet",
            "zooBet",
            {
                "currency": currency,
                "animals": animals,
                "identifier": identifier or uuid.uuid4().hex,
            },
            dry_run,
        )

    async def place_sport_bet(
        self,
        amount: float,
        currency: str,
        outcome_ids: List[str],
        odds_change: str,
        bet_type: str,
        identifier: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a sports bet (a single, or a multi with several outcomes).

        Args:
            outcome_ids: Outcome ``id`` values from any fixture's markets
            odds_change: SportOddsChangeEnum value: which odds moves to accept
            bet_type: SportBetTypeEnum value
            dry_run: Return the request instead of sending it

        odds_change and bet_type have no defaults because their valid values
        are not confirmed; copy them from a bet placed in your browser
        (DevTools → Network → BetSlipFooter_SportBet).
        """
        self._check_amount(amount, currency)
        if not outcome_ids:
            raise ValidationError("outcome_ids must contain at least one outcome id")
        return await self._bet_mutation(
            "place_sport_bet",
            GraphQLMutations.SPORT_BET,
            "BetSlipFooter_SportBet",
            "sportBet",
            {
                "amount": amount,
                "currency": currency,
                "outcomeIds": list(outcome_ids),
                "oddsChange": odds_change,
                "betType": bet_type,
                "identifier": identifier or uuid.uuid4().hex,
            },
            dry_run,
        )

    async def cashout_sport_bet(
        self,
        bet_id: str,
        multiplier: float,
        cashout_percent: Optional[float] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Cash out an open sports bet.

        Args:
            bet_id: The bet's id (from get_active_sport_bets)
            multiplier: The cashout multiplier currently offered for the bet
            cashout_percent: Cash out only part of the bet
        """
        return await self._bet_mutation(
            "cashout_sport_bet",
            GraphQLMutations.SPORT_BET_CASHOUT,
            "SportBetPreview_CashoutSportBet",
            "cashoutSportBet",
            {
                "betId": bet_id,
                "multiplier": multiplier,
                "cashoutPercent": cashout_percent,
            },
            dry_run,
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

        def value(field: Optional[Dict[str, Any]]) -> Optional[float]:
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
        self,
        limit: int = 20,
        offset: int = 0,
        sort: str = "startAt",
        direction: str = "desc",
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
            variables={
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "direction": direction,
            },
            operation_name="ChallengePublicList",
        )
        return {
            "count": data.get("challengeUnauthenticatedUserCount", 0),
            "challenges": data.get("challengeUnauthenticatedUserList") or [],
        }

    async def get_active_races(
        self, leaderboard_limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get the currently running wager races, each with its top leaderboard."""
        data = await self._graphql_request(
            GraphQLQueries.ACTIVE_RACES,
            variables={"limit": leaderboard_limit},
            operation_name="ActiveRaces",
        )
        return data.get("activeRaces") or []

    async def get_public_chats(self) -> List[Dict[str, Any]]:
        """List public chat rooms (id, name, isPublic).

        Use the ids with StakeWebSocket.chat_messages.
        """
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
        allow_partial: bool = False,
    ) -> Dict[str, Any]:
        """Run a query rooted at ``user`` and return the user object."""
        data = await self._graphql_request(
            query,
            variables=variables,
            operation_name=operation_name,
            allow_partial=allow_partial,
        )
        user = data.get("user")
        if not user:
            raise StakeAPIError(
                f"No user data in {operation_name} response: {data!r}. "
                "Your session may have expired — refresh your cookies."
            )
        return cast(Dict[str, Any], user)

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
            GraphQLQueries.USER_STATS,
            variables={"name": name},
            operation_name="UserDetails",
        )
        user = data.get("user")
        if not user:
            raise StakeAPIError(f"Unknown user {name!r}")
        return cast(Dict[str, Any], user)

    async def get_account_status(self) -> Dict[str, Any]:
        """
        Get your account's verification and restriction status: kycStatus,
        email/phone verification, ban/suspension flags and self-exclusion.
        """
        return await self._user_query(GraphQLQueries.ACCOUNT_STATUS, "UserKycInfo")

    async def get_vip_info(self) -> Dict[str, Any]:
        """
        Get your VIP data: rank flags, VIP progress, rakeback balances,
        reload, daily and top-up bonuses, and your VIP host.

        Returns:
            The user object with ``flags`` (a list, possibly empty),
            ``flagProgress`` (one ``{"flag", "progress"}`` object, where
            progress is a fraction between 0 and 1), ``rakeback``, ``reload``,
            ``dailyBonus``, ``topUpBonus`` and ``vipInfo``. The last four are
            None when the feature is disabled for your account; the site
            reports that as an error next to the data, which is ignored here.
        """
        return await self._user_query(
            GraphQLQueries.VIP_INFO, "VipMeta", allow_partial=True
        )

    async def get_claimable_bonuses(self) -> List[Dict[str, Any]]:
        """Get self-serve bonuses you can claim now.

        Each has bonusCodeId, code, category and availableAt.
        """
        data = await self._graphql_request(
            GraphQLQueries.CLAIMABLE_BONUSES, operation_name="ClaimableVipRewards"
        )
        return data.get("claimableSelfServeBonuses") or []

    async def get_unclaimed_bonuses(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get bonus codes credited to you that have not been redeemed."""
        data = await self._graphql_request(
            GraphQLQueries.UNCLAIMED_BONUSES,
            variables={"limit": limit, "offset": offset},
            operation_name="UserBonusUnclaimedList",
        )
        return data.get("userBonusUnclaimedList") or []

    async def get_active_rollovers(self) -> List[Dict[str, Any]]:
        """Get wagering requirements on your bonuses.

        Each has amount, progress, expectedAmount and maxBet.
        """
        user = await self._user_query(
            GraphQLQueries.ACTIVE_ROLLOVERS, "UserActiveRollovers"
        )
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

    async def get_active_sport_bets(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get your open sports bets."""
        user = await self._user_query(
            GraphQLQueries.ACTIVE_SPORT_BETS,
            "ActiveBets_User",
            {"limit": limit, "offset": offset},
        )
        return user.get("activeSportBets") or []

    async def get_deposits(
        self, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get your crypto deposits (amount, currency, chain, status, hash)."""
        user = await self._user_query(
            GraphQLQueries.DEPOSITS, "DepositList", {"limit": limit, "offset": offset}
        )
        return user.get("depositList") or []

    async def get_withdrawals(
        self, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get your crypto withdrawals.

        Each has amount, currency, chain, status, hash and address.
        """
        user = await self._user_query(
            GraphQLQueries.WITHDRAWALS,
            "WithdrawalList",
            {"limit": limit, "offset": offset},
        )
        return user.get("withdrawalList") or []

    async def get_tip_history(
        self, limit: int = 20, offset: int = 0, name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tips you sent and received.

        Args:
            name: Your username. Looked up from your account when omitted.

        Raises:
            PermissionDeniedError: The site refuses tip history on some
                accounts even when logged in ("You are not allowed to do that").
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
        self,
        period: str = "all",
        sort: str = "wagered",
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get your per-game totals: bet count, wagered, profit and RTP.

        Args:
            period: "day", "week", "month" or "all"
            sort: "wagered", "profit", "bets" or "rtp"
        """
        data = await self._graphql_request(
            GraphQLQueries.GAME_STATISTICS,
            variables={
                "period": period,
                "sort": sort,
                "limit": limit,
                "offset": offset,
            },
            operation_name="UserGameStatisticList",
        )
        return data.get("userGameStatisticList") or []

    async def get_favourite_games(self, limit: int = 50, offset: int = 0) -> List[Game]:
        """Get the casino games you marked as favourite."""
        user = await self._user_query(
            GraphQLQueries.FAVOURITE_GAMES,
            "UserFavouriteGames",
            {"limit": limit, "offset": offset},
        )
        return [
            g for g in map(_game_from_kurator, user.get("favouriteGameList") or []) if g
        ]

    async def get_recent_games(self, limit: int = 20, offset: int = 0) -> List[Game]:
        """Get the casino games you played most recently."""
        user = await self._user_query(
            GraphQLQueries.RECENT_GAMES,
            "UserRecentGameList",
            {"limit": limit, "offset": offset},
        )
        return [
            g for g in map(_game_from_kurator, user.get("recentGameList") or []) if g
        ]

    async def get_race_positions(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get your finishing positions and payouts in past and current races."""
        user = await self._user_query(
            GraphQLQueries.RACE_POSITIONS,
            "UserRacePositionList",
            {"limit": limit, "offset": offset},
        )
        return user.get("racePositionList") or []

    async def get_notifications(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get your notifications, newest first.

        Each has ``type``, ``createdAt``, ``acknowledged`` and ``data``, whose
        ``__typename`` tells what it is (e.g. "ChatTip", "WalletDeposit",
        "NotificationUserBonus", "RacePosition", "SportBet").
        """
        user = await self._user_query(
            GraphQLQueries.NOTIFICATIONS,
            "NotificationList",
            {"limit": limit, "offset": offset},
        )
        return user.get("notificationList") or []

    async def get_gambling_limits(self) -> List[Dict[str, Any]]:
        """Get the responsible-gambling limits set on your account.

        Each has type, period, value and progress.
        """
        user = await self._user_query(
            GraphQLQueries.GAMBLING_LIMITS, "ResponsibleGamblingLimitList"
        )
        return user.get("responsibleGamblingLimits") or []

    async def get_sessions(
        self, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get your login sessions (device name, IP, location, active, last seen)."""
        user = await self._user_query(
            GraphQLQueries.SESSIONS, "SessionList", {"limit": limit, "offset": offset}
        )
        return user.get("sessionList") or []
