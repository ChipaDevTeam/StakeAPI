---
layout: default
title: StakeAPI Client
parent: API Reference
nav_order: 1
---

# StakeAPI Client
{: .fs-9 }

The main async client class — your entry point for every Stake.com API call.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

`StakeAPI` is the central class of this library. It manages the HTTP session, authentication headers and cookies, Cloudflare bypass, rate-limiting, and exposes every high-level method for casino games, sports events, user data, and betting.

All public methods are `async` and must be `await`ed inside an `async` function.

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
    cf_clearance: Optional[str] = None,
    user_agent: Optional[str] = None,
    base_url: str = "https://stake.com",
    timeout: int = 30,
    rate_limit: int = 10,
)
```

### Parameters

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `access_token` | `Optional[str]` | `None` | Your Stake.com `x-access-token` header value. Required for account-specific methods. |
| `session_cookie` | `Optional[str]` | `None` | Value of the `session` cookie from your browser. Alternative or complement to `access_token`. |
| `cf_clearance` | `Optional[str]` | `None` | Value of the `cf_clearance` cookie. **Required** to bypass Cloudflare protection. |
| `user_agent` | `Optional[str]` | `None` | The exact `User-Agent` string from the browser session that generated `cf_clearance`. Must match. |
| `base_url` | `str` | `"https://stake.com"` | Base URL for all requests. Change only for testing or proxy use. |
| `timeout` | `int` | `30` | Per-request timeout in seconds. Increase for slow connections. |
| `rate_limit` | `int` | `10` | Maximum requests per second before throttling kicks in. |

{: .warning }
> **Cloudflare**: Stake.com is protected by Cloudflare. Without a valid `cf_clearance` cookie you will receive `403 Forbidden` on most endpoints. See [Authentication](../getting-started/authentication.md) for how to obtain it.

### Full Example

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    client = StakeAPI(
        access_token="your_x_access_token",
        session_cookie="your_session_cookie",
        cf_clearance="your_cf_clearance_cookie",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
        timeout=60,
        rate_limit=5,
    )
    balance = await client.get_user_balance()
    await client.close()

asyncio.run(main())
```

---

## Async Context Manager

The recommended way to use `StakeAPI` is as an async context manager. It automatically creates and closes the HTTP session for you.

```python
async with StakeAPI(
    access_token="your_token",
    cf_clearance="your_cf_clearance",
    user_agent="your_user_agent",
) as client:
    balance = await client.get_user_balance()
    profile = await client.get_user_profile()
# Session is closed automatically here — no need to call client.close()
```

### `__aenter__(self)`

Creates the internal `aiohttp.ClientSession` with all configured headers and cookies, then returns `self`.

### `__aexit__(self, exc_type, exc_val, exc_tb)`

Gracefully closes the session. Called automatically at the end of an `async with` block, even if an exception occurred.

---

## Session Management

### `_create_session()`

```python
async def _create_session(self) -> None
```

Creates the `aiohttp.ClientSession` with the following headers pre-populated:

| Header | Value |
|:-------|:------|
| `User-Agent` | Provided value or sensible Chrome/Windows default |
| `Accept` | `application/graphql+json, application/json` |
| `Content-Type` | `application/json` |
| `Origin` | `https://stake.com` |
| `Referer` | `https://stake.com/` |
| `X-Language` | `en` |
| `X-Access-Token` | Your `access_token` (if provided) |

Cookies `session` and `cf_clearance` are injected at the session level so they are sent with every request automatically.

{: .note }
> You do not normally need to call this method directly — it is called automatically on first use or by `__aenter__`.

---

### `close()`

```python
async def close(self) -> None
```

Close the underlying HTTP session and free resources.

```python
client = StakeAPI(access_token="token", cf_clearance="...")
try:
    balance = await client.get_user_balance()
finally:
    await client.close()
```

{: .note }
> Prefer the `async with` pattern over manual `close()` calls — it is safer and more concise.

---

## Casino Methods

### `get_casino_games(category=None)`

```python
async def get_casino_games(
    self,
    category: Optional[str] = None
) -> List[Game]
```

Fetch the list of casino games available on Stake.com, optionally filtered by category.

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `category` | `Optional[str]` | `None` | Category slug to filter by, e.g. `"slots"`, `"live"`, `"table"` |

**Returns:** `List[Game]` — Each item is a [`Game`](models.md#class-game) object.

**Raises:** `StakeAPIError`, `AuthenticationError`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    # Get all games
    all_games = await client.get_casino_games()
    print(f"Total games: {len(all_games)}")

    # Filter to slots only
    slots = await client.get_casino_games(category="slots")
    for game in slots[:5]:
        print(f"  {game.name} ({game.provider}) — RTP: {game.rtp}%")
```

---

### `get_game_details(game_id)`

```python
async def get_game_details(self, game_id: str) -> Game
```

Fetch full details for a single casino game by its ID.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `game_id` | `str` | The unique game identifier (e.g. `"plinko"`, `"dice"`) |

**Returns:** `Game` — A fully populated [`Game`](models.md#class-game) object.

**Raises:** `GameNotFoundError` if the game ID does not exist, `StakeAPIError` for other errors.

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    game = await client.get_game_details("plinko")
    print(f"Name: {game.name}")
    print(f"Provider: {game.provider}")
    print(f"RTP: {game.rtp}%")
    print(f"Min bet: {game.min_bet} / Max bet: {game.max_bet}")
    print(f"Volatility: {game.volatility}")
    print(f"Features: {', '.join(game.features)}")
```

---

## Sports Methods

### `get_sports_events(sport=None)`

```python
async def get_sports_events(
    self,
    sport: Optional[str] = None
) -> List[SportEvent]
```

Fetch live and upcoming sports events, optionally filtered by sport.

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `sport` | `Optional[str]` | `None` | Sport slug to filter by, e.g. `"football"`, `"basketball"`, `"tennis"` |

**Returns:** `List[SportEvent]` — Each item is a [`SportEvent`](models.md#class-sportevent) object.

**Raises:** `StakeAPIError`, `AuthenticationError`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    # All available events
    events = await client.get_sports_events()

    # Football only
    football = await client.get_sports_events(sport="football")
    for event in football:
        print(f"{event.home_team} vs {event.away_team}")
        print(f"  League: {event.league}")
        print(f"  Starts: {event.start_time}")
        print(f"  Live: {event.live}")
        print(f"  Odds: {event.odds}")
```

---

## User Methods

### `get_user_profile()`

```python
async def get_user_profile(self) -> User
```

Fetch the authenticated user's profile information.

**Returns:** [`User`](models.md#class-user) object with `id`, `username`, `email`, `verified`, `created_at`, `country`, and `currency`.

**Raises:** `AuthenticationError` if not authenticated.

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    user = await client.get_user_profile()
    print(f"Username:  {user.username}")
    print(f"ID:        {user.id}")
    print(f"Verified:  {user.verified}")
    print(f"Country:   {user.country}")
    print(f"Currency:  {user.currency}")
    print(f"Joined:    {user.created_at.strftime('%Y-%m-%d')}")
```

---

### `get_user_balance()`

```python
async def get_user_balance(self) -> Dict[str, Dict[str, float]]
```

Fetch the user's wallet balances across all currencies using the GraphQL API. Returns both the spendable (`available`) amount and the locked (`vault`) amount separately.

**Returns:**

```python
{
    "available": {
        "btc":  0.00104200,
        "eth":  0.05000000,
        "usdt": 150.00,
        "ltc":  0.0,
        # ... one key per currency with a non-zero balance
    },
    "vault": {
        "btc":  0.01000000,
        "eth":  0.0,
        "usdt": 0.0,
    }
}
```

**Raises:** `AuthenticationError` if the session is not authenticated.

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    balance = await client.get_user_balance()

    print("=== Available ===")
    for currency, amount in balance["available"].items():
        if amount > 0:
            print(f"  {currency.upper()}: {amount:.8f}")

    print("=== Vault ===")
    for currency, amount in balance["vault"].items():
        if amount > 0:
            print(f"  {currency.upper()}: {amount:.8f}")
```

{: .note }
> This method uses the `UserBalances` GraphQL query under the hood. See [GraphQL Queries](endpoints.md#graphql-queries) for the raw query.

---

## Betting Methods

### `place_bet(bet_data)`

```python
async def place_bet(self, bet_data: Dict[str, Any]) -> Bet
```

Place a bet on a casino game or sports event.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `bet_data` | `Dict[str, Any]` | Dictionary containing all bet fields required by the endpoint |

**Returns:** [`Bet`](models.md#class-bet) object with the placed bet's ID, status, and payout information.

**Raises:** `InsufficientFundsError`, `ValidationError`, `AuthenticationError`, `StakeAPIError`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    bet = await client.place_bet({
        "game_id": "dice",
        "amount": 0.00001,
        "currency": "btc",
        "target": 50.0,   # example field — varies by game
    })
    print(f"Bet ID:     {bet.id}")
    print(f"Amount:     {bet.amount}")
    print(f"Potential:  {bet.potential_payout}")
    print(f"Status:     {bet.status}")
```

{: .warning }
> Always validate amounts with [`validate_bet_amount()`](utilities.md#validate_bet_amount) before calling this method to avoid unnecessary API errors.

---

### `get_bet_history(limit=50)`

```python
async def get_bet_history(self, limit: int = 50) -> List[Bet]
```

Retrieve the authenticated user's recent bet history.

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `limit` | `int` | `50` | Maximum number of bets to return. Higher values may be slower. |

**Returns:** `List[Bet]` — Most recent bets first.

**Raises:** `AuthenticationError`, `StakeAPIError`

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    bets = await client.get_bet_history(limit=100)

    wins   = [b for b in bets if b.status == "won"]
    losses = [b for b in bets if b.status == "lost"]

    print(f"Last {len(bets)} bets:")
    print(f"  Won:  {len(wins)}")
    print(f"  Lost: {len(losses)}")
    if bets:
        win_rate = len(wins) / len(bets) * 100
        print(f"  Win rate: {win_rate:.1f}%")
```

---

## Internal / Low-Level Methods

These methods are used internally but are also useful for advanced users who need to make custom requests.

### `_graphql_request(query, variables=None, operation_name=None)`

```python
async def _graphql_request(
    self,
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    operation_name: Optional[str] = None
) -> Dict[Any, Any]
```

Send a raw GraphQL request to `/_api/graphql`. Automatically handles authentication headers, checks for `errors` in the response, and returns the `data` field.

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `query` | `str` | — | GraphQL query or mutation string |
| `variables` | `Optional[Dict]` | `None` | Variables dict for parameterised queries |
| `operation_name` | `Optional[str]` | `None` | Optional operation name sent in the payload |

**Returns:** The `data` key of the GraphQL response as a `dict`.

**Raises:** `StakeAPIError` if the response contains a `errors` key.

```python
async with StakeAPI(access_token="...", cf_clearance="...") as client:
    data = await client._graphql_request(
        query="""
          query UserProfile {
            user { id name email }
          }
        """,
        operation_name="UserProfile",
    )
    print(data["user"]["name"])
```

---

### `_request(method, endpoint, params=None, data=None)`

```python
async def _request(
    self,
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
) -> Dict[Any, Any]
```

Make a raw authenticated HTTP request.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `method` | `str` | HTTP verb: `"GET"`, `"POST"`, `"PUT"`, `"DELETE"` |
| `endpoint` | `str` | Path relative to `base_url`, e.g. `"/_api/graphql"` |
| `params` | `Optional[Dict]` | URL query parameters |
| `data` | `Optional[Dict]` | JSON request body (serialised automatically) |

**Raises:**

| Status | Exception |
|:-------|:----------|
| `401` | `AuthenticationError` |
| `403` | `StakeAPIError` (Cloudflare block) |
| `429` | `RateLimitError` |
| `4xx/5xx` | `StakeAPIError` |
| Network error | `StakeAPIError` |

---

## Complete Working Example

```python
import asyncio
from stakeapi import StakeAPI
from stakeapi.utils import format_currency
from decimal import Decimal

async def main():
    async with StakeAPI(
        access_token="YOUR_ACCESS_TOKEN",
        cf_clearance="YOUR_CF_CLEARANCE",
        user_agent="YOUR_USER_AGENT",
    ) as client:

        # Profile
        user = await client.get_user_profile()
        print(f"Logged in as: {user.username}")

        # Balance
        balance = await client.get_user_balance()
        for currency, amount in balance["available"].items():
            if amount > 0:
                print(f"  {currency.upper()}: {amount:.8f}")

        # Casino games
        games = await client.get_casino_games(category="slots")
        print(f"\nSlots available: {len(games)}")

        # Bet history
        bets = await client.get_bet_history(limit=20)
        won = sum(1 for b in bets if b.status == "won")
        print(f"\nLast 20 bets — Won: {won}, Lost: {len(bets) - won}")

asyncio.run(main())
```

---

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

## See Also

- [AuthManager](auth-manager.md) — Token and cookie management
- [Data Models](models.md) — `User`, `Game`, `Bet`, `SportEvent`
- [Endpoints](endpoints.md) — All URL constants and GraphQL queries
- [Exceptions](exceptions.md) — Error handling reference
- [Utilities](utilities.md) — Helper functions
- [Authentication Guide](../getting-started/authentication.md) — How to get your tokens
