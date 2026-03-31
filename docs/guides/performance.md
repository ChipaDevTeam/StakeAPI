---
layout: default
title: Performance
parent: Guides
nav_order: 11
---

# Performance Guide
{: .fs-9 }

Optimize your StakeAPI integration for maximum speed and efficiency.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Why Performance Matters

When building real-time dashboards, betting bots, or analytics tools, every millisecond counts. StakeAPI is built on async Python for exactly this reason.

## Concurrent Requests with asyncio.gather

The single most impactful optimization — run independent requests in parallel:

```python
import asyncio
from stakeapi import StakeAPI

async def fast_dashboard():
    async with StakeAPI(access_token="your_token") as client:
        # ❌ SLOW — Sequential (3 round trips)
        # balance = await client.get_user_balance()
        # games = await client.get_casino_games()
        # events = await client.get_sports_events()
        
        # ✅ FAST — Concurrent (1 round trip)
        balance, games, events = await asyncio.gather(
            client.get_user_balance(),
            client.get_casino_games(),
            client.get_sports_events(),
        )
        
        print(f"Balance: {balance}")
        print(f"Games: {len(games)}")
        print(f"Events: {len(events)}")

asyncio.run(fast_dashboard())
```

**Impact:** 3x faster for 3 concurrent requests. The speedup scales linearly.

## Session Reuse

Always reuse the same client session — creating new sessions is expensive:

```python
# ❌ SLOW — New session per request
for i in range(10):
    async with StakeAPI(access_token="token") as client:
        await client.get_user_balance()

# ✅ FAST — Reuse session
async with StakeAPI(access_token="token") as client:
    for i in range(10):
        await client.get_user_balance()
```

## Request Only What You Need

With GraphQL, you can request exactly the fields you need:

```python
# ❌ SLOW — Fetching everything
full_query = """
query {
  user {
    id
    name
    email
    country
    level
    balances {
      available { amount currency }
      vault { amount currency }
    }
    statistics { ... }
  }
}
"""

# ✅ FAST — Only fetch balance
slim_query = """
query {
  user {
    balances {
      available { amount currency }
    }
  }
}
"""
```

## Response Caching

Cache responses that don't change frequently:

```python
import time
from functools import lru_cache

class CachedStakeAPI:
    def __init__(self, client):
        self.client = client
        self._cache = {}
        self._cache_ttl = {}
    
    async def get_cached(self, key, fetcher, ttl=60):
        """Get cached result or fetch fresh data."""
        now = time.time()
        
        if key in self._cache and now < self._cache_ttl.get(key, 0):
            return self._cache[key]
        
        result = await fetcher()
        self._cache[key] = result
        self._cache_ttl[key] = now + ttl
        return result
    
    async def get_games_cached(self, category=None):
        """Casino games change infrequently — cache for 5 minutes."""
        key = f"games:{category}"
        return await self.get_cached(
            key,
            lambda: self.client.get_casino_games(category=category),
            ttl=300
        )
    
    async def get_balance_cached(self):
        """Balance changes often — cache for 10 seconds."""
        return await self.get_cached(
            "balance",
            self.client.get_user_balance,
            ttl=10
        )
```

## Connection Pooling

aiohttp handles connection pooling automatically, but you can configure it:

```python
import aiohttp

# Custom connector with connection limits
connector = aiohttp.TCPConnector(
    limit=100,          # Max connections
    limit_per_host=30,  # Max per host
    ttl_dns_cache=300,  # DNS cache TTL
    enable_cleanup_closed=True,
)

# Use custom timeout
timeout = aiohttp.ClientTimeout(
    total=30,
    connect=5,
    sock_read=10,
)
```

## Controlled Concurrency

Don't fire thousands of requests at once — use semaphores:

```python
async def batch_fetch(client, ids, max_concurrent=10):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_one(id):
        async with semaphore:
            return await client.get_game_details(id)
    
    return await asyncio.gather(*[fetch_one(id) for id in ids])
```

## Performance Benchmarks

Typical latencies for StakeAPI operations:

| Operation | Sequential | Concurrent | Improvement |
|:----------|:-----------|:-----------|:------------|
| Single balance check | ~200ms | ~200ms | — |
| 5 independent queries | ~1000ms | ~250ms | 4x |
| 10 game details | ~2000ms | ~300ms | 6.7x |
| 50 sport events | ~10s | ~1s | 10x |

## Performance Tips Summary

1. **Use `asyncio.gather()`** for independent requests
2. **Reuse sessions** — one client context for multiple requests
3. **Cache responses** that don't change frequently
4. **Request minimal data** with targeted GraphQL queries
5. **Control concurrency** with semaphores
6. **Set appropriate timeouts** — don't wait forever
7. **Use WebSockets** for real-time data instead of polling

{% include affiliate-banner.html %}

---

{: .note }
> Build the fastest Stake.com tools with StakeAPI's async architecture. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and start building today!
