---
layout: default
title: Data Models
parent: API Reference
nav_order: 3
---

# Data Models
{: .fs-9 }

Type-safe Pydantic models for all Stake.com API responses.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

StakeAPI uses [Pydantic](https://docs.pydantic.dev/) models for automatic data validation, serialization, and type safety. All API responses are converted into these models.

**Import:**

```python
from stakeapi.models import User, Game, SportEvent, Bet, Transaction, Statistics
```

---

## User

Represents a Stake.com user account.

```python
class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    verified: bool = False
    created_at: datetime
    country: Optional[str] = None
    currency: str = "USD"
```

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | — | Unique user ID |
| `username` | `str` | — | Display name |
| `email` | `Optional[str]` | `None` | Email address |
| `verified` | `bool` | `False` | Email verification status |
| `created_at` | `datetime` | — | Account creation timestamp |
| `country` | `Optional[str]` | `None` | User's country |
| `currency` | `str` | `"USD"` | Preferred currency |

### Factory Method

```python
user = User.from_dict({"id": "123", "username": "player1", "created_at": "2024-01-01"})
```

---

## Game

Represents a casino game on Stake.com.

```python
class Game(BaseModel):
    id: str
    name: str
    category: str
    provider: str
    description: Optional[str] = None
    min_bet: Decimal = Decimal("0.01")
    max_bet: Decimal = Decimal("1000.00")
    rtp: Optional[float] = None
    volatility: Optional[str] = None
    features: List[str] = []
    thumbnail_url: Optional[str] = None
```

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | — | Unique game identifier |
| `name` | `str` | — | Game display name |
| `category` | `str` | — | Game category (slots, table-games, etc.) |
| `provider` | `str` | — | Software provider name |
| `description` | `Optional[str]` | `None` | Game description |
| `min_bet` | `Decimal` | `0.01` | Minimum bet amount |
| `max_bet` | `Decimal` | `1000.00` | Maximum bet amount |
| `rtp` | `Optional[float]` | `None` | Return to Player percentage |
| `volatility` | `Optional[str]` | `None` | Volatility level (low/medium/high) |
| `features` | `List[str]` | `[]` | Special features list |
| `thumbnail_url` | `Optional[str]` | `None` | Thumbnail image URL |

### Factory Method

```python
game = Game.from_dict({
    "id": "sweet-bonanza",
    "name": "Sweet Bonanza",
    "category": "slots",
    "provider": "Pragmatic Play",
    "rtp": 96.48,
    "volatility": "high"
})
```

---

## SportEvent

Represents a sports event/match.

```python
class SportEvent(BaseModel):
    id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: datetime
    status: str
    odds: Dict[str, float] = {}
    live: bool = False
```

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | — | Unique event ID |
| `sport` | `str` | — | Sport type |
| `league` | `str` | — | League/competition name |
| `home_team` | `str` | — | Home team name |
| `away_team` | `str` | — | Away team name |
| `start_time` | `datetime` | — | Scheduled start time |
| `status` | `str` | — | Event status |
| `odds` | `Dict[str, float]` | `{}` | Market odds dictionary |
| `live` | `bool` | `False` | Whether event is currently live |

### Odds Format

```python
event.odds = {
    "home": 1.85,
    "draw": 3.50,
    "away": 4.20
}
```

---

## Bet

Represents a placed bet.

```python
class Bet(BaseModel):
    id: str
    user_id: str
    game_id: Optional[str] = None
    event_id: Optional[str] = None
    bet_type: str
    amount: Decimal
    potential_payout: Decimal
    odds: Optional[float] = None
    status: str
    placed_at: datetime
    settled_at: Optional[datetime] = None
```

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `id` | `str` | — | Unique bet ID |
| `user_id` | `str` | — | User who placed the bet |
| `game_id` | `Optional[str]` | `None` | Casino game ID (if casino bet) |
| `event_id` | `Optional[str]` | `None` | Sports event ID (if sports bet) |
| `bet_type` | `str` | — | Type of bet (single, multi, etc.) |
| `amount` | `Decimal` | — | Wager amount |
| `potential_payout` | `Decimal` | — | Potential winnings |
| `odds` | `Optional[float]` | `None` | Bet odds |
| `status` | `str` | — | `pending`, `won`, `lost`, `cancelled` |
| `placed_at` | `datetime` | — | When the bet was placed |
| `settled_at` | `Optional[datetime]` | `None` | When the bet was settled |

---

## Transaction

Represents a financial transaction.

```python
class Transaction(BaseModel):
    id: str
    user_id: str
    type: str
    amount: Decimal
    currency: str
    status: str
    timestamp: datetime
    description: Optional[str] = None
```

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | `str` | Transaction ID |
| `user_id` | `str` | User ID |
| `type` | `str` | `deposit`, `withdrawal`, `bet`, `win` |
| `amount` | `Decimal` | Transaction amount |
| `currency` | `str` | Currency code |
| `status` | `str` | Transaction status |
| `timestamp` | `datetime` | When it occurred |
| `description` | `Optional[str]` | Description |

---

## Statistics

Aggregated user statistics.

```python
class Statistics(BaseModel):
    total_bets: int = 0
    total_wagered: Decimal = Decimal("0")
    total_won: Decimal = Decimal("0")
    total_lost: Decimal = Decimal("0")
    win_rate: float = 0.0
    biggest_win: Decimal = Decimal("0")
    favorite_game: Optional[str] = None
```

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `total_bets` | `int` | `0` | Total number of bets |
| `total_wagered` | `Decimal` | `0` | Total amount wagered |
| `total_won` | `Decimal` | `0` | Total amount won |
| `total_lost` | `Decimal` | `0` | Total amount lost |
| `win_rate` | `float` | `0.0` | Win rate percentage |
| `biggest_win` | `Decimal` | `0` | Largest single win |
| `favorite_game` | `Optional[str]` | `None` | Most played game |

---

## Working with Models

### Serialization

All models support Pydantic serialization:

```python
# To dictionary
user_dict = user.model_dump()

# To JSON string
user_json = user.model_dump_json()

# From dictionary
user = User.from_dict(data)
# or
user = User(**data)
```

### Validation

Pydantic automatically validates data types:

```python
# This will raise a validation error
game = Game(id=123, name=456)  # id and name must be strings
```

{% include affiliate-banner.html %}

---

{: .note }
> Working with real data is the best way to learn. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and explore the full data model with live API responses.
