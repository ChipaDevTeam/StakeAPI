"""Tests for StakeWebSocket against a local graphql-transport-ws server."""

import asyncio
import json

import pytest
from aiohttp import web

from stakeapi import StakeAPI, StakeWebSocket
from stakeapi.exceptions import GraphQLError, NetworkError, PermissionDeniedError


class FakeStakeServer:
    """Minimal graphql-ws server that mimics stake's /_api/websockets."""

    def __init__(self):
        self.init_payloads = []
        self.completed = []
        self.pongs = 0

    async def handler(self, request):
        ws = web.WebSocketResponse(protocols=("graphql-transport-ws",))
        await ws.prepare(request)
        async for msg in ws:
            message = json.loads(msg.data)
            kind = message["type"]
            if kind == "connection_init":
                self.init_payloads.append(message.get("payload"))
                await ws.send_json({"type": "connection_ack"})
                await ws.send_json({"type": "ping"})
            elif kind == "pong":
                self.pongs += 1
            elif kind == "complete":
                self.completed.append(message["id"])
            elif kind == "subscribe":
                await self.respond(ws, message["id"], message["payload"])
        return ws

    async def respond(self, ws, sub_id, payload):
        query = payload["query"]
        if "CrashMultiplier" in query:
            for multiplier in (1.0, 1.5, 2.25):
                await ws.send_json({"id": sub_id, "type": "next", "payload": {
                    "data": {"crashMultiplier": {"id": "r1", "elapsed": 100, "multiplier": multiplier}}
                }})
        elif "subscription Crash " in query:
            await ws.send_json({"id": sub_id, "type": "next", "payload": {
                "data": {"crash": {"event": {"__typename": "MultiplayerCrash", "id": "r1", "status": "ended"}}}
            }})
            await ws.send_json({"id": sub_id, "type": "complete"})
        elif "ChatMessages" in query:
            await ws.send_json({"id": sub_id, "type": "next", "payload": {
                "data": {"chatMessages": {"id": "m1", "chatId": payload["variables"]["chatId"]}}
            }})
        elif "sessionExpired" in query:
            await ws.send_json({"id": sub_id, "type": "next", "payload": {"errors": [
                {"message": "Please log in.", "errorType": "notAuthenticated"}
            ]}})
        elif "badField" in query:
            await ws.send_json({"id": sub_id, "type": "error", "payload": [
                {"message": "Cannot query field \"badField\""}
            ]})
        elif "Hangup" in query:
            await ws.close()


@pytest.fixture
async def server():
    fake = FakeStakeServer()
    app = web.Application()
    app.router.add_get("/_api/websockets", fake.handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    fake.base_url = f"http://127.0.0.1:{port}"
    yield fake
    await runner.cleanup()


@pytest.fixture
async def ws(server):
    client = StakeAPI(access_token="tok", base_url=server.base_url)
    async with client.websocket() as socket:
        yield socket
    await client.close()


def test_url_from_base_url():
    client = StakeAPI(base_url="https://stake1017.com")
    assert StakeWebSocket(client).url == "wss://stake1017.com/_api/websockets"


@pytest.mark.asyncio
async def test_handshake_sends_token_and_answers_ping(server, ws):
    assert ws.connected
    assert server.init_payloads == [{"language": "en", "accessToken": "tok"}]
    await asyncio.sleep(0.05)
    assert server.pongs == 1


@pytest.mark.asyncio
async def test_stream_yields_field_and_completes_on_break(server, ws):
    seen = []
    async for tick in ws.crash_multiplier():
        seen.append(tick["multiplier"])
        if len(seen) == 2:
            break
    assert seen == [1.0, 1.5]
    await asyncio.sleep(0.05)
    assert server.completed == ["1"]


@pytest.mark.asyncio
async def test_event_unwrapped_and_server_complete_ends_stream(ws):
    events = [e async for e in ws.crash()]
    assert events == [{"__typename": "MultiplayerCrash", "id": "r1", "status": "ended"}]


@pytest.mark.asyncio
async def test_concurrent_subscriptions_with_variables(ws):
    async def first(stream):
        async for item in stream:
            return item

    tick, message = await asyncio.wait_for(
        asyncio.gather(first(ws.crash_multiplier()), first(ws.chat_messages("room-1"))),
        timeout=2,
    )
    assert tick["multiplier"] == 1.0
    assert message["chatId"] == "room-1"


@pytest.mark.asyncio
async def test_not_authenticated_raises_permission_denied(ws):
    with pytest.raises(PermissionDeniedError):
        async for _ in ws.session_expired():
            pass


@pytest.mark.asyncio
async def test_error_message_raises_graphql_error(ws):
    with pytest.raises(GraphQLError):
        async for _ in ws.subscribe("subscription Bad { badField }"):
            pass


@pytest.mark.asyncio
async def test_server_hangup_raises_network_error(ws):
    with pytest.raises(NetworkError):
        async for _ in ws.subscribe("subscription Hangup { x }"):
            pass


@pytest.mark.asyncio
async def test_subscribe_before_connect_raises():
    socket = StakeWebSocket(StakeAPI(base_url="http://127.0.0.1:1"))
    with pytest.raises(NetworkError):
        async for _ in socket.crash_multiplier():
            pass


@pytest.mark.asyncio
async def test_connect_failure_raises_network_error():
    socket = StakeWebSocket(StakeAPI(base_url="http://127.0.0.1:1"))
    with pytest.raises(NetworkError):
        await socket.connect()
    assert not socket.connected
