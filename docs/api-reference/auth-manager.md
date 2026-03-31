---
layout: default
title: AuthManager
parent: API Reference
nav_order: 2
---

# AuthManager
{: .fs-9 }

Authentication and token management for Stake.com API access.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Class: `AuthManager`

Handles authentication tokens, session cookies, and credential extraction for StakeAPI.

**Import:**

```python
from stakeapi.auth import AuthManager
```

---

## Constructor

```python
AuthManager(
    access_token: Optional[str] = None,
    session_cookie: Optional[str] = None,
)
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `access_token` | `Optional[str]` | `None` | Stake.com access token |
| `session_cookie` | `Optional[str]` | `None` | Session cookie value |

---

## Methods

### `get_auth_headers()`

Get authentication headers for HTTP requests.

```python
async def get_auth_headers(self) -> Dict[str, str]
```

**Returns:** Dictionary with `X-Access-Token` header if token is set.

```python
auth = AuthManager(access_token="token123")
headers = await auth.get_auth_headers()
# {"X-Access-Token": "token123"}
```

---

### `get_cookies()`

Get authentication cookies.

```python
def get_cookies(self) -> Dict[str, str]
```

**Returns:** Dictionary with `session` cookie if set.

---

### `set_access_token(access_token, expires_in=None)`

Set or update the access token.

```python
def set_access_token(
    self, 
    access_token: str, 
    expires_in: Optional[int] = None
)
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `access_token` | `str` | New access token |
| `expires_in` | `Optional[int]` | Expiration time in seconds |

```python
auth.set_access_token("new_token", expires_in=7200)  # Expires in 2 hours
```

---

### `set_session_cookie(session_cookie)`

Set the session cookie.

```python
def set_session_cookie(self, session_cookie: str)
```

---

### `is_token_expired()`

Check if the current token is expired (includes 5-minute buffer).

```python
def is_token_expired(self) -> bool
```

**Returns:** `True` if token is expired or will expire within 5 minutes.

```python
if auth.is_token_expired():
    print("Time to refresh your token!")
```

---

### `clear_tokens()`

Clear all stored authentication tokens and cookies.

```python
def clear_tokens(self)
```

---

### `extract_access_token_from_curl(curl_command)` (static)

Extract the access token from a cURL command string.

```python
@staticmethod
def extract_access_token_from_curl(curl_command: str) -> Optional[str]
```

**Returns:** Extracted token or `None`.

```python
token = AuthManager.extract_access_token_from_curl("""
    curl "https://stake.com/_api/graphql" \
        -H "x-access-token: abc123def456"
""")
# Returns: "abc123def456"
```

---

### `extract_session_from_curl(curl_command)` (static)

Extract the session cookie from a cURL command string.

```python
@staticmethod
def extract_session_from_curl(curl_command: str) -> Optional[str]
```

**Returns:** Extracted session cookie or `None`.

```python
session = AuthManager.extract_session_from_curl("""
    curl "https://stake.com/_api/graphql" \
        -b "session=abc123..."
""")
```

---

## Properties

| Property | Type | Description |
|:---------|:-----|:------------|
| `access_token` | `Optional[str]` | Current access token |
| `session_cookie` | `Optional[str]` | Current session cookie |

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

{: .note }
> Get your access token from [Stake.com](https://stake.com/?c=WY7953wQ) — log in, open Developer Tools, and copy from the Network tab.
