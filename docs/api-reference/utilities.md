---
layout: default
title: Utilities
parent: API Reference
nav_order: 6
---

# Utilities
{: .fs-9 }

Helper functions for validation, formatting, and safe type conversion.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

The `stakeapi.utils` module provides pure utility functions used throughout the library. You can import and use them in your own code — they have no side effects and no dependencies on the rest of StakeAPI.

**Import:**

```python
from stakeapi.utils import (
    validate_api_key,
    safe_decimal,
    parse_datetime,
    format_currency,
    calculate_win_rate,
    validate_bet_amount,
    sanitize_game_name,
)
```

---

## `validate_api_key(api_key)`

```python
def validate_api_key(api_key: str) -> bool
```

Check whether an API key string has a valid format. Accepts only alphanumeric strings between 32 and 64 characters long.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `api_key` | `str` | The API key string to validate |

**Returns:** `bool` — `True` if the format is valid, `False` otherwise.

**Validation rules:**
- Must be a non-empty string
- Must match `^[a-zA-Z0-9]{32,64}$` — alphanumeric only, 32–64 chars

```python
from stakeapi.utils import validate_api_key

print(validate_api_key("abc123"))                       # False — too short
print(validate_api_key("a" * 31))                       # False — 31 chars, too short
print(validate_api_key("a" * 32))                       # True  — exactly 32 chars
print(validate_api_key("AbC123xYz" * 4))                # True  — 36 chars, mixed case
print(validate_api_key("has spaces in it " * 3))        # False — spaces not allowed
print(validate_api_key(""))                             # False — empty string
print(validate_api_key(None))                           # False — not a string
```

{: .note }
> This validates format only — it does not verify the key is accepted by Stake.com's API. A key can pass this check and still be refused with `AuthenticationError`.

---

## `safe_decimal(value)`

```python
def safe_decimal(value: Any) -> Optional[Decimal]
```

Safely convert any value to a `Decimal`. Returns `None` instead of raising an exception if the conversion fails. Useful when working with raw API responses that may contain `null`, unexpected types, or malformed numbers.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `value` | `Any` | The value to convert — can be `str`, `int`, `float`, `None`, etc. |

**Returns:** `Optional[Decimal]` — A `Decimal` on success, `None` on failure.

**Why use `Decimal` instead of `float`?**
Floating-point arithmetic is imprecise for financial values. `Decimal("0.1") + Decimal("0.2")` equals `Decimal("0.3")` — which `float` cannot guarantee.

```python
from stakeapi.utils import safe_decimal
from decimal import Decimal

safe_decimal("0.00105")     # Decimal('0.00105')
safe_decimal(42)            # Decimal('42')
safe_decimal(3.14)          # Decimal('3.14')
safe_decimal("1e-8")        # Decimal('1E-8')  (1 satoshi in BTC)
safe_decimal(None)          # None
safe_decimal("not_a_number") # None
safe_decimal([1, 2, 3])     # None

# Safe usage with API data:
raw_amount = api_response.get("amount")   # Might be None or a bad value
amount = safe_decimal(raw_amount)
if amount is not None:
    print(f"Amount: {amount:.8f}")
else:
    print("Amount not available")
```

---

## `parse_datetime(date_string)`

```python
def parse_datetime(date_string: str) -> Optional[datetime]
```

Parse an ISO 8601 datetime string into a Python `datetime` object. Handles both timezone-aware (with `Z` or `+HH:MM` suffix) and naive formats gracefully. Returns `None` instead of raising on bad input.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `date_string` | `str` | ISO 8601 datetime string |

**Returns:** `Optional[datetime]` — A `datetime` object (UTC-aware) on success, `None` on failure.

**Parsing order:**
1. Try `fromisoformat()` after replacing `Z` with `+00:00` (handles UTC-suffixed strings)
2. Fall back to `fromisoformat()` on the raw string, then force-set `tzinfo=UTC`
3. Return `None` if both fail

```python
from stakeapi.utils import parse_datetime

parse_datetime("2025-01-15T14:30:00Z")
# datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

parse_datetime("2025-01-15T14:30:00+05:00")
# datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone(timedelta(hours=5)))

parse_datetime("2025-01-15T14:30:00")
# datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)  — UTC assumed

parse_datetime("")
# None

parse_datetime("not a date")
# None

# Common use with raw API data:
raw_ts = bet_data.get("createdAt")
created = parse_datetime(raw_ts)
if created:
    print(f"Bet placed: {created.strftime('%Y-%m-%d %H:%M UTC')}")
```

---

## `format_currency(amount, currency="USD")`

```python
def format_currency(amount: Decimal, currency: str = "USD") -> str
```

Format a `Decimal` amount as a human-readable currency string. Handles USD, EUR, GBP with native symbols; falls back to `"AMOUNT CODE"` format for crypto and other currencies.

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `amount` | `Decimal` | required | Monetary amount |
| `currency` | `str` | `"USD"` | Currency code (case-insensitive) |

**Returns:** `str` — Formatted string.

**Supported symbols:**

| Currency | Format |
|:---------|:-------|
| `USD` | `$1,234.56` |
| `EUR` | `€1,234.56` |
| `GBP` | `£1,234.56` |
| Others (BTC, ETH, etc.) | `0.00105000 BTC` |

```python
from stakeapi.utils import format_currency
from decimal import Decimal

format_currency(Decimal("1234.56"), "USD")     # "$1234.56"
format_currency(Decimal("99.99"), "EUR")       # "€99.99"
format_currency(Decimal("0.00105"), "BTC")     # "0.00 BTC"  ← 2 decimal places
format_currency(Decimal("0.00105"), "btc")     # "0.00 BTC"  ← case-insensitive
format_currency(Decimal("150.00"), "USDT")     # "150.00 USDT"

# Display a user's balance:
balance = await client.get_user_balance()
for currency, amount in balance["available"].items():
    if amount > 0:
        from decimal import Decimal
        print(format_currency(Decimal(str(amount)), currency))
```

{: .note }
> The `Decimal` format uses `.2f` precision for all currencies. For crypto display you may want higher precision — e.g. `f"{amount:.8f} BTC"`.

---

## `calculate_win_rate(wins, total_bets)`

```python
def calculate_win_rate(wins: int, total_bets: int) -> float
```

Calculate the win rate as a percentage from win and total bet counts.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `wins` | `int` | Number of winning bets |
| `total_bets` | `int` | Total number of bets placed |

**Returns:** `float` — Win rate as a percentage (0.0–100.0). Returns `0.0` if `total_bets` is `0` (avoids division by zero).

```python
from stakeapi.utils import calculate_win_rate

calculate_win_rate(48, 100)   # 48.0
calculate_win_rate(1, 3)      # 33.333...
calculate_win_rate(0, 50)     # 0.0
calculate_win_rate(50, 50)    # 100.0
calculate_win_rate(5, 0)      # 0.0  — no division by zero

# With real data:
bets = await client.get_bet_history(limit=100)
wins = sum(1 for b in bets if b.status == "won")
rate = calculate_win_rate(wins, len(bets))
print(f"Win rate: {rate:.1f}%  ({wins}/{len(bets)})")
```

---

## `validate_bet_amount(amount, min_bet, max_bet)`

```python
def validate_bet_amount(
    amount: Decimal,
    min_bet: Decimal,
    max_bet: Decimal,
) -> bool
```

Check that a bet amount is within the allowed range for a game (`min_bet ≤ amount ≤ max_bet`).

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `amount` | `Decimal` | The proposed bet amount |
| `min_bet` | `Decimal` | Minimum allowed bet (inclusive) |
| `max_bet` | `Decimal` | Maximum allowed bet (inclusive) |

**Returns:** `bool` — `True` if the amount is within range.

```python
from stakeapi.utils import validate_bet_amount
from decimal import Decimal

validate_bet_amount(Decimal("0.001"), Decimal("0.0001"), Decimal("100"))   # True
validate_bet_amount(Decimal("0.00001"), Decimal("0.0001"), Decimal("100")) # False — below min
validate_bet_amount(Decimal("200"), Decimal("0.0001"), Decimal("100"))     # False — above max
validate_bet_amount(Decimal("0.0001"), Decimal("0.0001"), Decimal("100"))  # True  — exactly min
validate_bet_amount(Decimal("100"), Decimal("0.0001"), Decimal("100"))     # True  — exactly max

# Use before placing a bet:
game = await client.get_game_details("dice")
amount = Decimal("0.00001")

if validate_bet_amount(amount, game.min_bet, game.max_bet):
    bet = await client.place_bet({"game_id": game.id, "amount": float(amount)})
else:
    print(f"Amount must be between {game.min_bet} and {game.max_bet}")
```

{: .warning }
> Always validate amounts client-side before calling `place_bet()`. Submitting an invalid amount wastes a network round-trip and may contribute to rate-limiting.

---

## `sanitize_game_name(name)`

```python
def sanitize_game_name(name: str) -> str
```

Clean a game name string for safe use in filenames, URLs, database keys, or log output. Strips special characters (keeps letters, numbers, spaces, hyphens) and normalises whitespace.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `name` | `str` | Raw game name string |

**Returns:** `str` — Sanitised string. Returns `""` for `None` or empty input.

**Transformation rules:**
1. Remove any character that is not `\w` (word char), space, or `-`
2. Collapse consecutive whitespace to a single space
3. Strip leading/trailing whitespace

```python
from stakeapi.utils import sanitize_game_name

sanitize_game_name("Plinko")                         # "Plinko"
sanitize_game_name("Dragon Tiger 🐉")                # "Dragon Tiger "  (emoji removed)
sanitize_game_name("Blackjack (Classic)")             # "Blackjack Classic"
sanitize_game_name("Super   Slots!!!")                # "Super Slots"
sanitize_game_name("  Baccarat  ")                   # "Baccarat"
sanitize_game_name("")                               # ""
sanitize_game_name(None)                             # ""

# Use when building file paths or slugs:
games = await client.get_casino_games()
for game in games[:5]:
    safe_name = sanitize_game_name(game.name)
    slug = safe_name.lower().replace(" ", "-")
    print(f"  {slug}")   # e.g. "plinko", "dragon-tiger"
```

---

## Quick Reference

| Function | Input | Returns | Use case |
|:---------|:------|:--------|:---------|
| `validate_api_key(key)` | `str` | `bool` | Pre-flight auth check |
| `safe_decimal(value)` | `Any` | `Optional[Decimal]` | Parse raw API amounts safely |
| `parse_datetime(s)` | `str` | `Optional[datetime]` | Parse API timestamps |
| `format_currency(amount, currency)` | `Decimal, str` | `str` | Display-friendly amounts |
| `calculate_win_rate(wins, total)` | `int, int` | `float` | Statistics dashboard |
| `validate_bet_amount(amount, min, max)` | `Decimal×3` | `bool` | Pre-bet validation |
| `sanitize_game_name(name)` | `str` | `str` | Safe filenames / slugs |

---

## Full Example: Stats Dashboard

```python
import asyncio
from decimal import Decimal
from stakeapi import StakeAPI
from stakeapi.utils import (
    safe_decimal,
    format_currency,
    calculate_win_rate,
)

async def print_stats():
    async with StakeAPI(
        access_token="YOUR_ACCESS_TOKEN",
        cf_clearance="YOUR_CF_CLEARANCE",
    ) as client:
        # Balance
        balance = await client.get_user_balance()
        print("=== Balance ===")
        for currency, amount in balance["available"].items():
            if amount > 0:
                d = safe_decimal(amount)
                print(f"  {format_currency(d, currency)}")

        # Bet history stats
        bets = await client.get_bet_history(limit=200)
        wins       = [b for b in bets if b.status == "won"]
        win_rate   = calculate_win_rate(len(wins), len(bets))
        wagered    = sum(b.amount for b in bets)
        returned   = sum(b.potential_payout for b in wins)

        print(f"\n=== Last {len(bets)} Bets ===")
        print(f"  Win rate:  {win_rate:.1f}%")
        print(f"  Wagered:   {wagered:.8f}")
        print(f"  Returned:  {returned:.8f}")
        print(f"  Net:       {returned - wagered:+.8f}")

asyncio.run(print_stats())
```

---

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

## See Also

- [Data Models](models.md) — `Decimal` fields in `Bet`, `Game`, `Statistics`
- [Exceptions](exceptions.md) — `ValidationError` raised when input fails checks
- [StakeAPI Client](client.md) — Methods that benefit from pre-validation
- [Advanced Usage](../guides/advanced-usage.md) — Combining utilities in real workflows
