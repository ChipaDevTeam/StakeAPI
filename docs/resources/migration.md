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

### v0.1.0 → v0.2.0 (Planned)

Expected changes:

- WebSocket API additions (non-breaking)
- New methods for chat and VIP data (non-breaking)
- Possible deprecation of some REST endpoints

### Deprecation Policy

- Deprecated features will show warnings for at least one minor version
- Deprecated features will be removed in the next major version
- Migration paths will always be documented here

{% include affiliate-banner.html %}

---

{: .note }
> Stay up to date with the latest StakeAPI features. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) to start using the API today.
