---
layout: default
title: Exceptions
parent: API Reference
nav_order: 5
---

# Exceptions
{: .fs-9 }

Complete reference for StakeAPI's exception hierarchy.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Exception Hierarchy

```
Exception
└── StakeAPIError
    ├── AuthenticationError
    ├── RateLimitError
    ├── ValidationError
    ├── NetworkError
    ├── GameNotFoundError
    └── InsufficientFundsError
```

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

## StakeAPIError

Base exception for all StakeAPI errors. Catch this to handle any API error.

```python
try:
    result = await client.get_user_balance()
except StakeAPIError as e:
    print(f"Something went wrong: {e}")
```

---

## AuthenticationError

Raised when authentication fails (HTTP 401).

**Common Causes:**
- Invalid access token
- Expired access token
- Missing access token
- Account session invalidated

```python
try:
    result = await client.get_user_balance()
except AuthenticationError:
    print("Token invalid or expired. Get a new one from stake.com")
```

---

## RateLimitError

Raised when API rate limits are exceeded (HTTP 429).

**Handling Strategy:** Exponential backoff

```python
import asyncio

try:
    result = await client.get_user_balance()
except RateLimitError:
    await asyncio.sleep(5)  # Wait and retry
    result = await client.get_user_balance()
```

---

## ValidationError

Raised when input data doesn't meet requirements.

```python
try:
    bet = await client.place_bet({"amount": -1})
except ValidationError as e:
    print(f"Invalid input: {e}")
```

---

## NetworkError

Raised when the HTTP connection fails.

**Common Causes:**
- No internet connection
- DNS resolution failure
- Connection timeout
- Server unreachable

```python
try:
    result = await client.get_user_balance()
except NetworkError:
    print("Network error — check your internet connection")
```

---

## GameNotFoundError

Raised when requesting a game that doesn't exist.

```python
try:
    game = await client.get_game_details("nonexistent")
except GameNotFoundError:
    print("Game not found")
```

---

## InsufficientFundsError

Raised when attempting to bet more than available balance.

```python
try:
    bet = await client.place_bet({"amount": 999999})
except InsufficientFundsError:
    print("Not enough funds")
```

---

## Recommended Error Handling Pattern

```python
from stakeapi.exceptions import *

try:
    result = await client.get_user_balance()
    
except AuthenticationError:
    # Token issues — cannot retry
    handle_auth_failure()
    
except RateLimitError:
    # Retry after delay
    await asyncio.sleep(5)
    
except NetworkError:
    # Connection issues — retry with backoff
    await asyncio.sleep(2)
    
except ValidationError as e:
    # Bad input — fix and retry
    log_validation_error(e)
    
except StakeAPIError as e:
    # Catch-all for other API errors
    log_error(e)
```

{% include affiliate-banner.html %}

---

{: .note }
> Test error handling with real API responses. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and build robust applications.
