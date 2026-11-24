---
layout: default
title: Authentication
parent: Getting Started
nav_order: 2
---

# Authentication
{: .fs-9 }

Learn how to authenticate with the Stake.com API using access tokens and session cookies.
{: .fs-6 .fw-300 }

---

## Overview

StakeAPI uses the same authentication mechanism as the Stake.com website. You need an **access token** (and optionally a **session cookie**) to make authenticated requests.

{: .important }
> You must have a [Stake.com account](https://stake.com/?c=WY7953wQ) to use StakeAPI. If you don't have one yet, [sign up here](https://stake.com/?c=WY7953wQ) — it takes less than a minute.

## Getting Your Access Token

### Method 1: Browser Developer Tools (Recommended)

1. **Log in** to [Stake.com](https://stake.com/?c=WY7953wQ) in your browser
2. **Open Developer Tools** — Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
3. **Go to the Network tab**
4. **Perform any action** on the site (check balance, browse games, etc.)
5. **Find a GraphQL request** — Look for requests to `/_api/graphql`
6. **Click on the request** and go to the **Headers** tab
7. **Find the `x-access-token` header** — This is your access token

Your access token will look something like:

```
2775b505cccaee723e5c705ba552fea7c272f6d20f68d7224eb3ba23446ca295...
```

### Method 2: Copy as cURL

1. Follow steps 1-5 above
2. **Right-click** the GraphQL request
3. Select **Copy** → **Copy as cURL**
4. Use the built-in extractor:

```python
from stakeapi.auth import AuthManager

curl_command = """
curl "https://stake.com/_api/graphql" \
  -H "x-access-token: your_token_here" \
  -H "content-type: application/json" \
  ...
"""

# Extract access token
token = AuthManager.extract_access_token_from_curl(curl_command)
print(f"Access Token: {token}")

# Extract session cookie
session = AuthManager.extract_session_from_curl(curl_command)
print(f"Session Cookie: {session}")
```

### Method 3: Environment Variables

Store your token securely in an environment variable:

```bash
# Windows (PowerShell)
$env:STAKE_ACCESS_TOKEN = "your_access_token_here"

# macOS/Linux
export STAKE_ACCESS_TOKEN="your_access_token_here"
```

Then use it in your code:

```python
import os
from stakeapi import StakeAPI

token = os.getenv("STAKE_ACCESS_TOKEN")
async with StakeAPI(access_token=token) as client:
    balance = await client.get_user_balance()
```

### Method 4: .env File

Create a `.env` file in your project root:

```env
STAKE_ACCESS_TOKEN=your_access_token_here
STAKE_SESSION_COOKIE=your_session_cookie_here
```

Then load it with `python-dotenv`:

```python
import os
from dotenv import load_dotenv
from stakeapi import StakeAPI

load_dotenv()

token = os.getenv("STAKE_ACCESS_TOKEN")
session = os.getenv("STAKE_SESSION_COOKIE")

async with StakeAPI(access_token=token, session_cookie=session) as client:
    balance = await client.get_user_balance()
```

{: .warning }
> **Never commit your `.env` file to version control.** Add it to your `.gitignore` file.

{% include affiliate-cta.html %}

## Authentication Options

StakeAPI supports multiple authentication methods:

### Access Token Only

The simplest approach — sufficient for most use cases:

```python
async with StakeAPI(access_token="your_token") as client:
    # Make API calls
    pass
```

### Access Token + Session Cookie

For maximum compatibility, use both:

```python
async with StakeAPI(
    access_token="your_token",
    session_cookie="your_session_cookie"
) as client:
    # Make API calls
    pass
```

### Cookie File

The simplest setup is to hand StakeAPI all of your browser's cookies for the site. Two file formats work:

- **`cookie.txt`**: the whole `cookie` request header, copied from DevTools → Network → any request to the site.
- **`cookies.json`**: a JSON export from a cookie extension such as Cookie-Editor or EditThisCookie (a list of objects with `name`, `value`, `domain` and `expirationDate`).

```python
async with StakeAPI(base_url="https://stake1017.com", cookie_file="cookies.json") as client:
    print(await client.get_account_status())
```

Your access token is read from the `session` cookie, so you don't need to pass it separately. From a JSON export, StakeAPI only sends cookies whose domain matches `base_url` and skips expired ones. If none match, it raises `ValidationError` naming the domains the file does have cookies for.

{: .warning }
> A cookie file is a live login. Keep it out of git (add `cookie.txt` and `cookies.json` to `.gitignore`), and log out of that session in your browser if the file leaks.

### Using AuthManager

For advanced token management:

```python
from stakeapi.auth import AuthManager

auth = AuthManager(access_token="your_token")

# Check if token is expired
if auth.is_token_expired():
    print("Token has expired, get a new one!")

# Update token
auth.set_access_token("new_token", expires_in=3600)

# Get auth headers for custom requests
headers = await auth.get_auth_headers()
```

## Token Lifecycle

| Aspect | Detail |
|:-------|:-------|
| **Format** | 96-character hex string |
| **Lifetime** | Session-based (varies) |
| **Scope** | Full account access |
| **Rotation** | New token per login session |
| **Invalidation** | Logging out invalidates the token |

## Security Best Practices

1. **Never hardcode tokens** — Use environment variables or `.env` files
2. **Rotate regularly** — Get a fresh token periodically
3. **Limit scope** — Don't share your token with others
4. **Use `.gitignore`** — Exclude `.env` and any files containing tokens
5. **Monitor usage** — Watch for unexpected API activity

```gitignore
# .gitignore
.env
*.env
config.py
secrets.py
cookie.txt
cookies.json
```

## Handling Token Expiration

Tokens can expire or be invalidated. A rejected token raises `AuthenticationError` (HTTP 401) or `PermissionDeniedError` (the GraphQL API says "not allowed" or "please log in"). Credentials are sent with every request, so you can replace them without recreating the client:

```python
from stakeapi import StakeAPI
from stakeapi.exceptions import AuthenticationError, PermissionDeniedError

async with StakeAPI(cookie_file="cookie.txt") as client:
    try:
        balance = await client.get_user_balance()
    except (AuthenticationError, PermissionDeniedError):
        # Re-export your cookies into cookie.txt from the browser, then:
        await client.reload_cookies()
        balance = await client.get_user_balance()
```

| Method | What it does |
|:-------|:-------------|
| `client.set_access_token(token)` | Use a new access token from the next request on |
| `await client.reload_cookies()` | Re-read the `cookie_file` and use its cookies (and the `session` token) from the next request on. An access token you passed explicitly is kept. Needs `cookie_file=`. |

`client.access_token` and `client.session_cookie` can also be assigned directly.

## 403 Forbidden

A 403 means the site's bot protection refused the request before it reached the API. The error says who blocked it (a Cloudflare block page, a Cloudflare challenge, Kasada, or unknown) and checks what it can:

- **No cookies sent.** Pass `cookie_file=` with the cookies of a browser logged in to the same domain as `base_url`.
- **No `cf_clearance`.** Cloudflare-protected mirrors need it; copy it from DevTools → Application → Cookies.
- **Old cookies.** Some are short-lived, so re-copy them.
- **Different browser or network.** The protection checks that a request looks like the browser that earned the cookies. Run from the same network and pass `user_agent=` with that browser's exact User-Agent.

{: .note }
> Even with valid cookies a script can still be refused. Browser-issued bot-protection tokens (Kasada's `x-kpsdk-*` headers, for example) cannot be produced by this library, and it does not try to work around them. What does work is sending the requests from a real browser: see [Browser Login](../guides/browser-login.md), where you log in through a Chrome window, or the library reuses the login from your own Chrome.

## Checking Token Validity

```python
from stakeapi.auth import AuthManager

auth = AuthManager(access_token="your_token")

# Set expiration tracking
auth.set_access_token("your_token", expires_in=7200)  # 2 hours

# Check later
if auth.is_token_expired():
    print("Time to refresh your token!")
    auth.clear_tokens()
```

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

## Next Steps

Now that you're authenticated, make your first API call:

- [Quick Start Guide](quickstart.md) — Your first API call in 30 seconds
- [User Account API](../guides/user-account.md) — Get your profile and balance
- [Casino Games API](../guides/casino-games.md) — Browse available games

---

{: .note }
> Need a Stake.com account to get started? [Sign up here](https://stake.com/?c=WY7953wQ) — it's free and takes less than a minute.
