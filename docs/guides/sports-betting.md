---
layout: default
title: Sports Betting
parent: Guides
nav_order: 2
---

# Sports Betting API
{: .fs-9 }

Access live sports events, odds, leagues, and markets from Stake.com's sportsbook.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

Stake.com is one of the world's largest crypto sportsbooks. The Sports Betting API gives you access to thousands of events across dozens of sports, with real-time odds and market data.

## Get Sports Events

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        # Get all upcoming events
        events = await client.get_sports_events()
        print(f"Total events: {len(events)}")
        
        for event in events[:10]:
            print(f"\n⚽ {event.home_team} vs {event.away_team}")
            print(f"   Sport: {event.sport}")
            print(f"   League: {event.league}")
            print(f"   Start: {event.start_time}")
            print(f"   Status: {event.status}")
            print(f"   Live: {'🔴 LIVE' if event.live else '⏳ Upcoming'}")
            
            if event.odds:
                print(f"   Odds:")
                for market, odds in event.odds.items():
                    print(f"     {market}: {odds}")

asyncio.run(main())
```

## Filter by Sport

Get events for specific sports:

```python
async with StakeAPI(access_token="your_token") as client:
    # Football/Soccer
    football = await client.get_sports_events(sport="football")
    print(f"Football events: {len(football)}")
    
    # Basketball
    basketball = await client.get_sports_events(sport="basketball")
    print(f"Basketball events: {len(basketball)}")
    
    # Tennis
    tennis = await client.get_sports_events(sport="tennis")
    print(f"Tennis events: {len(tennis)}")
```

### Supported Sports

| Sport | Slug | Description |
|:------|:-----|:------------|
| Football/Soccer | `football` | World's most popular sport |
| Basketball | `basketball` | NBA, EuroLeague, and more |
| Tennis | `tennis` | Grand Slams, ATP, WTA |
| American Football | `american-football` | NFL, College Football |
| Baseball | `baseball` | MLB, NPB |
| Ice Hockey | `ice-hockey` | NHL, KHL |
| MMA/UFC | `mma` | Mixed martial arts |
| Boxing | `boxing` | Professional boxing |
| Cricket | `cricket` | IPL, international cricket |
| Esports | `esports` | CS2, Dota 2, League of Legends |
| Table Tennis | `table-tennis` | Professional table tennis |
| Volleyball | `volleyball` | Indoor and beach volleyball |

## Using GraphQL for Sports Data

For more detailed results, use the GraphQL API directly:

```python
from stakeapi.endpoints import GraphQLQueries

async with StakeAPI(access_token="your_token") as client:
    data = await client._graphql_request(
        query=GraphQLQueries.SPORTS_EVENTS,
        variables={
            "first": 50,
            "sportSlug": "football"
        },
        operation_name="SportsEvents"
    )
    
    for edge in data.get("sportsEvents", {}).get("edges", []):
        event = edge["node"]
        competitors = [c["name"] for c in event.get("competitors", [])]
        print(f"{' vs '.join(competitors)}")
        print(f"  League: {event['league']['name']}")
        print(f"  Start: {event['startTime']}")
        
        # Show markets and odds
        for market in event.get("markets", []):
            print(f"  Market: {market['name']}")
            for outcome in market.get("outcomes", []):
                print(f"    {outcome['name']}: {outcome['odds']}")
```

## Odds Analysis

Build tools to analyze odds and find value:

```python
async def analyze_odds():
    async with StakeAPI(access_token="your_token") as client:
        events = await client.get_sports_events(sport="football")
        
        print("📊 ODDS ANALYSIS")
        print("=" * 60)
        
        for event in events:
            if not event.odds:
                continue
            
            home_odds = event.odds.get("home")
            away_odds = event.odds.get("away")
            draw_odds = event.odds.get("draw")
            
            if home_odds and away_odds:
                # Calculate implied probabilities
                home_prob = (1 / home_odds) * 100
                away_prob = (1 / away_odds) * 100
                draw_prob = (1 / draw_odds) * 100 if draw_odds else 0
                
                total_prob = home_prob + away_prob + draw_prob
                margin = total_prob - 100  # Bookmaker margin
                
                print(f"\n{event.home_team} vs {event.away_team}")
                print(f"  Home: {home_odds:.2f} ({home_prob:.1f}%)")
                print(f"  Away: {away_odds:.2f} ({away_prob:.1f}%)")
                if draw_odds:
                    print(f"  Draw: {draw_odds:.2f} ({draw_prob:.1f}%)")
                print(f"  Margin: {margin:.2f}%")

asyncio.run(analyze_odds())
```

## Live Events

Filter for currently live events:

```python
async def get_live_events():
    async with StakeAPI(access_token="your_token") as client:
        all_events = await client.get_sports_events()
        
        live_events = [e for e in all_events if e.live]
        
        print(f"🔴 LIVE EVENTS ({len(live_events)})")
        print("=" * 50)
        
        for event in live_events:
            print(f"\n  {event.sport.upper()} | {event.league}")
            print(f"  {event.home_team} vs {event.away_team}")
            if event.odds:
                odds_str = " | ".join(f"{k}: {v}" for k, v in event.odds.items())
                print(f"  Odds: {odds_str}")

asyncio.run(get_live_events())
```

## Value Bet Finder

Find events where the bookmaker margin is lowest (best value for bettors):

```python
async def find_value_bets():
    async with StakeAPI(access_token="your_token") as client:
        events = await client.get_sports_events()
        
        value_events = []
        
        for event in events:
            if not event.odds or "home" not in event.odds or "away" not in event.odds:
                continue
            
            total_implied = sum(1/v for v in event.odds.values() if v > 0)
            margin = (total_implied - 1) * 100
            
            value_events.append({
                "event": event,
                "margin": margin
            })
        
        # Sort by lowest margin (best value)
        value_events.sort(key=lambda x: x["margin"])
        
        print("💎 BEST VALUE BETS (Lowest Margins)")
        print("=" * 60)
        
        for item in value_events[:15]:
            event = item["event"]
            print(f"\n  {event.home_team} vs {event.away_team}")
            print(f"  {event.sport} | {event.league}")
            print(f"  Margin: {item['margin']:.2f}%")

asyncio.run(find_value_bets())
```

## The SportEvent Model

```python
class SportEvent(BaseModel):
    id: str                        # Unique identifier
    sport: str                     # Sport type
    league: str                    # League/competition name
    home_team: str                 # Home team name
    away_team: str                 # Away team name
    start_time: datetime           # Event start time
    status: str                    # Event status
    odds: Dict[str, float]         # Market odds
    live: bool                     # Whether currently live
```

{% include affiliate-banner.html %}

## Real-World Example: Sports Dashboard

```python
import asyncio
from collections import Counter
from stakeapi import StakeAPI

async def sports_dashboard():
    async with StakeAPI(access_token="your_token") as client:
        events = await client.get_sports_events()
        
        print("🏈 SPORTS DASHBOARD")
        print("=" * 60)
        print(f"Total Events: {len(events)}")
        
        # Events by sport
        sports = Counter(e.sport for e in events)
        print("\n📊 Events by Sport:")
        for sport, count in sports.most_common():
            bar = "█" * (count // 2)
            print(f"  {sport:20s} {count:4d} {bar}")
        
        # Live vs upcoming
        live = sum(1 for e in events if e.live)
        upcoming = len(events) - live
        print(f"\n🔴 Live: {live}")
        print(f"⏳ Upcoming: {upcoming}")
        
        # Top leagues
        leagues = Counter(e.league for e in events)
        print("\n🏆 Top 10 Leagues:")
        for league, count in leagues.most_common(10):
            print(f"  {league:30s} {count:4d} events")

asyncio.run(sports_dashboard())
```

---

{: .note }
> Access thousands of live sports events with real odds data. [Create your Stake.com account](https://stake.com/?c=WY7953wQ) and start building your sports analytics tools today!
