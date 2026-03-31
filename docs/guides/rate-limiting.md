---
layout: default
title: Rate Limiting
parent: Guides
nav_order: 7
---

# Rate Limiting
{: .fs-9 }

Understand and work within Stake.com's API rate limits for reliable applications.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

Stake.com enforces rate limits to protect their infrastructure. Understanding these limits is essential for building reliable applications that don't get blocked.

## Rate Limit Configuration

StakeAPI lets you configure rate limiting when creating the client:

```python
from stakeapi import StakeAPI

# Default: 10 requests per second
client = StakeAPI(access_token="token", rate_limit=10)

# Conservative: 5 requests per second
client = StakeAPI(access_token="token", rate_limit=5)

# Aggressive: 20 requests per second (use with caution!)
client = StakeAPI(access_token="token", rate_limit=20)
```

## Handling Rate Limit Errors

When you exceed the rate limit, a `RateLimitError` is raised:

```python
from stakeapi.exceptions import RateLimitError
import asyncio

async def fetch_with_backoff(client, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await client.get_user_balance()
        except RateLimitError:
            wait = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
            print(f"Rate limited! Waiting {wait}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait)
    
    raise Exception("Exceeded maximum retries")
```

## Implementing a Rate Limiter

Build a custom rate limiter for more control:

```python
import asyncio
import time

class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, requests_per_second: int = 10):
        self.rate = requests_per_second
        self.tokens = requests_per_second
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_refill = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

# Usage
limiter = RateLimiter(requests_per_second=5)

async with StakeAPI(access_token="token") as client:
    for i in range(100):
        await limiter.acquire()
        balance = await client.get_user_balance()
        print(f"Request {i + 1}: OK")
```

## Batch Requests with Rate Limiting

When making many requests, use controlled concurrency:

```python
import asyncio

async def batch_fetch(client, game_ids: list, concurrency: int = 5):
    """Fetch multiple games with controlled concurrency."""
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    
    async def fetch_one(game_id):
        async with semaphore:
            try:
                game = await client.get_game_details(game_id)
                results.append(game)
            except RateLimitError:
                await asyncio.sleep(2)
                game = await client.get_game_details(game_id)
                results.append(game)
    
    await asyncio.gather(*[fetch_one(gid) for gid in game_ids])
    return results
```

## Best Practices

| Practice | Why |
|:---------|:----|
| Start with low rate limits | Increase gradually as needed |
| Use exponential backoff | Prevents overwhelming the API |
| Cache responses | Reduces unnecessary requests |
| Batch related requests | Use `asyncio.gather` wisely |
| Monitor your usage | Log request counts and timings |
| Use GraphQL efficiently | Request only needed fields |

{% include affiliate-banner.html %}

---

{: .note }
> Build efficient, rate-limit-aware applications. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and start developing your StakeAPI integration.
