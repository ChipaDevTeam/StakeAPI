---
layout: default
title: WebSockets
parent: Guides
nav_order: 8
---

# WebSocket Guide
{: .fs-9 }

Connect to Stake.com's real-time data streams for live updates and instant notifications.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

Stake pushes live data over a GraphQL WebSocket at `wss://<domain>/_api/websockets`, using the standard [graphql-ws](https://github.com/enisdenjo/graphql-ws) protocol (`graphql-transport-ws`). `StakeWebSocket` handles the connection, keep-alive pings, and running many subscriptions over one socket.

Most feeds are public, so no login is needed. The connection still has to pass Cloudflare, so give the client the same cookies you use for normal requests.

## Quick start

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(base_url="https://stake1017.com", cookie_file="cookie.txt") as client:
        async with client.websocket() as ws:
            async for tick in ws.crash_multiplier():
                print(f"{tick['multiplier']:.2f}x")

asyncio.run(main())
```

`client.websocket()` reuses the client's `base_url`, cookies, User-Agent and access token. Each stream is an async iterator. Leaving the `async for` loop (with `break`, `return` or an exception) unsubscribes on the server.

## Available streams

| Method | Yields | Login |
|:-------|:-------|:------|
| `crash()` | Crash round state (`__typename == "MultiplayerCrash"`) and player bets/cashouts (`"MultiplayerCrashBet"`) | No |
| `crash_multiplier()` | `{"id", "elapsed", "multiplier"}` ticks for the running round | No |
| `slide()` | Slide round (`"MultiplayerSlide"`) and bet (`"MultiplayerSlideBet"`) events | No |
| `all_house_bets()` | Every public casino bet as it settles | No |
| `highroller_bets()` | High-roller casino bets | No |
| `all_sport_bets()` | Public sports bets as they are placed | No |
| `sport_market(market_id, provider)` | A market with its outcomes each time the odds change | No |
| `sport_fixture(fixture_id, provider)` | A fixture each time its status or score changes | No |
| `race_status()` | Race start/end/status changes | No |
| `race_leaderboard(race_id, limit=10)` | Leaderboard updates for one race | No |
| `chat_messages(chat_id)` | Messages in a public chat room | No |
| `session_expired()` | Fires when your session expires | Yes |

Streams that need a login raise `PermissionDeniedError`. A rejected subscription raises `GraphQLError`, and a dropped connection raises `NetworkError` in every open stream.

## Several streams at once

One connection can carry any number of subscriptions. Run each one in its own task:

```python
async def watch_crash(ws):
    async for event in ws.crash():
        # Round statuses: pending, starting, start, in_progress, crash
        if event["__typename"] == "MultiplayerCrash" and event["status"] == "crash":
            print(f"Crashed at {event['multiplier']:.2f}x")

async def watch_highrollers(ws):
    async for bet in ws.highroller_bets():
        inner = bet["bet"]
        print(f"{bet['game']['name']}: {inner['amount']} {inner['currency']}")

async with client.websocket() as ws:
    await asyncio.gather(watch_crash(ws), watch_highrollers(ws))
```

## Live odds for a match

Take the market id and provider from any fixture returned by the sports methods:

```python
fixtures = (await client.get_fixtures(search_type="live", limit=1))["fixtures"]
fixture = fixtures[0]
market = fixture["groups"][0]["templates"][0]["markets"][0]

async with client.websocket() as ws:
    async for update in ws.sport_market(market["id"], fixture["provider"]):
        odds = {o["name"]: o["odds"] for o in update["outcomes"]}
        print(update["status"], odds)
```

## Chat

```python
chats = await client.get_public_chats()           # [{"id", "name": "en", ...}, ...]
english = next(c for c in chats if c["name"] == "en")

async with client.websocket() as ws:
    async for message in ws.chat_messages(english["id"]):
        text = message["data"].get("message")
        if text:
            print(f"{message['user']['name']}: {text}")
```

## Custom subscriptions

`subscribe()` runs any GraphQL subscription and yields its `data` payloads:

```python
query = "subscription CrashMultiplier { crashMultiplier { multiplier } }"
async for data in ws.subscribe(query):
    print(data["crashMultiplier"]["multiplier"])
```

## Reconnecting

`StakeWebSocket` does not reconnect by itself. Wrap your loop to reconnect after a `NetworkError`:

```python
from stakeapi.exceptions import NetworkError

while True:
    try:
        async with client.websocket() as ws:
            async for tick in ws.crash_multiplier():
                print(tick["multiplier"])
    except NetworkError as e:
        print(f"Disconnected ({e}), retrying in 5s")
        await asyncio.sleep(5)
```
