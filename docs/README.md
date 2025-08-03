# StakeAPI Documentation

Welcome to the StakeAPI documentation! This unofficial Python library provides a comprehensive interface to interact with stake.com programmatically.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [API Reference](#api-reference)
5. [Examples](#examples)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Best Practices](#best-practices)

## Installation

Install StakeAPI using pip:

```bash
pip install stakeapi
```

For development installation:

```bash
git clone https://github.com/yourusername/StakeAPI.git
cd StakeAPI
pip install -e ".[dev]"
```

## Quick Start

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(api_key="your_api_key") as client:
        # Get user profile
        user = await client.get_user_profile()
        print(f"Welcome, {user.username}!")
        
        # Get casino games
        games = await client.get_casino_games(category="slots")
        print(f"Found {len(games)} slot games")
        
        # Get account balance
        balance = await client.get_user_balance()
        print(f"Balance: {balance}")

asyncio.run(main())
```

## Authentication

StakeAPI supports multiple authentication methods:

### API Key Authentication

```python
from stakeapi import StakeAPI

client = StakeAPI(api_key="your_api_key_here")
```

### Environment Variables

Set your API key as an environment variable:

```bash
export STAKE_API_KEY="your_api_key_here"
```

```python
import os
from stakeapi import StakeAPI

api_key = os.getenv("STAKE_API_KEY")
client = StakeAPI(api_key=api_key)
```

### Configuration File

Create a `.env` file:

```
STAKE_API_KEY=your_api_key_here
STAKE_API_SECRET=your_api_secret_here
```

```python
from dotenv import load_dotenv
import os
from stakeapi import StakeAPI

load_dotenv()
client = StakeAPI(api_key=os.getenv("STAKE_API_KEY"))
```

## API Reference

### Client Initialization

```python
StakeAPI(
    api_key: Optional[str] = None,
    base_url: str = "https://stake.com",
    timeout: int = 30,
    rate_limit: int = 10,
)
```

### Casino Methods

#### `get_casino_games(category: Optional[str] = None) -> List[Game]`

Get available casino games, optionally filtered by category.

```python
# Get all games
games = await client.get_casino_games()

# Get only slot games
slots = await client.get_casino_games(category="slots")
```

#### `get_game_details(game_id: str) -> Game`

Get detailed information about a specific game.

```python
game = await client.get_game_details("game_id_123")
print(f"Game: {game.name}")
print(f"RTP: {game.rtp}%")
print(f"Min bet: ${game.min_bet}")
```

### Sports Methods

#### `get_sports_events(sport: Optional[str] = None) -> List[SportEvent]`

Get available sports events.

```python
# Get all sports events
events = await client.get_sports_events()

# Get only football events
football = await client.get_sports_events(sport="football")
```

### User Methods

#### `get_user_profile() -> User`

Get current user profile information.

```python
user = await client.get_user_profile()
print(f"Username: {user.username}")
print(f"Verified: {user.verified}")
print(f"Country: {user.country}")
```

#### `get_user_balance() -> Dict[str, float]`

Get user account balance by currency.

```python
balance = await client.get_user_balance()
for currency, amount in balance.items():
    print(f"{currency}: {amount}")
```

### Betting Methods

#### `place_bet(bet_data: Dict[str, Any]) -> Bet`

Place a bet (use with caution).

```python
bet_data = {
    "game_id": "game_123",
    "amount": "10.00",
    "bet_type": "win"
}
bet = await client.place_bet(bet_data)
print(f"Bet ID: {bet.id}")
```

#### `get_bet_history(limit: int = 50) -> List[Bet]`

Get user betting history.

```python
bets = await client.get_bet_history(limit=20)
for bet in bets:
    print(f"Bet {bet.id}: ${bet.amount} - {bet.status}")
```

## Examples

### Basic Usage

```python
import asyncio
from stakeapi import StakeAPI

async def basic_example():
    async with StakeAPI(api_key="your_key") as client:
        user = await client.get_user_profile()
        games = await client.get_casino_games()
        balance = await client.get_user_balance()
        
        print(f"User: {user.username}")
        print(f"Games available: {len(games)}")
        print(f"Balance: {balance}")

asyncio.run(basic_example())
```

### Game Analysis

```python
async def analyze_games():
    async with StakeAPI(api_key="your_key") as client:
        games = await client.get_casino_games()
        
        # Group by provider
        providers = {}
        for game in games:
            if game.provider not in providers:
                providers[game.provider] = []
            providers[game.provider].append(game)
        
        # Show top providers
        for provider, games_list in sorted(providers.items(), 
                                         key=lambda x: len(x[1]), 
                                         reverse=True)[:5]:
            print(f"{provider}: {len(games_list)} games")
```

### Sports Betting Analysis

```python
async def analyze_odds():
    async with StakeAPI(api_key="your_key") as client:
        events = await client.get_sports_events(sport="football")
        
        # Find value bets (low margin events)
        value_bets = []
        for event in events:
            if event.odds and "home" in event.odds and "away" in event.odds:
                home_prob = 1 / event.odds["home"]
                away_prob = 1 / event.odds["away"]
                margin = (home_prob + away_prob - 1) * 100
                
                if margin < 5:  # Less than 5% margin
                    value_bets.append((event, margin))
        
        print(f"Found {len(value_bets)} value betting opportunities")
```

## Error Handling

StakeAPI provides specific exception types for different error conditions:

```python
from stakeapi.exceptions import (
    StakeAPIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

async def handle_errors():
    try:
        async with StakeAPI(api_key="invalid_key") as client:
            user = await client.get_user_profile()
    except AuthenticationError:
        print("Invalid API key")
    except RateLimitError:
        print("Rate limit exceeded, please wait")
    except StakeAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

### Retry Logic

```python
import asyncio
from stakeapi.exceptions import RateLimitError

async def retry_request(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)
```

## Rate Limiting

StakeAPI implements automatic rate limiting to prevent API abuse:

```python
# Configure rate limiting
client = StakeAPI(api_key="your_key", rate_limit=5)  # 5 requests per second
```

For batch operations, consider implementing your own rate limiting:

```python
import asyncio

async def batch_process_with_rate_limit(items, func, rate_limit=10):
    semaphore = asyncio.Semaphore(rate_limit)
    
    async def limited_func(item):
        async with semaphore:
            result = await func(item)
            await asyncio.sleep(1 / rate_limit)  # Ensure rate limit
            return result
    
    tasks = [limited_func(item) for item in items]
    return await asyncio.gather(*tasks)
```

## Best Practices

### 1. Use Context Managers

Always use the async context manager to ensure proper session cleanup:

```python
async with StakeAPI(api_key="your_key") as client:
    # Your code here
    pass
# Session is automatically closed
```

### 2. Handle Errors Gracefully

Implement comprehensive error handling for production applications:

```python
from stakeapi.exceptions import StakeAPIError
import logging

async def safe_api_call():
    try:
        async with StakeAPI(api_key="your_key") as client:
            return await client.get_user_profile()
    except StakeAPIError as e:
        logging.error(f"API error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None
```

### 3. Implement Caching

Cache frequently accessed data to reduce API calls:

```python
import asyncio
from datetime import datetime, timedelta

class CachedStakeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self._games_cache = None
        self._games_cache_time = None
        self._cache_duration = timedelta(hours=1)
    
    async def get_casino_games_cached(self):
        now = datetime.now()
        if (self._games_cache is None or 
            self._games_cache_time is None or 
            now - self._games_cache_time > self._cache_duration):
            
            async with StakeAPI(api_key=self.api_key) as client:
                self._games_cache = await client.get_casino_games()
                self._games_cache_time = now
        
        return self._games_cache
```

### 4. Monitor Your Usage

Keep track of your API usage to avoid rate limits:

```python
import time
from collections import deque

class APIUsageMonitor:
    def __init__(self, window_size=60):  # 1-minute window
        self.window_size = window_size
        self.requests = deque()
    
    def record_request(self):
        now = time.time()
        self.requests.append(now)
        
        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window_size:
            self.requests.popleft()
    
    def get_current_rate(self):
        return len(self.requests)
    
    def can_make_request(self, max_rate=60):
        return self.get_current_rate() < max_rate
```

### 5. Use Environment Variables

Never hardcode API keys in your source code:

```python
import os
from stakeapi import StakeAPI

# Good
api_key = os.getenv("STAKE_API_KEY")
if not api_key:
    raise ValueError("STAKE_API_KEY environment variable not set")

client = StakeAPI(api_key=api_key)

# Bad - Never do this
# client = StakeAPI(api_key="sk_live_abcd1234...")
```

## Support

For issues, questions, or contributions:

- GitHub Issues: [https://github.com/yourusername/StakeAPI/issues](https://github.com/yourusername/StakeAPI/issues)
- Documentation: [https://stakeapi.readthedocs.io](https://stakeapi.readthedocs.io)
- Email: support@stakeapi.dev

## Legal Notice

This is an unofficial API wrapper not affiliated with stake.com. Use responsibly and ensure compliance with all applicable laws and regulations in your jurisdiction.
