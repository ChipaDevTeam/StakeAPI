"""Live data over stake's GraphQL WebSocket (/_api/websockets)."""

import asyncio
import itertools
import json
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING

import aiohttp

from .endpoints import GraphQLSubscriptions
from .exceptions import GraphQLError, NetworkError, PermissionDeniedError, StakeAPIError

if TYPE_CHECKING:
    from .client import StakeAPI

# The site speaks the graphql-ws protocol (https://github.com/enisdenjo/graphql-ws)
PROTOCOL = "graphql-transport-ws"

# Sentinel pushed to a subscription's queue when the server completes it
_COMPLETE = object()


class StakeWebSocket:
    """
    Subscribe to live stake.com data: crash and slide rounds, bet feeds,
    sports odds and scores, races and chat.

    One connection carries any number of subscriptions. Each subscription is
    an async iterator that yields the subscription's ``data`` payloads.

    Example:
        async with StakeAPI(cookie_file="cookie.txt") as client:
            async with client.websocket() as ws:
                async for point in ws.crash_multiplier():
                    print(point["multiplier"])
    """

    def __init__(self, client: "StakeAPI", language: str = "en"):
        """
        Args:
            client: The StakeAPI client whose base_url, cookies and access
                token are reused for the connection.
            language: Language sent in the connection params.
        """
        self._client = client
        self._language = language
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._reader: Optional[asyncio.Task] = None
        self._queues: Dict[str, asyncio.Queue] = {}
        self._ids = itertools.count(1)

    @property
    def url(self) -> str:
        """WebSocket URL derived from the client's base_url."""
        base = self._client.base_url.rstrip("/")
        return base.replace("https://", "wss://", 1).replace("http://", "ws://", 1) + "/_api/websockets"

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self, ack_timeout: float = 10.0):
        """
        Open the connection and complete the graphql-ws handshake.

        Raises:
            NetworkError: If the connection fails or is not acknowledged.
        """
        if self.connected:
            return
        headers, cookies = self._client._session_headers()
        # Content-Type is meaningless for a WebSocket upgrade
        headers.pop("Content-Type", None)
        # No total timeout: the connection is meant to stay open
        self._session = aiohttp.ClientSession(headers=headers, cookies=cookies or None)
        try:
            self._ws = await self._session.ws_connect(
                self.url, protocols=(PROTOCOL,), heartbeat=None
            )
            params: Dict[str, Any] = {"language": self._language}
            if self._client.access_token:
                params["accessToken"] = self._client.access_token
            await self._ws.send_json({"type": "connection_init", "payload": params})
            ack = await self._ws.receive(timeout=ack_timeout)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            await self.close()
            raise NetworkError(
                f"Could not open WebSocket to {self.url}: {e}. If this is a 403, "
                "your Cloudflare cookies (cf_clearance) are missing, expired, or "
                "from a different domain than base_url."
            )

        message = _parse(ack)
        if not message or message.get("type") != "connection_ack":
            await self.close()
            raise NetworkError(f"WebSocket handshake was not acknowledged: {ack.data!r}")

        self._reader = asyncio.create_task(self._read_loop())

    async def close(self):
        """Close the connection and end every open subscription."""
        if self._reader:
            self._reader.cancel()
            try:
                await self._reader
            except (asyncio.CancelledError, Exception):
                pass
            self._reader = None
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None
        if self._session:
            await self._session.close()
            self._session = None
        self._fail_all(NetworkError("WebSocket connection closed"))

    async def subscribe(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run any GraphQL subscription and yield each ``data`` payload.

        Leaving the ``async for`` loop (break, return or an exception) stops
        the subscription on the server.

        Raises:
            PermissionDeniedError: The subscription needs a logged-in account.
            GraphQLError: The server rejected the subscription.
            NetworkError: The connection dropped.
        """
        if not self.connected:
            raise NetworkError("WebSocket is not connected — call connect() first")

        sub_id = str(next(self._ids))
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[sub_id] = queue
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        await self._ws.send_json({"id": sub_id, "type": "subscribe", "payload": payload})

        try:
            while True:
                item = await queue.get()
                if item is _COMPLETE:
                    return
                if isinstance(item, Exception):
                    raise item
                yield item
        finally:
            self._queues.pop(sub_id, None)
            if self.connected:
                try:
                    await self._ws.send_json({"id": sub_id, "type": "complete"})
                except (aiohttp.ClientError, ConnectionError, RuntimeError):
                    pass

    async def _read_loop(self):
        error: Exception = NetworkError("WebSocket connection closed by server")
        try:
            async for msg in self._ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        error = NetworkError(f"WebSocket error: {self._ws.exception()}")
                    continue
                message = _parse(msg)
                if message:
                    await self._dispatch(message)
            if self._ws.close_code not in (None, 1000):
                error = NetworkError(f"WebSocket closed with code {self._ws.close_code}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error = NetworkError(f"WebSocket read failed: {e}")
        self._fail_all(error)

    async def _dispatch(self, message: Dict[str, Any]):
        kind = message.get("type")
        if kind == "ping":
            await self._ws.send_json({"type": "pong"})
            return
        queue = self._queues.get(message.get("id"))
        if queue is None:
            return
        payload = message.get("payload")
        if kind == "next":
            errors = (payload or {}).get("errors")
            queue.put_nowait(_subscription_error(errors) if errors else (payload or {}).get("data") or {})
        elif kind == "error":
            queue.put_nowait(_subscription_error(payload if isinstance(payload, list) else [payload]))
        elif kind == "complete":
            queue.put_nowait(_COMPLETE)

    def _fail_all(self, error: Exception):
        for queue in self._queues.values():
            queue.put_nowait(error)

    async def _field(
        self, query: str, field: str, variables: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Any]:
        """Subscribe and yield just one top-level field of each payload."""
        async for data in self.subscribe(query, variables):
            yield data.get(field)

    # Casino games
    def crash(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Crash round and bet events. Each item has ``__typename``
        "MultiplayerCrash" (round state) or "MultiplayerCrashBet" (a player's
        bet or cashout). Round status goes pending → starting → start →
        in_progress → crash; on "crash", ``multiplier`` is the final value
        (``crashpoint`` stays null on the live stream).
        """
        return self._unwrap_event(GraphQLSubscriptions.CRASH, "crash")

    def crash_multiplier(self) -> AsyncIterator[Dict[str, Any]]:
        """Crash multiplier ticks: {"id", "elapsed" (ms), "multiplier"}."""
        return self._field(GraphQLSubscriptions.CRASH_MULTIPLIER, "crashMultiplier")

    def slide(self) -> AsyncIterator[Dict[str, Any]]:
        """Slide round ("MultiplayerSlide") and bet ("MultiplayerSlideBet") events."""
        return self._unwrap_event(GraphQLSubscriptions.SLIDE, "slide")

    # Bet feeds
    def all_house_bets(self) -> AsyncIterator[Dict[str, Any]]:
        """Every public casino bet as it settles (same shape as AllHouseBets)."""
        return self._field(GraphQLSubscriptions.ALL_HOUSE_BETS, "allHouseBets")

    def highroller_bets(self) -> AsyncIterator[Dict[str, Any]]:
        """High-roller casino bets as they settle."""
        return self._field(GraphQLSubscriptions.HIGHROLLER_HOUSE_BETS, "highrollerHouseBets")

    def all_sport_bets(self) -> AsyncIterator[Dict[str, Any]]:
        """Public sports bets as they are placed."""
        return self._field(GraphQLSubscriptions.ALL_SPORT_BETS, "allSportBets")

    # Sports
    def sport_market(self, market_id: str, provider: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Live odds for one market. Yields the market each time it changes.

        Args:
            market_id: Market ``id`` from any fixture's ``groups`` data
            provider: The fixture's ``provider``, e.g. "betradar" or "oddin"
        """
        return self._field(
            GraphQLSubscriptions.SPORT_MARKET,
            "sportMarket",
            {"marketId": market_id, "provider": provider},
        )

    def sport_fixture(self, fixture_id: str, provider: str) -> AsyncIterator[Dict[str, Any]]:
        """Live status and score for one fixture. Yields it each time it changes."""
        return self._field(
            GraphQLSubscriptions.SPORT_FIXTURE,
            "sportFixture",
            {"fixtureId": fixture_id, "provider": provider},
        )

    # Promotions and chat
    def race_status(self) -> AsyncIterator[Dict[str, Any]]:
        """Race start, end and status changes."""
        return self._field(GraphQLSubscriptions.RACE_STATUS, "raceStatus")

    def race_leaderboard(self, race_id: str, limit: int = 10) -> AsyncIterator[Dict[str, Any]]:
        """Leaderboard updates for one race (ids from get_active_races)."""
        return self._field(
            GraphQLSubscriptions.RACE_LEADERBOARD, "race", {"raceId": race_id, "limit": limit}
        )

    def chat_messages(self, chat_id: str) -> AsyncIterator[Dict[str, Any]]:
        """Messages in a public chat room (ids from StakeAPI.get_public_chats)."""
        return self._field(
            GraphQLSubscriptions.CHAT_MESSAGES, "chatMessages", {"chatId": chat_id}
        )

    def session_expired(self) -> AsyncIterator[Dict[str, Any]]:
        """Fires when the logged-in session expires. Requires an access token."""
        return self._field(GraphQLSubscriptions.SESSION_EXPIRED, "sessionExpired")

    async def _unwrap_event(self, query: str, field: str) -> AsyncIterator[Dict[str, Any]]:
        async for data in self.subscribe(query):
            event = (data.get(field) or {}).get("event")
            if event:
                yield event


def _parse(msg: aiohttp.WSMessage) -> Optional[Dict[str, Any]]:
    if msg.type != aiohttp.WSMsgType.TEXT:
        return None
    try:
        message = json.loads(msg.data)
    except (TypeError, ValueError):
        return None
    return message if isinstance(message, dict) else None


def _subscription_error(errors: List[Dict[str, Any]]) -> StakeAPIError:
    errors = [e for e in errors if isinstance(e, dict)] or [{"message": "Unknown error"}]
    joined = ", ".join(e.get("message", "Unknown error") for e in errors)
    if any(e.get("errorType") == "notAuthenticated" for e in errors):
        return PermissionDeniedError(
            f"Subscription needs a logged-in account: {joined}", errors=errors
        )
    return GraphQLError(f"Subscription error: {joined}", errors=errors)
