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

WebSockets provide real-time, bidirectional communication with Stake.com. Use them for live game updates, bet results, balance changes, and chat messages — all pushed to you instantly without polling.

## Why WebSockets?

| Approach | Latency | Efficiency | Use Case |
|:---------|:--------|:-----------|:---------|
| REST Polling | High (1-60s) | Low | Infrequent checks |
| GraphQL Polling | Medium (1-30s) | Medium | Periodic updates |
| **WebSocket** | **Instant** (<100ms) | **High** | Live data, real-time apps |

## Basic WebSocket Connection

```python
import asyncio
import websockets
import json

async def connect_to_stake():
    uri = "wss://stake.com/_api/websocket"
    
    headers = {
        "x-access-token": "your_token_here",
        "Origin": "https://stake.com",
    }
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        print("✅ Connected to Stake.com WebSocket")
        
        # Subscribe to balance updates
        subscribe_msg = {
            "type": "subscribe",
            "channel": "user:balances"
        }
        await ws.send(json.dumps(subscribe_msg))
        
        # Listen for messages
        async for message in ws:
            data = json.loads(message)
            print(f"📩 Received: {data}")

asyncio.run(connect_to_stake())
```

## Subscribing to Channels

### Balance Updates

Get notified whenever your balance changes:

```python
async def watch_balance(ws):
    await ws.send(json.dumps({
        "type": "subscribe",
        "channel": "user:balances"
    }))
    
    async for message in ws:
        data = json.loads(message)
        if data.get("channel") == "user:balances":
            print(f"💰 Balance update: {data['payload']}")
```

### Live Game Results

Watch game results in real-time:

```python
async def watch_game_results(ws, game_slug: str):
    await ws.send(json.dumps({
        "type": "subscribe",
        "channel": f"game:{game_slug}"
    }))
    
    async for message in ws:
        data = json.loads(message)
        print(f"🎰 Game result: {data}")
```

### Sports Live Updates

Track live sports events:

```python
async def watch_live_sports(ws, event_id: str):
    await ws.send(json.dumps({
        "type": "subscribe",
        "channel": f"sports:event:{event_id}"
    }))
    
    async for message in ws:
        data = json.loads(message)
        print(f"⚽ Score update: {data}")
```

## Robust WebSocket Client

A production-ready WebSocket client with reconnection:

```python
import asyncio
import websockets
import json
import logging

logger = logging.getLogger("stake_ws")

class StakeWebSocket:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.uri = "wss://stake.com/_api/websocket"
        self.ws = None
        self.subscriptions = []
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
    
    async def connect(self):
        while True:
            try:
                headers = {
                    "x-access-token": self.access_token,
                    "Origin": "https://stake.com",
                }
                
                async with websockets.connect(
                    self.uri, 
                    extra_headers=headers,
                    ping_interval=30,
                    ping_timeout=10
                ) as ws:
                    self.ws = ws
                    self.reconnect_delay = 1  # Reset on successful connect
                    logger.info("Connected to Stake.com WebSocket")
                    
                    # Re-subscribe to channels
                    for channel in self.subscriptions:
                        await self._subscribe(channel)
                    
                    await self._listen()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            
            # Exponential backoff
            logger.info(f"Reconnecting in {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(
                self.reconnect_delay * 2, 
                self.max_reconnect_delay
            )
    
    async def _subscribe(self, channel: str):
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "subscribe",
                "channel": channel
            }))
            logger.info(f"Subscribed to {channel}")
    
    async def subscribe(self, channel: str):
        if channel not in self.subscriptions:
            self.subscriptions.append(channel)
        await self._subscribe(channel)
    
    async def _listen(self):
        async for message in self.ws:
            data = json.loads(message)
            await self.on_message(data)
    
    async def on_message(self, data: dict):
        """Override this method to handle messages."""
        print(f"Message: {data}")

# Usage:
class MyHandler(StakeWebSocket):
    async def on_message(self, data):
        channel = data.get("channel", "")
        
        if "balances" in channel:
            print(f"💰 Balance changed: {data['payload']}")
        elif "game:" in channel:
            print(f"🎰 Game update: {data['payload']}")
        else:
            print(f"📩 {data}")

async def main():
    handler = MyHandler(access_token="your_token")
    await handler.subscribe("user:balances")
    await handler.connect()

asyncio.run(main())
```

## Combining WebSocket with REST API

```python
async def live_balance_tracker():
    """Combine REST for initial state and WebSocket for live updates."""
    
    async with StakeAPI(access_token="your_token") as client:
        # Get initial balance via REST
        balance = await client.get_user_balance()
        print("Initial balance:", balance)
    
    # Then switch to WebSocket for live updates
    ws_client = StakeWebSocket(access_token="your_token")
    await ws_client.subscribe("user:balances")
    await ws_client.connect()
```

{% include affiliate-banner.html %}

---

{: .note }
> Real-time data makes all the difference. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and build live dashboards with WebSocket support.
