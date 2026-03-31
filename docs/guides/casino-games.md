---
layout: default
title: Casino Games
parent: Guides
nav_order: 1
---

# Casino Games API
{: .fs-9 }

Browse, search, and analyze thousands of casino games on Stake.com.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

The Casino Games API gives you access to Stake.com's complete game library — slots, table games, live dealer games, and more. You can filter by category, provider, and analyze RTP (Return to Player) data.

## Get All Casino Games

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        games = await client.get_casino_games()
        print(f"Total games available: {len(games)}")
        
        for game in games[:10]:
            print(f"🎰 {game.name}")
            print(f"   Provider: {game.provider}")
            print(f"   Category: {game.category}")
            print(f"   Min Bet: {game.min_bet} | Max Bet: {game.max_bet}")
            if game.rtp:
                print(f"   RTP: {game.rtp}%")
            print()

asyncio.run(main())
```

## Filter by Category

Stake.com organizes games into categories. Filter to find exactly what you're looking for:

```python
async with StakeAPI(access_token="your_token") as client:
    # Get only slot games
    slots = await client.get_casino_games(category="slots")
    print(f"Slot games: {len(slots)}")
    
    # Get table games
    table_games = await client.get_casino_games(category="table-games")
    print(f"Table games: {len(table_games)}")
```

### Available Categories

| Category | Description |
|:---------|:------------|
| `slots` | Slot machines and video slots |
| `table-games` | Blackjack, roulette, baccarat, etc. |
| `live-casino` | Live dealer games with real croupiers |
| `game-shows` | Interactive game show experiences |
| `stake-originals` | Exclusive Stake.com original games |

## Get Game Details

Get detailed information about a specific game:

```python
async with StakeAPI(access_token="your_token") as client:
    game = await client.get_game_details("game_id_here")
    
    print(f"Name: {game.name}")
    print(f"Provider: {game.provider}")
    print(f"Category: {game.category}")
    print(f"Description: {game.description}")
    print(f"Min Bet: ${game.min_bet}")
    print(f"Max Bet: ${game.max_bet}")
    print(f"RTP: {game.rtp}%")
    print(f"Volatility: {game.volatility}")
    print(f"Features: {', '.join(game.features)}")
```

## Analyze Games by Provider

Find out which providers offer the most games and the best RTP:

```python
import asyncio
from collections import defaultdict
from stakeapi import StakeAPI

async def analyze_providers():
    async with StakeAPI(access_token="your_token") as client:
        games = await client.get_casino_games()
        
        providers = defaultdict(lambda: {"count": 0, "rtps": [], "categories": set()})
        
        for game in games:
            p = providers[game.provider]
            p["count"] += 1
            p["categories"].add(game.category)
            if game.rtp:
                p["rtps"].append(game.rtp)
        
        print("📊 Provider Analysis")
        print("=" * 60)
        
        for name, data in sorted(providers.items(), key=lambda x: x[1]["count"], reverse=True):
            avg_rtp = sum(data["rtps"]) / len(data["rtps"]) if data["rtps"] else 0
            print(f"\n🏢 {name}")
            print(f"   Games: {data['count']}")
            print(f"   Categories: {', '.join(data['categories'])}")
            if avg_rtp:
                print(f"   Average RTP: {avg_rtp:.2f}%")

asyncio.run(analyze_providers())
```

## Find High-RTP Games

Smart players look for games with the highest Return to Player percentage:

```python
async def find_best_rtp_games():
    async with StakeAPI(access_token="your_token") as client:
        games = await client.get_casino_games()
        
        # Filter games with RTP data and sort by RTP
        games_with_rtp = [g for g in games if g.rtp is not None]
        games_with_rtp.sort(key=lambda g: g.rtp, reverse=True)
        
        print("🎯 Top 20 Games by RTP")
        print("=" * 50)
        
        for i, game in enumerate(games_with_rtp[:20], 1):
            print(f"{i:2d}. {game.name}")
            print(f"    Provider: {game.provider} | RTP: {game.rtp}%")

asyncio.run(find_best_rtp_games())
```

## Game Search Utility

Build a custom search function to find games by name:

```python
async def search_games(query: str):
    async with StakeAPI(access_token="your_token") as client:
        all_games = await client.get_casino_games()
        
        # Case-insensitive search
        matches = [g for g in all_games if query.lower() in g.name.lower()]
        
        print(f"🔍 Search results for '{query}': {len(matches)} games")
        for game in matches:
            print(f"  - {game.name} ({game.provider}) — RTP: {game.rtp or 'N/A'}%")
        
        return matches

asyncio.run(search_games("sweet bonanza"))
```

## Using GraphQL for Casino Games

For more control, use the raw GraphQL query:

```python
from stakeapi.endpoints import GraphQLQueries

async with StakeAPI(access_token="your_token") as client:
    data = await client._graphql_request(
        query=GraphQLQueries.CASINO_GAMES,
        variables={
            "first": 20,
            "categorySlug": "slots"
        },
        operation_name="CasinoGames"
    )
    
    for edge in data.get("casinoGames", {}).get("edges", []):
        game = edge["node"]
        print(f"{game['name']} — {game['provider']['name']}")
```

## The Game Model

Every game is returned as a `Game` Pydantic model:

```python
class Game(BaseModel):
    id: str                          # Unique identifier
    name: str                        # Display name
    category: str                    # Game category
    provider: str                    # Software provider
    description: Optional[str]       # Game description
    min_bet: Decimal                 # Minimum bet amount
    max_bet: Decimal                 # Maximum bet amount
    rtp: Optional[float]             # Return to Player %
    volatility: Optional[str]        # low, medium, high
    features: List[str]              # Special features
    thumbnail_url: Optional[str]     # Thumbnail image URL
```

{% include affiliate-banner.html %}
{% include discord-cta.html %}

## Real-World Example: Casino Dashboard

Build a comprehensive casino dashboard:

```python
import asyncio
from stakeapi import StakeAPI

async def casino_dashboard():
    async with StakeAPI(access_token="your_token") as client:
        games = await client.get_casino_games()
        
        # Category breakdown
        categories = {}
        for game in games:
            categories[game.category] = categories.get(game.category, 0) + 1
        
        print("🎰 CASINO DASHBOARD")
        print("=" * 50)
        print(f"\nTotal Games: {len(games)}")
        
        print("\n📂 Games by Category:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * (count // 5)
            print(f"  {cat:20s} {count:4d} {bar}")
        
        # Provider leaderboard
        providers = {}
        for game in games:
            providers[game.provider] = providers.get(game.provider, 0) + 1
        
        print("\n🏢 Top 10 Providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider:25s} {count:4d} games")
        
        # RTP statistics
        rtps = [g.rtp for g in games if g.rtp]
        if rtps:
            print(f"\n📈 RTP Statistics:")
            print(f"  Average: {sum(rtps)/len(rtps):.2f}%")
            print(f"  Highest: {max(rtps):.2f}%")
            print(f"  Lowest:  {min(rtps):.2f}%")

asyncio.run(casino_dashboard())
```

---

{: .note }
> Explore the full Stake.com game library with your own account. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and try these examples with real data!
