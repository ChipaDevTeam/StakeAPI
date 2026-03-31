---
layout: default
title: Error Handling
parent: Guides
nav_order: 6
---

# Error Handling
{: .fs-9 }

Build robust applications with StakeAPI's comprehensive exception hierarchy.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Exception Hierarchy

StakeAPI provides a granular exception hierarchy so you can handle specific errors precisely:

```
StakeAPIError (base)
├── AuthenticationError     — Invalid/expired tokens
├── RateLimitError          — Too many requests
├── ValidationError         — Invalid input data
├── NetworkError            — Connection failures
├── GameNotFoundError       — Game doesn't exist
└── InsufficientFundsError  — Not enough balance
```

## Basic Error Handling

```python
from stakeapi import StakeAPI
from stakeapi.exceptions import (
    StakeAPIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError,
    GameNotFoundError,
    InsufficientFundsError,
)

async with StakeAPI(access_token="your_token") as client:
    try:
        balance = await client.get_user_balance()
        print(balance)
        
    except AuthenticationError:
        print("Your access token is invalid or expired.")
        print("Get a new token from stake.com")
        
    except RateLimitError:
        print("Too many requests. Slow down!")
        
    except NetworkError:
        print("Network error. Check your internet connection.")
        
    except StakeAPIError as e:
        print(f"API error: {e}")
```

## Handling Each Exception Type

### AuthenticationError

Raised when your access token is invalid, expired, or missing:

```python
try:
    user = await client.get_user_profile()
except AuthenticationError:
    # Token expired — get a new one
    print("Please refresh your access token")
```

### RateLimitError

Raised when you exceed Stake.com's rate limits:

```python
import asyncio

async def request_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.get_user_balance()
        except RateLimitError:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    raise Exception("Max retries exceeded")
```

### ValidationError

Raised when input data doesn't meet requirements:

```python
try:
    bet = await client.place_bet({"amount": -1})
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### NetworkError

Raised when the HTTP connection fails:

```python
try:
    balance = await client.get_user_balance()
except NetworkError:
    print("Could not connect to Stake.com")
    print("Check your internet connection")
```

### GameNotFoundError

Raised when requesting a non-existent game:

```python
try:
    game = await client.get_game_details("nonexistent_id")
except GameNotFoundError:
    print("Game not found")
```

### InsufficientFundsError

Raised when trying to bet more than your balance:

```python
try:
    bet = await client.place_bet({"amount": 1000000})
except InsufficientFundsError:
    print("Not enough funds to place this bet")
```

## Production Error Handling Pattern

A robust pattern for production applications:

```python
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stakeapi")

async def robust_api_call(client, method, *args, max_retries=3, **kwargs):
    """Make an API call with automatic retry and error handling."""
    
    for attempt in range(1, max_retries + 1):
        try:
            result = await method(*args, **kwargs)
            return result
            
        except AuthenticationError:
            logger.error("Authentication failed. Token may be expired.")
            raise  # Don't retry auth errors
            
        except RateLimitError:
            wait = 2 ** attempt
            logger.warning(f"Rate limited (attempt {attempt}/{max_retries}). "
                          f"Retrying in {wait}s...")
            await asyncio.sleep(wait)
            
        except NetworkError:
            wait = attempt * 2
            logger.warning(f"Network error (attempt {attempt}/{max_retries}). "
                          f"Retrying in {wait}s...")
            await asyncio.sleep(wait)
            
        except StakeAPIError as e:
            logger.error(f"API error: {e}")
            if attempt == max_retries:
                raise
            await asyncio.sleep(1)
    
    raise StakeAPIError(f"Failed after {max_retries} attempts")

# Usage:
async with StakeAPI(access_token="your_token") as client:
    balance = await robust_api_call(client, client.get_user_balance)
    print(balance)
```

## Custom Exception Handling with Logging

```python
import traceback

async def safe_operation(client):
    """Perform operation with comprehensive error logging."""
    try:
        balance = await client.get_user_balance()
        games = await client.get_casino_games()
        return {"balance": balance, "games": games}
        
    except AuthenticationError:
        logger.error("AUTH_ERROR: Token invalid or expired")
        return None
        
    except RateLimitError:
        logger.warning("RATE_LIMIT: Too many requests")
        return None
        
    except StakeAPIError as e:
        logger.error(f"API_ERROR: {e}")
        logger.debug(traceback.format_exc())
        return None
        
    except Exception as e:
        logger.critical(f"UNEXPECTED_ERROR: {e}")
        logger.debug(traceback.format_exc())
        raise
```

{% include affiliate-banner.html %}

---

{: .note }
> Robust error handling is essential for production applications. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and test your error handling with real API responses.
