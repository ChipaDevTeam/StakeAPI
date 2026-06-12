---
layout: default
title: AuthManager
parent: API Reference
nav_order: 2
---

# AuthManager
{: .fs-9 }

Authentication, token management, and credential extraction for Stake.com.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

`AuthManager` handles everything authentication-related in StakeAPI. It stores your access token and session cookie, tracks token expiry, and provides static helpers to extract credentials from browser cURL exports.

You typically do not instantiate `AuthManager` directly — the `StakeAPI` client creates one internally and exposes it via `client._auth_manager`. However, you can use it standalone for credential management in larger applications.

**Import:**

```python
from stakeapi.auth import AuthManager
```

---

## Class: `AuthManager`

### Constructor

```python
AuthManager(
    access_token: Optional[str] = None,
    session_cookie: Optional[str] = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `access_token` | `Optional[str]` | `None` | Your Stake.com `x-access-token` value |
| `session_cookie` | `Optional[str]` | `None` | Value of the `session` cookie |

**Example:**

```python
from stakeapi.auth import AuthManager

auth = AuthManager(
    access_token="abc123...",
    session_cookie="xyz789...",
)
```

---

## Instance Attributes

| Attribute | Type | Description |
|:----------|:-----|:------------|
| `access_token` | `Optional[str]` | Currently stored access token |
| `session_cookie` | `Optional[str]` | Currently stored session cookie |
| `_token_expires_at` | `Optional[float]` | Unix timestamp when the token expires (`None` = unknown) |

---

## Methods

### `get_auth_headers()`

```python
async def get_auth_headers(self) -> Dict[str, str]
```

Returns a dictionary of HTTP headers required for authentication. If an access token is set, it will be included as `X-Access-Token`.

**Returns:** `Dict[str, str]` — Headers dictionary, possibly empty if no token is set.

```python
auth = AuthManager(access_token="token123")
headers = await auth.get_auth_headers()
# Result: {"X-Access-Token": "token123"}

# Without a token:
auth_empty = AuthManager()
headers = await auth_empty.get_auth_headers()
# Result: {}
```

{: .note }
> This method is `async` for forward compatibility, even though the current implementation does not perform I/O.

---

### `get_cookies()`

```python
def get_cookies(self) -> Dict[str, str]
```

Returns a dictionary of cookies required for authentication. If a session cookie is set, it is included as the `session` key.

**Returns:** `Dict[str, str]` — Cookie dictionary.

```python
auth = AuthManager(session_cookie="sess_abc123")
cookies = auth.get_cookies()
# Result: {"session": "sess_abc123"}

# Without a cookie:
auth_empty = AuthManager()
cookies = auth_empty.get_cookies()
# Result: {}
```

---

### `set_access_token(access_token, expires_in=None)`

```python
def set_access_token(
    self,
    access_token: str,
    expires_in: Optional[int] = None,
) -> None
```

Update the stored access token. Optionally record when it will expire so [`is_token_expired()`](#is_token_expired) can detect stale tokens.

**Parameters:**

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `access_token` | `str` | — | New access token string |
| `expires_in` | `Optional[int]` | `None` | Seconds until the token expires. If provided, expiry tracking is enabled. |

```python
# Simple update
auth.set_access_token("new_token_abc")

# With expiry tracking (e.g. token valid for 2 hours)
auth.set_access_token("new_token_abc", expires_in=7200)

# Later, check if refresh is needed:
if auth.is_token_expired():
    new_token = fetch_new_token()
    auth.set_access_token(new_token, expires_in=7200)
```

---

### `set_session_cookie(session_cookie)`

```python
def set_session_cookie(self, session_cookie: str) -> None
```

Update the stored session cookie.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `session_cookie` | `str` | New session cookie value |

```python
auth.set_session_cookie("new_session_xyz")
print(auth.get_cookies())
# {"session": "new_session_xyz"}
```

---

### `is_token_expired()`

```python
def is_token_expired(self) -> bool
```

Check whether the current access token has expired or is within 5 minutes of expiring.

**Returns:** `bool`
- `True` — Token is expired or expiring in under 5 minutes. Refresh it now.
- `False` — Token is still valid **or** no expiry was set (cannot determine).

**Logic:**
- If `_token_expires_at` is `None` (no expiry was given via `set_access_token(expires_in=...)`), this always returns `False` — the token is assumed to be valid indefinitely.
- If expiry was set, returns `True` when `time.time() >= (expires_at - 300)`.

```python
auth = AuthManager()
auth.set_access_token("my_token", expires_in=3600)  # 1 hour

# Immediately after setting:
print(auth.is_token_expired())  # False

# ... 55 minutes later ...
# print(auth.is_token_expired())  # False (still 5 min buffer left)

# ... 56 minutes later ...
# print(auth.is_token_expired())  # True — refresh needed

# Use in a guard:
if auth.is_token_expired():
    auth.set_access_token(refresh_token(), expires_in=3600)
```

{: .warning }
> If you set a token without `expires_in`, `is_token_expired()` always returns `False`. This is intentional — without an expiry date, the library cannot know when the token becomes invalid.

---

### `clear_tokens()`

```python
def clear_tokens(self) -> None
```

Wipe all stored authentication state: access token, session cookie, and expiry timestamp.

Use this to log out or reset credentials before setting new ones.

```python
auth.clear_tokens()

print(auth.access_token)      # None
print(auth.session_cookie)    # None
print(auth.is_token_expired()) # False (nothing to check)
```

---

### `extract_access_token_from_curl(curl_command)` *(static)*

```python
@staticmethod
def extract_access_token_from_curl(curl_command: str) -> Optional[str]
```

Parse a cURL command string (copied from browser DevTools) and extract the `x-access-token` header value.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `curl_command` | `str` | Full cURL command as a string |

**Returns:** `Optional[str]` — The token value, or `None` if no `x-access-token` header is found.

**How to get your cURL command from Chrome/Edge:**

1. Open [Stake.com](https://stake.com/?c=WY7953wQ) and log in
2. Open DevTools (`F12`) → **Network** tab
3. Find any GraphQL request to `/_api/graphql`
4. Right-click → **Copy** → **Copy as cURL**
5. Paste the result into this method

```python
curl_cmd = """
curl 'https://stake.com/_api/graphql' \
  -H 'x-access-token: eyJhbGciOiJIUzI1NiJ9...' \
  -H 'content-type: application/json' \
  --data-raw '{"query":"..."}'
"""

token = AuthManager.extract_access_token_from_curl(curl_cmd)
print(token)
# eyJhbGciOiJIUzI1NiJ9...

# Use it directly:
client = StakeAPI(access_token=token, cf_clearance="...")
```

{: .note }
> The regex is case-insensitive — it matches `x-access-token`, `X-Access-Token`, etc.

---

### `extract_session_from_curl(curl_command)` *(static)*

```python
@staticmethod
def extract_session_from_curl(curl_command: str) -> Optional[str]
```

Parse a cURL command string and extract the `session` cookie value from the `-b` / `--cookie` flag.

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `curl_command` | `str` | Full cURL command as a string |

**Returns:** `Optional[str]` — The session cookie value, or `None` if not found.

```python
curl_cmd = """
curl 'https://stake.com/_api/graphql' \
  -b 'session=s%3A...encrypted_value...; cf_clearance=abc...' \
  --data-raw '{"query":"..."}'
"""

session = AuthManager.extract_session_from_curl(curl_cmd)
print(session)
# s%3A...encrypted_value...
```

---

## Complete Workflow Example

The most common use-case: copy a cURL from your browser, extract all credentials, and use them.

```python
import asyncio
from stakeapi import StakeAPI
from stakeapi.auth import AuthManager

CURL_COMMAND = """
curl 'https://stake.com/_api/graphql' \
  -H 'x-access-token: YOUR_TOKEN_HERE' \
  -H 'user-agent: Mozilla/5.0 ...' \
  -b 'session=YOUR_SESSION; cf_clearance=YOUR_CF_CLEARANCE' \
  --data-raw '{"query":"{ user { id } }"}'
"""

async def main():
    # Extract credentials from cURL
    token   = AuthManager.extract_access_token_from_curl(CURL_COMMAND)
    session = AuthManager.extract_session_from_curl(CURL_COMMAND)

    print(f"Token found:   {bool(token)}")
    print(f"Session found: {bool(session)}")

    # Build the client
    async with StakeAPI(
        access_token=token,
        session_cookie=session,
        cf_clearance="your_cf_clearance_value",
        user_agent="Mozilla/5.0 ...",
    ) as client:
        user = await client.get_user_profile()
        print(f"Logged in as: {user.username}")

asyncio.run(main())
```

---

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

## See Also

- [StakeAPI Client](client.md) — Main client class that uses `AuthManager` internally
- [Authentication Guide](../getting-started/authentication.md) — Step-by-step credential extraction
- [Exceptions](exceptions.md) — `AuthenticationError` and related errors
- [Getting Started](../getting-started/index.md) — New to StakeAPI? Start here
