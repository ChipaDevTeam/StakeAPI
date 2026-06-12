---
layout: default
title: Data Models
parent: API Reference
nav_order: 3
---

# Data Models
{: .fs-9 }

Typed Pydantic models for every object returned by the Stake.com API.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

All models are built with [Pydantic v2](https://docs.pydantic.dev/) and provide full type safety. Every model exposes a `from_dict()` classmethod to construct instances from raw API response dictionaries. Fields use Python-native types — `Decimal` for monetary values, `datetime` for timestamps, `Optional[T]` where the API may omit a field.

**Import:**

```python
from stakeapi.models import User, Game, SportEvent, Bet, Transaction, Statistics
```

---

## Class: `User`

Represents a Stake.com user account.

### Fields

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | required | Unique user identifier |
| `username` | `str` | required | Public display name |
| `email` | `Optional[str]` | `None` | Email address (may be `None` if not exposed) |
| `verified` | `bool` | `False` | Whether the account has completed verification |
| `created_at` | `datetime` | required | Account creation timestamp (UTC) |
| `country` | `Optional[str]` | `None` | ISO country code, e.g. `"US"`, `"GB"` |
| `currency` | `str` | `"USD"` | Default display currency |

### `from_dict(data)` *(classmethod)*

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "User"
```

Construct a `User` from a raw dictionary (e.g. from a GraphQL response).

### Example

```python
from stakeapi.models import User
from datetime import datetime, timezone

user = User(
    id="u_12345",
    username="highroller",
    email="player@example.com",
    verified=True,
    created_at=datetime(2023, 6, 1, tzinfo=timezone.utc),
    country="US",
    currency="USD",
)

print(user.username)       # highroller
print(user.verified)       # True
print(user.created_at)     # 2023-06-01 00:00:00+00:00
```

### Usage with `StakeAPI`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    user = await client.get_user_profile()
    print(f"{user.username} ({user.country})")
    if not user.verified:
        print("Account not verified — some features may be restricted.")
```

---

## Class: `Game`

Represents a casino game available on Stake.com.

### Fields

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | required | Unique game identifier / slug |
| `name` | `str` | required | Display name, e.g. `"Plinko"`, `"Mines"` |
| `category` | `str` | required | Category slug, e.g. `"slots"`, `"live"`, `"originals"` |
| `provider` | `str` | required | Provider name, e.g. `"Stake Originals"`, `"Pragmatic Play"` |
| `description` | `Optional[str]` | `None` | Short game description |
| `min_bet` | `Decimal` | `0.01` | Minimum bet amount in the account's currency |
| `max_bet` | `Decimal` | `1000.00` | Maximum bet amount |
| `rtp` | `Optional[float]` | `None` | Return to Player percentage (0–100), e.g. `97.0` |
| `volatility` | `Optional[str]` | `None` | Volatility rating: `"low"`, `"medium"`, `"high"` |
| `features` | `List[str]` | `[]` | Special features, e.g. `["bonus_round", "free_spins"]` |
| `thumbnail_url` | `Optional[str]` | `None` | URL of the game's thumbnail image |

### `from_dict(data)` *(classmethod)*

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Game"
```

### Example

```python
from stakeapi.models import Game
from decimal import Decimal

game = Game(
    id="plinko",
    name="Plinko",
    category="originals",
    provider="Stake Originals",
    min_bet=Decimal("0.00000001"),
    max_bet=Decimal("100.00"),
    rtp=97.0,
    volatility="high",
    features=["multiplier"],
)

print(f"{game.name} — RTP: {game.rtp}%")
print(f"Bets: {game.min_bet} to {game.max_bet}")
```

### Usage with `StakeAPI`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    games = await client.get_casino_games(category="originals")
    with_rtp = [g for g in games if g.rtp is not None]
    with_rtp.sort(key=lambda g: g.rtp, reverse=True)
    print("Top 5 highest RTP Originals:")
    for g in with_rtp[:5]:
        print(f"  {g.name}: {g.rtp}%")
```

---

## Class: `SportEvent`

Represents a live or upcoming sports betting event.

### Fields

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | required | Unique event identifier |
| `sport` | `str` | required | Sport name, e.g. `"Football"`, `"Basketball"` |
| `league` | `str` | required | League / competition name |
| `home_team` | `str` | required | Home team or player name |
| `away_team` | `str` | required | Away team or player name |
| `start_time` | `datetime` | required | Scheduled start time (UTC) |
| `status` | `str` | required | `"scheduled"`, `"live"`, `"finished"`, `"cancelled"` |
| `odds` | `Dict[str, float]` | `{}` | Market odds, e.g. `{"home": 1.9, "draw": 3.4, "away": 4.1}` |
| `live` | `bool` | `False` | `True` if the event is currently in-play |

### `from_dict(data)` *(classmethod)*

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "SportEvent"
```

### Example

```python
from stakeapi.models import SportEvent
from datetime import datetime, timezone

event = SportEvent(
    id="evt_789",
    sport="Football",
    league="Premier League",
    home_team="Arsenal",
    away_team="Chelsea",
    start_time=datetime(2025, 9, 15, 20, 0, tzinfo=timezone.utc),
    status="scheduled",
    odds={"home": 1.85, "draw": 3.50, "away": 4.20},
    live=False,
)

print(f"{event.home_team} vs {event.away_team}")
print(f"Kick-off: {event.start_time}")
print(f"Home win odds: {event.odds.get('home', 'N/A')}")
```

### Usage with `StakeAPI`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    events = await client.get_sports_events(sport="football")
    live_events = [e for e in events if e.live]
    print(f"Live matches: {len(live_events)}")
    for event in live_events:
        best = max(event.odds.values()) if event.odds else "N/A"
        print(f"  {event.home_team} vs {event.away_team} — best odds: {best}")
```

---

## Class: `Bet`

Represents a placed bet on a casino game or sports event.

### Fields

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | required | Unique bet identifier |
| `user_id` | `str` | required | ID of the user who placed the bet |
| `game_id` | `Optional[str]` | `None` | Casino game ID (set for casino bets) |
| `event_id` | `Optional[str]` | `None` | Sport event ID (set for sports bets) |
| `bet_type` | `str` | required | Type of bet: `"casino"`, `"sports"`, `"live"` |
| `amount` | `Decimal` | required | Amount wagered |
| `potential_payout` | `Decimal` | required | Potential return if the bet wins |
| `odds` | `Optional[float]` | `None` | Decimal odds (sports bets) |
| `status` | `str` | required | `"pending"`, `"won"`, `"lost"`, `"cancelled"` |
| `placed_at` | `datetime` | required | When the bet was placed (UTC) |
| `settled_at` | `Optional[datetime]` | `None` | When settled (`None` while pending) |

### `from_dict(data)` *(classmethod)*

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Bet"
```

### Example

```python
from stakeapi.models import Bet
from decimal import Decimal
from datetime import datetime, timezone

bet = Bet(
    id="bet_abc",
    user_id="u_12345",
    game_id="dice",
    bet_type="casino",
    amount=Decimal("0.00001"),
    potential_payout=Decimal("0.00002"),
    status="won",
    placed_at=datetime(2025, 1, 10, 14, 30, tzinfo=timezone.utc),
)

profit = bet.potential_payout - bet.amount if bet.status == "won" else -bet.amount
print(f"Bet: {bet.amount} → {bet.status} (P&L: {profit:+.8f})")
```

### Usage with `StakeAPI`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    bets = await client.get_bet_history(limit=50)
    total_wagered = sum(b.amount for b in bets)
    total_won     = sum(b.potential_payout for b in bets if b.status == "won")
    print(f"Net: {total_won - total_wagered:+.8f}")
```

---

## Class: `Transaction`

Represents a financial transaction: deposit, withdrawal, bet deduction, or win credit.

### Fields

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | required | Unique transaction ID |
| `user_id` | `str` | required | Owner user ID |
| `type` | `str` | required | `"deposit"`, `"withdrawal"`, `"bet"`, `"win"` |
| `amount` | `Decimal` | required | Transaction amount |
| `currency` | `str` | required | Currency code, e.g. `"btc"`, `"eth"`, `"usdt"` |
| `status` | `str` | required | `"pending"`, `"completed"`, `"failed"`, `"cancelled"` |
| `timestamp` | `datetime` | required | When the transaction occurred (UTC) |
| `description` | `Optional[str]` | `None` | Human-readable description |

### `from_dict(data)` *(classmethod)*

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Transaction"
```

### Example

```python
from stakeapi.models import Transaction
from decimal import Decimal
from datetime import datetime, timezone

tx = Transaction(
    id="tx_001",
    user_id="u_12345",
    type="deposit",
    amount=Decimal("0.01"),
    currency="btc",
    status="completed",
    timestamp=datetime(2025, 3, 1, 10, 0, tzinfo=timezone.utc),
    description="Bitcoin deposit",
)

print(f"{tx.type.capitalize()}: {tx.amount} {tx.currency.upper()} ({tx.status})")
```

---

## Class: `Statistics`

Aggregated betting statistics for a user account.

### Fields

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `total_bets` | `int` | `0` | Total number of bets placed |
| `total_wagered` | `Decimal` | `0` | Sum of all bet amounts |
| `total_won` | `Decimal` | `0` | Sum of all winning payouts |
| `total_lost` | `Decimal` | `0` | Sum of all losing bet amounts |
| `win_rate` | `float` | `0.0` | Win rate as a percentage (0–100) |
| `biggest_win` | `Decimal` | `0` | Largest single winning payout |
| `favorite_game` | `Optional[str]` | `None` | Game ID most frequently played |

### `from_dict(data)` *(classmethod)*

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Statistics"
```

### Example

```python
from stakeapi.models import Statistics
from decimal import Decimal

stats = Statistics(
    total_bets=1500,
    total_wagered=Decimal("0.15"),
    total_won=Decimal("0.14"),
    total_lost=Decimal("0.01"),
    win_rate=48.7,
    biggest_win=Decimal("0.005"),
    favorite_game="dice",
)

print(f"Bets:      {stats.total_bets}")
print(f"Win rate:  {stats.win_rate:.1f}%")
print(f"Net P&L:   {stats.total_won - stats.total_wagered:+.8f}")
print(f"Best win:  {stats.biggest_win:.8f}")
```

---

## Model Summary

| Model | Key Fields | Returned By |
|:------|:-----------|:------------|
| `User` | `id`, `username`, `verified`, `currency` | `get_user_profile()` |
| `Game` | `id`, `name`, `category`, `rtp`, `min_bet` | `get_casino_games()`, `get_game_details()` |
| `SportEvent` | `home_team`, `away_team`, `odds`, `live` | `get_sports_events()` |
| `Bet` | `amount`, `status`, `potential_payout` | `place_bet()`, `get_bet_history()` |
| `Transaction` | `type`, `amount`, `currency`, `status` | *(future endpoint)* |
| `Statistics` | `total_bets`, `win_rate`, `biggest_win` | *(future endpoint)* |

---

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

## See Also

- [StakeAPI Client](client.md) — Methods that return these models
- [Endpoints](endpoints.md) — GraphQL queries that power the data
- [Utilities](utilities.md) — `safe_decimal()`, `format_currency()`, and helpers
- [Exceptions](exceptions.md) — Error types you may encounter
