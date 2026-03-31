---
layout: default
title: Quick Start
parent: Getting Started
nav_order: 3
---

# Quick Start
{: .fs-9 }

Go from zero to your first API call in under 60 seconds.
{: .fs-6 .fw-300 }

---

## Prerequisites

Before continuing, make sure you have:

- [x] Python 3.8+ installed
- [x] StakeAPI installed (`pip install stakeapi`)
- [x] A [Stake.com account](https://stake.com/?c=WY7953wQ) with an access token

{% include affiliate-cta.html %}

## Your First Script

Create a file called `my_first_script.py`:

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    # Replace with your actual access token
    async with StakeAPI(access_token="your_access_token_here") as client:
        
        # 1. Get your balance
        balance = await client.get_user_balance()
        print("💰 Your Balance:")
        for currency, amount in balance["available"].items():
            if amount > 0:
                print(f"  {currency.upper()}: {amount}")
        
        # 2. Browse casino games
        games = await client.get_casino_games(category="slots")
        print(f"\n🎰 Found {len(games)} slot games!")
        for game in games[:5]:
            print(f"  - {game.name} by {game.provider}")
        
        # 3. Check sports events
        events = await client.get_sports_events(sport="football")
        print(f"\n⚽ Found {len(events)} football events!")
        for event in events[:3]:
            print(f"  - {event.home_team} vs {event.away_team}")

asyncio.run(main())
```

Run it:

```bash
python my_first_script.py
```

## Using Environment Variables

For a production-ready setup, use environment variables instead of hardcoding tokens:

```python
import asyncio
import os
from dotenv import load_dotenv
from stakeapi import StakeAPI

load_dotenv()  # Load from .env file

async def main():
    token = os.getenv("STAKE_ACCESS_TOKEN")
    if not token:
        print("Set STAKE_ACCESS_TOKEN environment variable!")
        return
    
    async with StakeAPI(access_token=token) as client:
        balance = await client.get_user_balance()
        print(balance)

asyncio.run(main())
```

## Understanding the Async Pattern

StakeAPI is built with `async/await` for maximum performance. Here's why:

```python
# ✅ CORRECT — Using async context manager
async with StakeAPI(access_token=token) as client:
    result = await client.get_user_balance()

# ✅ CORRECT — Manual session management
client = StakeAPI(access_token=token)
await client._create_session()
try:
    result = await client.get_user_balance()
finally:
    await client.close()

# ❌ WRONG — Forgetting to await
async with StakeAPI(access_token=token) as client:
    result = client.get_user_balance()  # This returns a coroutine, not the result!
```

## Multiple Concurrent Requests

One of the biggest advantages of async is making multiple requests simultaneously:

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        # Run 3 requests at the same time!
        balance, games, events = await asyncio.gather(
            client.get_user_balance(),
            client.get_casino_games(),
            client.get_sports_events(),
        )
        
        print(f"Balance: {balance}")
        print(f"Games: {len(games)}")
        print(f"Events: {len(events)}")

asyncio.run(main())
```

## Error Handling

Always handle errors in production code:

```python
import asyncio
from stakeapi import StakeAPI
from stakeapi.exceptions import (
    StakeAPIError,
    AuthenticationError,
    RateLimitError,
)

async def main():
    async with StakeAPI(access_token="your_token") as client:
        try:
            balance = await client.get_user_balance()
            print(balance)
        except AuthenticationError:
            print("Invalid or expired token. Get a new one from stake.com")
        except RateLimitError:
            print("Too many requests. Wait a moment and try again.")
        except StakeAPIError as e:
            print(f"API error: {e}")

asyncio.run(main())
```

{% include affiliate-banner.html %}

## What's Next?

Now that you've made your first API call, explore the full power of StakeAPI:

| Guide | Description |
|:------|:------------|
| [Casino Games]({% link guides/casino-games.md %}) | Browse and analyze casino games |
| [Sports Betting]({% link guides/sports-betting.md %}) | Access sports events and odds |
| [User Account]({% link guides/user-account.md %}) | Manage your profile and balance |
| [Betting API]({% link guides/betting.md %}) | Place bets and track history |
| [Advanced Usage]({% link guides/advanced-usage.md %}) | Build analytics and automation tools |
| [API Reference]({% link api-reference/client.md %}) | Complete method documentation |

---

{: .highlight }
> **Pro tip:** Combine StakeAPI with data visualization libraries like `matplotlib` or `plotly` to create stunning dashboards of your Stake.com activity. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) to get started!
