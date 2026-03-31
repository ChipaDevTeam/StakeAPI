---
layout: default
title: Examples
parent: Resources
nav_order: 1
---

# Code Examples
{: .fs-9 }

Complete, ready-to-run examples for every feature of StakeAPI.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Basic: Check Your Balance

The simplest possible StakeAPI script:

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        balance = await client.get_user_balance()
        
        print("Available:")
        for currency, amount in balance["available"].items():
            if amount > 0:
                print(f"  {currency.upper()}: {amount}")

asyncio.run(main())
```

## Basic: Get User Profile

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        user = await client.get_user_profile()
        print(f"Username: {user.username}")
        print(f"Verified: {user.verified}")
        print(f"Currency: {user.currency}")
        print(f"Member since: {user.created_at}")

asyncio.run(main())
```

## Basic: Browse Casino Games

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        # Get slot games
        slots = await client.get_casino_games(category="slots")
        print(f"Found {len(slots)} slot games\n")
        
        for game in slots[:10]:
            rtp_str = f"RTP: {game.rtp}%" if game.rtp else "RTP: N/A"
            print(f"  {game.name} ({game.provider}) — {rtp_str}")

asyncio.run(main())
```

## Basic: Sports Events

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        events = await client.get_sports_events(sport="football")
        
        for event in events[:10]:
            status = "🔴 LIVE" if event.live else "⏳ Upcoming"
            print(f"  {event.home_team} vs {event.away_team} [{status}]")
            print(f"    League: {event.league}")
            if event.odds:
                for market, odds in event.odds.items():
                    print(f"    {market}: {odds}")
            print()

asyncio.run(main())
```

## Intermediate: Extract Token from cURL

```python
from stakeapi.auth import AuthManager

curl_command = '''
curl "https://stake.com/_api/graphql" \
  -H "x-access-token: your_token_here" \
  -b "session=your_session_here"
'''

token = AuthManager.extract_access_token_from_curl(curl_command)
session = AuthManager.extract_session_from_curl(curl_command)

print(f"Token: {token}")
print(f"Session: {session}")
```

## Intermediate: Concurrent Data Fetching

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        # Fetch everything at once
        balance, games, events, bets = await asyncio.gather(
            client.get_user_balance(),
            client.get_casino_games(),
            client.get_sports_events(),
            client.get_bet_history(limit=20),
        )
        
        print(f"Balance currencies: {len(balance['available'])}")
        print(f"Casino games: {len(games)}")
        print(f"Sports events: {len(events)}")
        print(f"Recent bets: {len(bets)}")

asyncio.run(main())
```

## Intermediate: Game Provider Analysis

```python
import asyncio
from collections import Counter
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        games = await client.get_casino_games()
        
        providers = Counter(g.provider for g in games)
        categories = Counter(g.category for g in games)
        
        print("Top Providers:")
        for provider, count in providers.most_common(10):
            print(f"  {provider}: {count} games")
        
        print("\nCategories:")
        for category, count in categories.most_common():
            print(f"  {category}: {count} games")

asyncio.run(main())
```

## Advanced: Betting Performance Report

```python
import asyncio
from decimal import Decimal
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        bets = await client.get_bet_history(limit=100)
        
        if not bets:
            print("No bets found")
            return
        
        won = [b for b in bets if b.status == "won"]
        lost = [b for b in bets if b.status == "lost"]
        
        total_wagered = sum(float(b.amount) for b in bets)
        total_won = sum(float(b.potential_payout) for b in won)
        
        print("PERFORMANCE REPORT")
        print("=" * 40)
        print(f"Total Bets:     {len(bets)}")
        print(f"Won:            {len(won)}")
        print(f"Lost:           {len(lost)}")
        print(f"Win Rate:       {len(won)/len(bets)*100:.1f}%")
        print(f"Total Wagered:  {total_wagered:.6f}")
        print(f"Total Won:      {total_won:.6f}")
        print(f"Net P&L:        {total_won - total_wagered:+.6f}")

asyncio.run(main())
```

## Advanced: Balance Monitor with Alerts

```python
import asyncio
from datetime import datetime
from stakeapi import StakeAPI

async def monitor(token: str, check_interval: int = 30):
    prev = {}
    
    while True:
        try:
            async with StakeAPI(access_token=token) as client:
                balance = await client.get_user_balance()
                now = datetime.now().strftime("%H:%M:%S")
                
                for cur, amt in balance["available"].items():
                    if amt <= 0:
                        continue
                    
                    old = prev.get(cur, amt)
                    diff = amt - old
                    
                    if diff > 0:
                        print(f"[{now}] 📈 {cur.upper()}: +{diff:.8f}")
                    elif diff < 0:
                        print(f"[{now}] 📉 {cur.upper()}: {diff:.8f}")
                
                prev = {k: v for k, v in balance["available"].items() if v > 0}
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(check_interval)

asyncio.run(monitor("your_token"))
```

## Advanced: Export to CSV

```python
import asyncio
import csv
from stakeapi import StakeAPI

async def export_bets():
    async with StakeAPI(access_token="your_token") as client:
        bets = await client.get_bet_history(limit=100)
        
        with open("bets.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ID", "Type", "Amount", "Payout", "Status", "Date"])
            
            for b in bets:
                w.writerow([
                    b.id, b.bet_type, float(b.amount),
                    float(b.potential_payout), b.status,
                    b.placed_at.isoformat()
                ])
        
        print(f"Exported {len(bets)} bets to bets.csv")

asyncio.run(export_bets())
```

## Advanced: Custom GraphQL Query

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        query = """
        query {
          user {
            id
            name
            balances {
              available {
                amount
                currency
              }
            }
          }
        }
        """
        
        data = await client._graphql_request(query=query)
        print(data)

asyncio.run(main())
```

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

{: .note }
> All examples require a [Stake.com account](https://stake.com/?c=WY7953wQ) and access token. Sign up now to get started!
