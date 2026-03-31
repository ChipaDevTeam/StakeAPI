---
layout: default
title: Utilities
parent: API Reference
nav_order: 6
---

# Utilities
{: .fs-9 }

Helper functions for validation, formatting, and data conversion.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

The `stakeapi.utils` module provides utility functions for common operations like validation, formatting, and type conversion.

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

Validate that an API key matches the expected format.

```python
def validate_api_key(api_key: str) -> bool
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `api_key` | `str` | The API key to validate |

**Returns:** `True` if the key is a 32-64 character alphanumeric string.

```python
validate_api_key("abc123def456")  # True
validate_api_key("")               # False
validate_api_key(None)             # False
```

---

## `safe_decimal(value)`

Safely convert any value to a `Decimal`, returning `None` on failure.

```python
def safe_decimal(value: Any) -> Optional[Decimal]
```

```python
safe_decimal("123.45")     # Decimal('123.45')
safe_decimal(100)          # Decimal('100')
safe_decimal("invalid")   # None
safe_decimal(None)         # None
```

---

## `parse_datetime(date_string)`

Parse an ISO format datetime string to a `datetime` object.

```python
def parse_datetime(date_string: str) -> Optional[datetime]
```

Handles:
- ISO 8601 with timezone: `2024-01-01T12:00:00+00:00`
- ISO 8601 with Z: `2024-01-01T12:00:00Z`
- ISO 8601 without timezone: `2024-01-01T12:00:00`

```python
parse_datetime("2024-01-01T12:00:00Z")
# datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

parse_datetime("invalid")  # None
parse_datetime("")          # None
```

---

## `format_currency(amount, currency)`

Format a decimal amount with the appropriate currency symbol.

```python
def format_currency(amount: Decimal, currency: str = "USD") -> str
```

| Currency | Example Output |
|:---------|:---------------|
| `USD` | `$100.50` |
| `EUR` | `€100.50` |
| `GBP` | `£100.50` |
| Other | `100.50 BTC` |

```python
from decimal import Decimal

format_currency(Decimal("100.50"), "USD")  # "$100.50"
format_currency(Decimal("0.001"), "BTC")   # "0.00 BTC"
```

---

## `calculate_win_rate(wins, total_bets)`

Calculate the win rate as a percentage.

```python
def calculate_win_rate(wins: int, total_bets: int) -> float
```

```python
calculate_win_rate(25, 100)  # 25.0
calculate_win_rate(0, 0)     # 0.0
calculate_win_rate(3, 10)    # 30.0
```

---

## `validate_bet_amount(amount, min_bet, max_bet)`

Check that a bet amount falls within the allowed range.

```python
def validate_bet_amount(
    amount: Decimal, 
    min_bet: Decimal, 
    max_bet: Decimal
) -> bool
```

```python
from decimal import Decimal

validate_bet_amount(
    Decimal("0.5"),
    min_bet=Decimal("0.01"),
    max_bet=Decimal("1000")
)  # True

validate_bet_amount(
    Decimal("0.001"),
    min_bet=Decimal("0.01"),
    max_bet=Decimal("1000")
)  # False — below minimum
```

---

## `sanitize_game_name(name)`

Remove special characters and normalize whitespace in game names.

```python
def sanitize_game_name(name: str) -> str
```

```python
sanitize_game_name("Sweet Bonanza™ 1000")  # "Sweet Bonanza 1000"
sanitize_game_name("  Multiple   Spaces  ")  # "Multiple Spaces"
sanitize_game_name("")                        # ""
```

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

{: .note }
> These utilities make working with [Stake.com](https://stake.com/?c=WY7953wQ) data clean and safe. Sign up and start building!
