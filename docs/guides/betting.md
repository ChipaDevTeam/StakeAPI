---
layout: default
title: Betting
parent: Guides
nav_order: 4
---

# Betting API
{: .fs-9 }

Place bets, track your history, and manage your wagers programmatically.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

Stake has no single "place bet" endpoint. Each game has its own call: Stake Originals such as Dice use REST endpoints under `/_api/casino/`, while Crash, Slide, Flip, Zoo and sports bets use GraphQL mutations. StakeAPI has a method for each. See [Betting Methods](../api-reference/client.md#betting-methods) for the full list.

{: .warning }
> **Responsible Gambling:** Always gamble responsibly. Set limits and never bet more than you can afford to lose. StakeAPI is a tool — use it wisely.

{: .warning }
> **Unvalidated.** The betting methods have never been run against the live site. Use `dry_run=True` first, then the smallest amount you can.

## Turning betting on

Betting is off by default, so a script cannot place a bet by accident. Pass `allow_betting=True` to enable it:

```python
client = StakeAPI(cookie_file="cookie.txt", allow_betting=True)
```

Without it, every bet method raises `BettingDisabledError`.

## Dry runs

`dry_run=True` returns the request that would be sent, without sending it. This works even when betting is disabled:

```python
async with StakeAPI(cookie_file="cookie.txt") as client:
    print(await client.crash_bet(0.0001, "btc", cashout_at=2.0, dry_run=True))
    # {'dry_run': True, 'endpoint': '/_api/graphql',
    #  'operation_name': 'MultiplayerCrashBet',
    #  'variables': {'amount': 0.0001, 'currency': 'btc', 'cashoutAt': 2.0}}
```

## Place a Bet

```python
import asyncio
from stakeapi import StakeAPI

async def roll_dice():
    async with StakeAPI(cookie_file="cookie.txt", allow_betting=True) as client:
        result = await client.dice_roll(0.00000100, "btc", target=50.5, condition="above")
        print(f"Payout: {result['payout']} ({result['payoutMultiplier']}x)")

asyncio.run(roll_dice())
```

For other Stake Originals, copy the request body from your browser (DevTools → Network → the request to `/_api/casino/<game>/...`) and send it with `casino_bet()`:

```python
result = await client.casino_bet("limbo/bet", {
    "amount": 0.00000100,
    "currency": "btc",
    # ...the other fields exactly as the site sends them
})
```

## Get Bet History

Retrieve your recent bets with full details:

```python
async def view_bet_history():
    async with StakeAPI(access_token="your_token") as client:
        bets = await client.get_bet_history(limit=50)
        
        print(f"📋 BET HISTORY ({len(bets)} bets)")
        print("=" * 70)
        
        for bet in bets:
            status_icon = {
                "won": "🟢",
                "lost": "🔴",
                "pending": "🟡",
                "cancelled": "⚪"
            }.get(bet.status, "❓")
            
            print(f"\n{status_icon} Bet #{bet.id}")
            print(f"   Amount: {bet.amount}")
            print(f"   Payout: {bet.potential_payout}")
            print(f"   Status: {bet.status}")
            print(f"   Placed: {bet.placed_at}")
            if bet.settled_at:
                print(f"   Settled: {bet.settled_at}")
            if bet.odds:
                print(f"   Odds: {bet.odds}")

asyncio.run(view_bet_history())
```

## Bet History via GraphQL

For more detailed bet data including game names:

```python
from stakeapi.endpoints import GraphQLQueries

async with StakeAPI(access_token="your_token") as client:
    data = await client._graphql_request(
        query=GraphQLQueries.BET_HISTORY,
        variables={"first": 20},
        operation_name="BetHistory"
    )
    
    bets = data.get("user", {}).get("bets", {}).get("edges", [])
    
    for edge in bets:
        bet = edge["node"]
        print(f"Game: {bet['game']['name']}")
        print(f"  Amount: {bet['amount']} {bet['currency']}")
        print(f"  Multiplier: {bet['multiplier']}x")
        print(f"  Payout: {bet['payout']}")
        print(f"  Outcome: {bet['outcome']}")
        print()
```

## Performance Analytics

Analyze your betting performance:

```python
from decimal import Decimal

async def betting_analytics():
    async with StakeAPI(access_token="your_token") as client:
        bets = await client.get_bet_history(limit=100)
        
        if not bets:
            print("No bet history found")
            return
        
        # Basic stats
        total = len(bets)
        won = [b for b in bets if b.status == "won"]
        lost = [b for b in bets if b.status == "lost"]
        pending = [b for b in bets if b.status == "pending"]
        
        total_wagered = sum(b.amount for b in bets)
        total_won = sum(b.potential_payout for b in won)
        net_profit = total_won - total_wagered
        
        win_rate = len(won) / total * 100 if total > 0 else 0
        roi = float(net_profit / total_wagered * 100) if total_wagered > 0 else 0
        
        print("📊 BETTING PERFORMANCE")
        print("=" * 50)
        print(f"  Total Bets:      {total}")
        print(f"  Won:             {len(won)} ({win_rate:.1f}%)")
        print(f"  Lost:            {len(lost)}")
        print(f"  Pending:         {len(pending)}")
        print(f"  Total Wagered:   {total_wagered}")
        print(f"  Total Won:       {total_won}")
        print(f"  Net Profit:      {net_profit}")
        print(f"  ROI:             {roi:+.2f}%")
        
        # Biggest win
        if won:
            biggest = max(won, key=lambda b: b.potential_payout)
            print(f"\n🏆 Biggest Win:")
            print(f"  Amount: {biggest.amount} → Payout: {biggest.potential_payout}")
            print(f"  Odds: {biggest.odds}")
        
        # Streaks
        current_streak = 0
        best_win_streak = 0
        worst_loss_streak = 0
        temp_streak = 0
        
        for bet in sorted(bets, key=lambda b: b.placed_at):
            if bet.status == "won":
                if temp_streak > 0:
                    temp_streak += 1
                else:
                    temp_streak = 1
                best_win_streak = max(best_win_streak, temp_streak)
            elif bet.status == "lost":
                if temp_streak < 0:
                    temp_streak -= 1
                else:
                    temp_streak = -1
                worst_loss_streak = max(worst_loss_streak, abs(temp_streak))
        
        print(f"\n📈 Streaks:")
        print(f"  Best Win Streak:   {best_win_streak}")
        print(f"  Worst Loss Streak: {worst_loss_streak}")

asyncio.run(betting_analytics())
```

## The Bet Model

```python
class Bet(BaseModel):
    id: str                         # Unique bet ID
    user_id: str                    # User who placed the bet
    game_id: Optional[str]          # Casino game ID
    event_id: Optional[str]         # Sports event ID
    bet_type: str                   # single, multi, etc.
    amount: Decimal                 # Wager amount
    potential_payout: Decimal       # Potential winnings
    odds: Optional[float]           # Bet odds
    status: str                     # pending, won, lost, cancelled
    placed_at: datetime             # When the bet was placed
    settled_at: Optional[datetime]  # When the bet was settled
```

## Profit/Loss Tracking Over Time

```python
from datetime import datetime, timedelta

async def daily_pnl():
    async with StakeAPI(access_token="your_token") as client:
        bets = await client.get_bet_history(limit=100)
        
        # Group by day
        daily = {}
        for bet in bets:
            day = bet.placed_at.strftime("%Y-%m-%d")
            if day not in daily:
                daily[day] = {"wagered": Decimal(0), "won": Decimal(0), "count": 0}
            
            daily[day]["wagered"] += bet.amount
            daily[day]["count"] += 1
            
            if bet.status == "won":
                daily[day]["won"] += bet.potential_payout
        
        print("📅 DAILY PROFIT/LOSS")
        print("=" * 60)
        
        running_total = Decimal(0)
        for day in sorted(daily.keys()):
            d = daily[day]
            pnl = d["won"] - d["wagered"]
            running_total += pnl
            
            icon = "🟢" if pnl >= 0 else "🔴"
            print(f"  {day}  {icon} {float(pnl):+10.4f}  "
                  f"(Bets: {d['count']}, Running: {float(running_total):+.4f})")

asyncio.run(daily_pnl())
```

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

{: .note }
> Ready to track your betting performance? [Create your Stake.com account](https://stake.com/?c=WY7953wQ) and use StakeAPI to build powerful analytics tools.
