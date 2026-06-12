---
layout: default
title: Exceptions
parent: API Reference
nav_order: 5
---

# Exceptions
{: .fs-9 }

Error types raised by StakeAPI — and how to handle them gracefully.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

All StakeAPI exceptions inherit from `StakeAPIError`, which itself inherits from Python's built-in `Exception`. This hierarchy lets you catch errors at whatever granularity you need — catch every StakeAPI error with one `except StakeAPIError` block, or handle each case individually.

**Import:**

```python
from stakeapi.exceptions import (
    StakeAPIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError,
    GameNotFoundError,
    InsufficientFundsError,
)
```

---

## Exception Hierarchy

```
Exception
└── StakeAPIError                  # Base class — catch-all for library errors
    ├── AuthenticationError        # 401 / invalid token or session
    ├── RateLimitError             # 429 / too many requests
    ├── ValidationError            # Bad input values
    ├── NetworkError               # Connection / timeout failures
    ├── GameNotFoundError          # Requested game does not exist
    └── InsufficientFundsError     # Balance too low for the operation
```

---

## `StakeAPIError`

**Base class** for all StakeAPI exceptions. Catch this to handle any library error without caring about the specific cause.

```python
class StakeAPIError(Exception):
    pass
```

**When raised:**
- GraphQL response contains an `errors` field
- HTTP response is `4xx` or `5xx` and no more specific exception applies
- Cloudflare blocks the request (`403 Forbidden`)

**Example:**

```python
from stakeapi import StakeAPI
from stakeapi.exceptions import StakeAPIError

async with StakeAPI(access_token="...", cf_clearance="...") as client:
    try:
        balance = await client.get_user_balance()
    except StakeAPIError as e:
        print(f"API error: {e}")
        # Log, retry, or alert
```

{: .warning }
> A `403` response from Stake.com usually means your `cf_clearance` cookie is expired or missing. Refresh it from your browser — see the [Authentication Guide](../getting-started/authentication.md).

---

## `AuthenticationError`

Raised when the API returns `401 Unauthorized` — meaning your access token or session cookie is invalid, expired, or missing.

```python
class AuthenticationError(StakeAPIError):
    pass
```

**When raised:**
- `access_token` is wrong, expired, or not provided for a protected endpoint
- Session cookie is invalid or has been revoked

**Example:**

```python
from stakeapi.exceptions import AuthenticationError

async with StakeAPI(access_token="bad_token", cf_clearance="...") as client:
    try:
        user = await client.get_user_profile()
    except AuthenticationError:
        print("Your token is invalid. Get a fresh one from Stake.com.")
        # Re-extract token from browser DevTools
```

**How to fix:**

1. Log into [Stake.com](https://stake.com/?c=WY7953wQ)
2. Open DevTools (`F12`) → Network tab
3. Find a `/_api/graphql` request
4. Copy the `x-access-token` header value
5. Pass it to `StakeAPI(access_token=...)`

---

## `RateLimitError`

Raised when the API returns `429 Too Many Requests` — you are sending requests too fast.

```python
class RateLimitError(StakeAPIError):
    pass
```

**When raised:**
- More requests per second than Stake.com allows (typically ~10 req/s)
- Burst of requests in a short window

**Example:**

```python
import asyncio
from stakeapi.exceptions import RateLimitError

async with StakeAPI(access_token="...", cf_clearance="...") as client:
    try:
        games = await client.get_casino_games()
    except RateLimitError:
        print("Rate limit hit — waiting 5 seconds...")
        await asyncio.sleep(5)
        games = await client.get_casino_games()  # Retry
```

**How to avoid:**

- Set `rate_limit` in the constructor (default is `10` req/s)
- Add `await asyncio.sleep(0.1)` between rapid sequential calls
- Use batching where possible instead of many small calls

```python
# Lower the rate limit to be safe
client = StakeAPI(
    access_token="...",
    cf_clearance="...",
    rate_limit=5,  # max 5 requests/second
)
```

---

## `ValidationError`

Raised when input data does not meet the required format or constraints.

```python
class ValidationError(StakeAPIError):
    pass
```

**When raised:**
- A bet amount is below `min_bet` or above `max_bet`
- A required parameter is missing or the wrong type
- An ID has an invalid format

**Example:**

```python
from stakeapi.exceptions import ValidationError
from stakeapi.utils import validate_bet_amount
from decimal import Decimal

async with StakeAPI(access_token="...", cf_clearance="...") as client:
    amount = Decimal("0.000000001")  # Too small

    try:
        if not validate_bet_amount(amount, Decimal("0.00001"), Decimal("100")):
            raise ValidationError(f"Bet amount {amount} is below the minimum.")
        bet = await client.place_bet({"amount": amount, "game_id": "dice"})
    except ValidationError as e:
        print(f"Validation failed: {e}")
```

---

## `NetworkError`

Raised when there is a low-level network problem — no response received, connection refused, or DNS failure.

```python
class NetworkError(StakeAPIError):
    pass
```

**When raised:**
- `aiohttp.ClientError` — wraps underlying network errors
- Connection timeout (exceeds the `timeout` value set in the constructor)
- DNS resolution failure

**Example:**

```python
from stakeapi.exceptions import NetworkError

async with StakeAPI(access_token="...", cf_clearance="...", timeout=10) as client:
    try:
        balance = await client.get_user_balance()
    except NetworkError as e:
        print(f"Network problem: {e}")
        print("Check your internet connection and try again.")
```

**How to handle:**

- Implement exponential backoff for retries
- Increase `timeout` if your connection is slow
- Check for Stake.com maintenance on their [Discord](https://discord.gg/PHHfh6UyCb)

---

## `GameNotFoundError`

Raised when you request details for a game ID that does not exist on Stake.com.

```python
class GameNotFoundError(StakeAPIError):
    pass
```

**When raised:**
- `get_game_details(game_id)` is called with an unknown or misspelled game ID

**Example:**

```python
from stakeapi.exceptions import GameNotFoundError

async with StakeAPI(access_token="...", cf_clearance="...") as client:
    try:
        game = await client.get_game_details("nonexistent_game_xyz")
    except GameNotFoundError:
        print("That game doesn't exist. Try get_casino_games() to list valid IDs.")
```

---

## `InsufficientFundsError`

Raised when the account balance is too low to complete an operation — typically when placing a bet.

```python
class InsufficientFundsError(StakeAPIError):
    pass
```

**When raised:**
- `place_bet()` is called but the wallet balance is less than the bet amount
- The vault balance is not moved to available before betting

**Example:**

```python
from stakeapi.exceptions import InsufficientFundsError

async with StakeAPI(access_token="...", cf_clearance="...") as client:
    try:
        bet = await client.place_bet({
            "game_id": "dice",
            "amount": 9999,  # Way too much
            "currency": "btc",
        })
    except InsufficientFundsError:
        balance = await client.get_user_balance()
        available_btc = balance["available"].get("btc", 0)
        print(f"Not enough funds. Available BTC: {available_btc:.8f}")
```

---

## Handling All Errors Together

For production code, catch errors from most to least specific:

```python
import asyncio
from stakeapi import StakeAPI
from stakeapi.exceptions import (
    AuthenticationError,
    RateLimitError,
    InsufficientFundsError,
    GameNotFoundError,
    NetworkError,
    ValidationError,
    StakeAPIError,
)

async def safe_place_bet(client, game_id: str, amount: float):
    try:
        bet = await client.place_bet({
            "game_id": game_id,
            "amount": amount,
            "currency": "btc",
        })
        print(f"Bet placed: {bet.id} — {bet.status}")
        return bet

    except AuthenticationError:
        print("Token expired — re-authenticate.")
    except RateLimitError:
        print("Rate limit hit — sleeping 5s...")
        await asyncio.sleep(5)
        return await safe_place_bet(client, game_id, amount)
    except InsufficientFundsError:
        print("Not enough balance.")
    except GameNotFoundError:
        print(f"Game '{game_id}' not found.")
    except ValidationError as e:
        print(f"Invalid input: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")
    except StakeAPIError as e:
        print(f"Unexpected API error: {e}")

    return None
```

---

## Error Reference Table

| Exception | HTTP Status / Trigger | Common Fix |
|:----------|:----------------------|:-----------|
| `StakeAPIError` | Any unhandled API error | Check message for details |
| `AuthenticationError` | `401` | Refresh `access_token` from browser |
| `RateLimitError` | `429` | Back off and retry after delay |
| `ValidationError` | Bad input | Validate with `validate_bet_amount()` etc. |
| `NetworkError` | No response / timeout | Check connectivity, increase `timeout` |
| `GameNotFoundError` | Unknown game ID | Use `get_casino_games()` for valid IDs |
| `InsufficientFundsError` | Low balance | Check balance before betting |

---

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

## See Also

- [Error Handling Guide](../guides/error-handling.md) — Production-grade error handling patterns
- [StakeAPI Client](client.md) — Methods that raise these exceptions
- [Authentication Guide](../getting-started/authentication.md) — Fix `AuthenticationError`
- [Rate Limiting Guide](../guides/rate-limiting.md) — Avoid `RateLimitError`
