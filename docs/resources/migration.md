---
layout: default
title: Migration Guide
parent: Resources
nav_order: 6
---

# Migration Guide
{: .fs-9 }

How to upgrade between StakeAPI versions smoothly.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Versioning Policy

StakeAPI follows [Semantic Versioning](https://semver.org/):

- **Major** (x.0.0) — Breaking changes
- **Minor** (0.x.0) — New features, backwards compatible
- **Patch** (0.0.x) — Bug fixes, backwards compatible

## Upgrading StakeAPI

### Using pip

```bash
# Upgrade to latest
pip install --upgrade stakeapi

# Upgrade to specific version
pip install stakeapi==0.2.0

# Check current version
python -c "import stakeapi; print(stakeapi.__version__)"
```

## Migration: Pre-release → v0.1.0

If you were using StakeAPI before the official v0.1.0 release:

### Import Changes

```python
# Old (if applicable)
from stake_api import Client

# New (v0.1.0+)
from stakeapi import StakeAPI
```

### Client Initialization

```python
# Old
client = Client(api_key="your_key")

# New (v0.1.0+)
client = StakeAPI(access_token="your_token")
```

### Balance Method

```python
# Old
balance = await client.get_balance()

# New (v0.1.0+) — returns structured dict
balance = await client.get_user_balance()
# Returns: {"available": {...}, "vault": {...}}
```

### Context Manager

```python
# Old — manual cleanup
client = Client(api_key="key")
balance = await client.get_balance()
await client.close()

# New (v0.1.0+) — async context manager
async with StakeAPI(access_token="token") as client:
    balance = await client.get_user_balance()
# Session closed automatically
```

## Future Migration Notes

This section will be updated as new versions are released.

### v0.1.0 → v0.2.0

Mostly additions: public casino and sports data, WebSocket feeds, account data, betting methods, and browser login. Things that can affect existing code:

- **Python 3.10 or newer is required.** Python 3.8 and 3.9 are no longer supported.
- **`place_bet()` still raises**, now with a message pointing to the per-game methods (`dice_roll()`, `crash_bet()`, `place_sport_bet()`, ...). Those need `StakeAPI(..., allow_betting=True)` and support `dry_run=True`.
- **`get_casino_games()`, `get_game_details()` and `get_sports_events()` now work** instead of raising. Pass the site's slugs (`"stake-originals"`, `"stake-dice"`, `"soccer"`). The old example slug `"football"` is `"soccer"`.
- **`Game` has two new fields**, `slug` and `player_count`.
- **`get_bet_history()`** takes `offset` and a `game` filter.
- **"Please log in." errors** raise `PermissionDeniedError` instead of a plain `GraphQLError`.
- **Credentials can be changed while running**: `client.access_token`, `client.set_access_token()` and `await client.reload_cookies()` take effect on the next request, and a closed client reconnects on its next request.
- **403 errors** now say who blocked the request and what to check. For logged-in calls that a plain script cannot make, use `StakeAPI.with_browser()` (`pip install "stakeapi[browser]"`).

### Deprecation Policy

- Deprecated features will show warnings for at least one minor version
- Deprecated features will be removed in the next major version
- Migration paths will always be documented here

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

{: .note }
> Stay up to date with the latest StakeAPI features. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) to start using the API today.
