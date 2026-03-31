---
layout: default
title: StakeAPI Client
parent: API Reference
nav_order: 1
---

# StakeAPI Client
{: .fs-9 }

Complete reference for the main `StakeAPI` client class.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Class: `StakeAPI`

The main client for interacting with the Stake.com API. Supports both REST and GraphQL requests with async/await.

**Import:**

```python
from stakeapi import StakeAPI
```

---

## Constructor

```python
StakeAPI(
    access_token: Optional[str] = None,
    session_cookie: Optional[str] = None,
    base_url: str = "https://stake.com",
    timeout: int = 30,
    rate_limit: int = 10,
)
```

### Parameters

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `access_token` | `Optional[str]` | `None` | Your Stake.com access token (`x-access-token` header) |
| `session_cookie` | `Optional[str]` | `None` | Session cookie for authentication |
| `base_url` | `str` | `"https://stake.com"` | Base URL for the API |
| `timeout` | `int` | `30` | Request timeout in seconds |
| `rate_limit` | `int` | `10` | Maximum requests per second |

### Example

```python
# Basic usage
client = StakeAPI(access_token="your_token")

# Full configuration
client = StakeAPI(
    access_token="your_token",
    session_cookie="your_session",
    timeout=60,
    rate_limit=5,
)
```

---

## Context Manager

StakeAPI implements the async context manager protocol for automatic session management.

```python
async with StakeAPI(access_token="token") as client:
    # Session is created automatically
    balance = await client.get_user_balance()
# Session is closed automatically
```

### `__aenter__(self)`

Creates the HTTP session and returns the client instance.

### `__aexit__(self, exc_type, exc_val, exc_tb)`

Closes the HTTP session.

---

## Casino Methods

### `get_casino_games(category=None)`

Get available casino games.

```python
async def get_casino_games(
    self, 
    category: Optional[str] = None
) -> List[Game]
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `category` | `Optional[str]` | `None` | Filter by game category |

**Returns:** `List[Game]` — List of casino game objects

**Example:**

```python
# All games
games = await client.get_casino_games()

# Only slots
slots = await client.get_casino_games(category="slots")
```

---

### `get_game_details(game_id)`

Get details for a specific game.

```python
async def get_game_details(self, game_id: str) -> Game
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `game_id` | `str` | The game identifier |

**Returns:** `Game` — Game details object

**Example:**

```python
game = await client.get_game_details("game_123")
print(f"{game.name} — RTP: {game.rtp}%")
```

---

## Sports Methods

### `get_sports_events(sport=None)`

Get available sports events.

```python
async def get_sports_events(
    self, 
    sport: Optional[str] = None
) -> List[SportEvent]
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `sport` | `Optional[str]` | `None` | Filter by sport type |

**Returns:** `List[SportEvent]` — List of sports event objects

**Example:**

```python
# All events
events = await client.get_sports_events()

# Football only
football = await client.get_sports_events(sport="football")
```

---

## User Methods

### `get_user_profile()`

Get the current user's profile information.

```python
async def get_user_profile(self) -> User
```

**Returns:** `User` — User profile object

**Example:**

```python
user = await client.get_user_profile()
print(f"Username: {user.username}")
print(f"Verified: {user.verified}")
```

---

### `get_user_balance()`

Get the user's account balance across all currencies using GraphQL.

```python
async def get_user_balance(self) -> Dict[str, Dict[str, float]]
```

**Returns:** Dictionary with `available` and `vault` balances

**Response Format:**

```python
{
    "available": {
        "btc": 0.001,
        "eth": 0.05,
        "usd": 100.0,
    },
    "vault": {
        "btc": 0.01,
        "eth": 0.0,
    }
}
```

**Example:**

```python
balance = await client.get_user_balance()

for currency, amount in balance["available"].items():
    if amount > 0:
        print(f"{currency.upper()}: {amount}")
```

---

## Betting Methods

### `place_bet(bet_data)`

Place a bet.

```python
async def place_bet(self, bet_data: Dict[str, Any]) -> Bet
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `bet_data` | `Dict[str, Any]` | Bet information dictionary |

**Returns:** `Bet` — Bet confirmation object

**Example:**

```python
bet = await client.place_bet({
    "game_id": "game_123",
    "amount": 0.001,
    "currency": "btc",
})
print(f"Bet ID: {bet.id} — Status: {bet.status}")
```

---

### `get_bet_history(limit=50)`

Get the user's bet history.

```python
async def get_bet_history(self, limit: int = 50) -> List[Bet]
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `limit` | `int` | `50` | Maximum number of bets to return |

**Returns:** `List[Bet]` — List of bet objects

**Example:**

```python
bets = await client.get_bet_history(limit=20)
for bet in bets:
    print(f"{bet.id}: {bet.amount} → {bet.status}")
```

---

## Internal Methods

### `_graphql_request(query, variables=None, operation_name=None)`

Make a raw GraphQL request to the Stake.com API.

```python
async def _graphql_request(
    self,
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    operation_name: Optional[str] = None
) -> Dict[Any, Any]
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `query` | `str` | — | GraphQL query string |
| `variables` | `Optional[Dict]` | `None` | Query variables |
| `operation_name` | `Optional[str]` | `None` | Operation name |

**Returns:** GraphQL response data

**Raises:** `StakeAPIError` for GraphQL errors

---

### `_request(method, endpoint, params=None, data=None)`

Make an authenticated HTTP request.

```python
async def _request(
    self,
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None
) -> Dict[Any, Any]
```

**Raises:**
- `AuthenticationError` for 401 responses
- `RateLimitError` for 429 responses
- `StakeAPIError` for other errors

---

### `close()`

Close the HTTP session.

```python
await client.close()
```

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

{: .note }
> All methods require a valid [Stake.com account](https://stake.com/?c=WY7953wQ). Get started in minutes!
