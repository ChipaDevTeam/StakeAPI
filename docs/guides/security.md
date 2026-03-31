---
layout: default
title: Security
parent: Guides
nav_order: 10
---

# Security Best Practices
{: .fs-9 }

Protect your Stake.com account and API tokens with these essential security practices.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Token Security

Your access token provides full access to your [Stake.com account](https://stake.com/?c=WY7953wQ). Treat it like a password.

### Do's and Don'ts

| ✅ Do | ❌ Don't |
|:------|:---------|
| Store tokens in environment variables | Hardcode tokens in source code |
| Use `.env` files (locally only) | Commit `.env` to version control |
| Rotate tokens regularly | Share tokens with others |
| Use minimal-scope tokens | Log tokens to console/files |
| Encrypt stored tokens | Send tokens over insecure channels |

### Environment Variables

```python
import os

# ✅ GOOD — from environment
token = os.getenv("STAKE_ACCESS_TOKEN")

# ❌ BAD — hardcoded
token = "2775b505cccaee723e5c705..."
```

### .gitignore Configuration

Always exclude sensitive files:

```gitignore
# Secrets
.env
*.env
.env.local
.env.production
config.py
secrets.py
credentials.json

# IDE
.idea/
.vscode/settings.json
```

## Secure Token Storage

### Using python-dotenv

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads from .env file

token = os.getenv("STAKE_ACCESS_TOKEN")
if not token:
    raise ValueError("STAKE_ACCESS_TOKEN not set")
```

### Using keyring (System Keychain)

For maximum security, store tokens in the OS keychain:

```python
import keyring

# Store (do once)
keyring.set_password("stakeapi", "access_token", "your_token_here")

# Retrieve
token = keyring.get_password("stakeapi", "access_token")
```

## Network Security

### HTTPS Only

StakeAPI always communicates over HTTPS. Never change the base URL to HTTP:

```python
# ✅ GOOD — HTTPS (default)
client = StakeAPI(access_token=token, base_url="https://stake.com")

# ❌ BAD — Never use HTTP
client = StakeAPI(access_token=token, base_url="http://stake.com")
```

### Request Timeouts

Always set timeouts to prevent hanging connections:

```python
# 30-second timeout (default)
client = StakeAPI(access_token=token, timeout=30)

# Shorter timeout for critical applications
client = StakeAPI(access_token=token, timeout=10)
```

## Session Management

### Close Sessions Properly

Always use the context manager to ensure sessions are closed:

```python
# ✅ GOOD — Context manager handles cleanup
async with StakeAPI(access_token=token) as client:
    balance = await client.get_user_balance()

# ✅ GOOD — Manual cleanup
client = StakeAPI(access_token=token)
try:
    await client._create_session()
    balance = await client.get_user_balance()
finally:
    await client.close()
```

### Token Expiration Handling

```python
from stakeapi.auth import AuthManager

auth = AuthManager(access_token=token)
auth.set_access_token(token, expires_in=3600)

# Check before making requests
if auth.is_token_expired():
    print("Token expired — get a new one")
    auth.clear_tokens()  # Clean up expired tokens from memory
```

## Input Validation

Use the built-in validation utilities:

```python
from stakeapi.utils import validate_api_key, validate_bet_amount
from decimal import Decimal

# Validate API key format
if not validate_api_key(token):
    raise ValueError("Invalid API key format")

# Validate bet amounts
if not validate_bet_amount(
    amount=Decimal("0.001"),
    min_bet=Decimal("0.0001"),
    max_bet=Decimal("1.0")
):
    raise ValueError("Bet amount out of range")
```

## Logging Security

Never log sensitive data:

```python
import logging
logger = logging.getLogger("stakeapi")

# ✅ GOOD — mask the token
logger.info(f"Using token: {token[:8]}...{token[-4:]}")

# ❌ BAD — full token in logs
logger.info(f"Using token: {token}")
```

## Security Checklist

- [ ] Access tokens stored in environment variables
- [ ] `.env` file added to `.gitignore`
- [ ] Tokens rotated regularly
- [ ] HTTPS used for all connections
- [ ] Timeouts configured
- [ ] Sessions properly closed
- [ ] No tokens in log output
- [ ] Input validation on all user-supplied data
- [ ] Error messages don't leak sensitive info

{% include affiliate-banner.html %}

---

{: .note }
> Security starts with a properly configured account. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and enable 2FA for maximum account security.
