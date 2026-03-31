---
layout: default
title: Advanced Usage
parent: Guides
nav_order: 9
---

# Advanced Usage
{: .fs-9 }

Build analytics dashboards, automate workflows, and create powerful tools with StakeAPI.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Analytics Dashboard

Build a comprehensive analytics system that tracks your performance:

```python
import asyncio
from collections import defaultdict
from decimal import Decimal
from stakeapi import StakeAPI

class StakeAnalytics:
    """Comprehensive analytics engine for Stake.com."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    async def full_report(self):
        async with StakeAPI(access_token=self.access_token) as client:
            # Fetch all data concurrently
            balance, bets, games = await asyncio.gather(
                client.get_user_balance(),
                client.get_bet_history(limit=100),
                client.get_casino_games(),
            )
            
            self._print_balance_report(balance)
            self._print_betting_report(bets)
            self._print_game_report(games)
    
    def _print_balance_report(self, balance):
        print("\n💰 BALANCE REPORT")
        print("=" * 50)
        
        for category in ["available", "vault"]:
            non_zero = {k: v for k, v in balance[category].items() if v > 0}
            if non_zero:
                print(f"\n  {category.title()}:")
                for currency, amount in sorted(non_zero.items()):
                    print(f"    {currency.upper():8s} {amount:.8f}")
    
    def _print_betting_report(self, bets):
        if not bets:
            return
        
        total = len(bets)
        won = sum(1 for b in bets if b.status == "won")
        lost = sum(1 for b in bets if b.status == "lost")
        
        total_wagered = sum(float(b.amount) for b in bets)
        total_won = sum(float(b.potential_payout) for b in bets if b.status == "won")
        
        print("\n📊 BETTING PERFORMANCE")
        print("=" * 50)
        print(f"  Total Bets:    {total}")
        print(f"  Won:           {won} ({won/total*100:.1f}%)")
        print(f"  Lost:          {lost} ({lost/total*100:.1f}%)")
        print(f"  Total Wagered: {total_wagered:.6f}")
        print(f"  Total Won:     {total_won:.6f}")
        print(f"  Net P&L:       {total_won - total_wagered:+.6f}")
        
        if total_wagered > 0:
            roi = (total_won - total_wagered) / total_wagered * 100
            print(f"  ROI:           {roi:+.2f}%")
    
    def _print_game_report(self, games):
        print("\n🎰 GAME CATALOG")
        print("=" * 50)
        print(f"  Total Games: {len(games)}")
        
        categories = defaultdict(int)
        providers = defaultdict(int)
        
        for game in games:
            categories[game.category] += 1
            providers[game.provider] += 1
        
        print(f"\n  Categories ({len(categories)}):")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"    {cat:20s} {count:4d}")
        
        print(f"\n  Top 10 Providers:")
        for prov, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {prov:25s} {count:4d}")

# Run the analytics
async def main():
    analytics = StakeAnalytics(access_token="your_token")
    await analytics.full_report()

asyncio.run(main())
```

## Provider Analysis

Deep-dive into game providers to find the best options:

```python
async def analyze_providers():
    async with StakeAPI(access_token="your_token") as client:
        games = await client.get_casino_games()
        
        providers = defaultdict(lambda: {
            "count": 0, "categories": set(), "rtps": [],
            "min_bets": [], "max_bets": []
        })
        
        for game in games:
            p = providers[game.provider]
            p["count"] += 1
            p["categories"].add(game.category)
            if game.rtp:
                p["rtps"].append(game.rtp)
            p["min_bets"].append(float(game.min_bet))
            p["max_bets"].append(float(game.max_bet))
        
        print("🏢 PROVIDER DEEP DIVE")
        print("=" * 70)
        
        for name, data in sorted(providers.items(), key=lambda x: x[1]["count"], reverse=True)[:15]:
            avg_rtp = sum(data["rtps"]) / len(data["rtps"]) if data["rtps"] else 0
            avg_min = sum(data["min_bets"]) / len(data["min_bets"])
            avg_max = sum(data["max_bets"]) / len(data["max_bets"])
            
            print(f"\n  🏢 {name}")
            print(f"     Games: {data['count']}")
            print(f"     Categories: {', '.join(sorted(data['categories']))}")
            if avg_rtp:
                print(f"     Avg RTP: {avg_rtp:.2f}%")
            print(f"     Bet Range: ${avg_min:.2f} — ${avg_max:.2f}")

asyncio.run(analyze_providers())
```

## Value Bet Finder

Automatically find sports events with the best odds:

```python
async def find_value_bets():
    async with StakeAPI(access_token="your_token") as client:
        events = await client.get_sports_events()
        
        value_bets = []
        
        for event in events:
            if not event.odds or len(event.odds) < 2:
                continue
            
            # Calculate bookmaker margin
            total_implied = sum(1/v for v in event.odds.values() if v > 0)
            margin = (total_implied - 1) * 100
            
            if margin < 5.0:  # Less than 5% margin = good value
                value_bets.append({
                    "event": event,
                    "margin": margin,
                    "sport": event.sport,
                })
        
        value_bets.sort(key=lambda x: x["margin"])
        
        print("💎 VALUE BETS (Lowest Margins)")
        print("=" * 60)
        
        for item in value_bets[:20]:
            e = item["event"]
            print(f"\n  {e.sport.upper()} | {e.league}")
            print(f"  {e.home_team} vs {e.away_team}")
            print(f"  Margin: {item['margin']:.2f}%")
            for market, odds in e.odds.items():
                prob = (1/odds)*100
                print(f"    {market}: {odds:.2f} ({prob:.1f}%)")

asyncio.run(find_value_bets())
```

## Automated Monitoring

Create a monitoring script that runs continuously:

```python
import asyncio
from datetime import datetime

async def monitor_loop(access_token: str, interval: int = 60):
    """Continuously monitor balance and generate alerts."""
    
    previous_balance = {}
    
    while True:
        try:
            async with StakeAPI(access_token=access_token) as client:
                balance = await client.get_user_balance()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for currency, amount in balance["available"].items():
                    if amount <= 0:
                        continue
                    
                    prev = previous_balance.get(currency, amount)
                    change = amount - prev
                    
                    if change > 0:
                        print(f"[{timestamp}] 📈 {currency.upper()}: +{change:.8f} "
                              f"(now: {amount:.8f})")
                    elif change < 0:
                        print(f"[{timestamp}] 📉 {currency.upper()}: {change:.8f} "
                              f"(now: {amount:.8f})")
                
                previous_balance = balance["available"]
                
        except Exception as e:
            print(f"[{timestamp}] ❌ Error: {e}")
        
        await asyncio.sleep(interval)

asyncio.run(monitor_loop("your_token", interval=30))
```

## Export Data to CSV

Export your bet history for analysis in Excel or Google Sheets:

```python
import csv
from io import StringIO

async def export_bets_to_csv():
    async with StakeAPI(access_token="your_token") as client:
        bets = await client.get_bet_history(limit=100)
        
        with open("bet_history.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Type", "Amount", "Payout", "Odds",
                "Status", "Placed At", "Settled At"
            ])
            
            for bet in bets:
                writer.writerow([
                    bet.id,
                    bet.bet_type,
                    float(bet.amount),
                    float(bet.potential_payout),
                    bet.odds,
                    bet.status,
                    bet.placed_at.isoformat(),
                    bet.settled_at.isoformat() if bet.settled_at else "",
                ])
        
        print(f"✅ Exported {len(bets)} bets to bet_history.csv")

asyncio.run(export_bets_to_csv())
```

{% include affiliate-banner.html %}

---

{: .note }
> Build professional-grade tools and dashboards. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and unleash the full power of StakeAPI in your projects.
