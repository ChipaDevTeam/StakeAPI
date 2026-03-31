---
layout: default
title: Troubleshooting
parent: Resources
nav_order: 3
---

# Troubleshooting
{: .fs-9 }

Solutions to common issues when using StakeAPI.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Authentication Issues

### `AuthenticationError: Invalid access token`

**Cause:** Your access token is invalid or has expired.

**Solution:**
1. Log in to [Stake.com](https://stake.com/?c=WY7953wQ) in your browser
2. Open Developer Tools → Network tab
3. Find a request to `/_api/graphql`
4. Copy the fresh `x-access-token` value

```python
# Check if token is valid format
from stakeapi.utils import validate_api_key
print(validate_api_key(your_token))  # Should be True
```

### Token works in browser but not in Python

**Cause:** Token may have been invalidated after you logged out, or headers are missing.

**Solution:** Ensure you're passing the token correctly:

```python
# ✅ Correct
client = StakeAPI(access_token="your_actual_token_value")

# ❌ Wrong — don't include the header name
client = StakeAPI(access_token="x-access-token: token_value")
```

---

## Connection Issues

### `NetworkError: Request failed`

**Cause:** Cannot connect to Stake.com servers.

**Solutions:**
1. Check your internet connection
2. Verify Stake.com is accessible from your location
3. Check if you're behind a firewall/proxy
4. Try increasing the timeout:

```python
client = StakeAPI(access_token="token", timeout=60)
```

### Connection timeout

**Cause:** Request took too long.

**Solution:** Increase timeout:

```python
client = StakeAPI(access_token="token", timeout=120)
```

---

## Rate Limiting

### `RateLimitError: Rate limit exceeded`

**Cause:** Too many requests too quickly.

**Solution:** Add delays between requests:

```python
import asyncio

# Add delay between requests
for game_id in game_ids:
    game = await client.get_game_details(game_id)
    await asyncio.sleep(0.5)  # 500ms delay
```

Or use exponential backoff:

```python
async def fetch_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return await func()
        except RateLimitError:
            await asyncio.sleep(2 ** i)
    raise Exception("Max retries exceeded")
```

---

## Import Issues

### `ModuleNotFoundError: No module named 'stakeapi'`

**Solution:**

```bash
pip install stakeapi
```

If using a virtual environment, make sure it's activated:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### `ImportError: cannot import name 'StakeAPI'`

**Solution:** Check your import statement:

```python
# ✅ Correct
from stakeapi import StakeAPI

# ❌ Wrong
from stakeapi.client import StakeAPI  # Also works but not recommended
```

---

## Async Issues

### `RuntimeError: no running event loop`

**Cause:** Using async code without an event loop.

**Solution:** Use `asyncio.run()`:

```python
import asyncio

async def main():
    async with StakeAPI(access_token="token") as client:
        balance = await client.get_user_balance()

# ✅ Correct
asyncio.run(main())

# ❌ Wrong — don't call async functions directly
# main()  # This returns a coroutine, not the result
```

### `RuntimeWarning: coroutine was never awaited`

**Cause:** Forgetting to `await` an async call.

```python
# ❌ Wrong
balance = client.get_user_balance()  # Missing await!

# ✅ Correct
balance = await client.get_user_balance()
```

### `RuntimeError: Session is closed`

**Cause:** Using the client after the context manager has exited.

```python
# ❌ Wrong
async with StakeAPI(access_token="token") as client:
    pass
# Client is closed here!
balance = await client.get_user_balance()

# ✅ Correct — keep operations inside the context
async with StakeAPI(access_token="token") as client:
    balance = await client.get_user_balance()
```

---

## Data Issues

### Empty results from API calls

**Possible causes:**
1. Account has no data (new account with no bets)
2. Filter parameters are too restrictive
3. API endpoint returned unexpected format

**Solution:** Try without filters first:

```python
# Try without category filter
games = await client.get_casino_games()  # No filter
print(f"Total games: {len(games)}")
```

### Pydantic validation errors

**Cause:** API returned unexpected data format.

**Solution:** Use raw GraphQL to inspect the response:

```python
data = await client._graphql_request(
    query="query { user { id name } }"
)
print(data)  # Inspect raw response
```

---

## Platform-Specific Issues

### Windows: `ProactorEventLoop` warnings

Add this at the top of your script:

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Jupyter Notebook: Event loop already running

Use `nest_asyncio`:

```python
import nest_asyncio
nest_asyncio.apply()

import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="token") as client:
        return await client.get_user_balance()

balance = asyncio.run(main())
```

---

## Still Stuck?

1. Check the [FAQ]({% link resources/faq.md %})
2. Search [GitHub Issues](https://github.com/chipadevteam/StakeAPI/issues)
3. Open a new issue with:
   - StakeAPI version
   - Python version
   - Full error traceback
   - Minimal reproducing code

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

{: .note }
> Most issues are solved by getting a fresh access token. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and grab a new token from Developer Tools.
