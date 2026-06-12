---
layout: default
title: API Reference
nav_order: 4
has_children: true
permalink: /api-reference
---

# API Reference
{: .fs-9 }

Complete technical reference for every class, method, and model in StakeAPI.
{: .fs-6 .fw-300 }

---

{% include affiliate-banner.html %}

## Modules

| Module | What it does |
|:-------|:-------------|
| [StakeAPI Client](client.md) | Main async client — casino, sports, user, and betting methods |
| [AuthManager](auth-manager.md) | Token storage, expiry tracking, cURL credential extraction |
| [Data Models](models.md) | Pydantic models: `User`, `Game`, `SportEvent`, `Bet`, `Transaction`, `Statistics` |
| [Endpoints & GraphQL](endpoints.md) | URL constants and pre-built GraphQL query strings |
| [Exceptions](exceptions.md) | Full exception hierarchy with examples and fix guidance |
| [Utilities](utilities.md) | `safe_decimal`, `format_currency`, `validate_bet_amount`, and more |

---

## Quick Navigation

### By task

| I want to… | Go to… |
|:-----------|:-------|
| Make my first API call | [Getting Started → Quick Start](../getting-started/quickstart.md) |
| Authenticate with Stake.com | [Getting Started → Authentication](../getting-started/authentication.md) |
| Get my account balance | [Client → `get_user_balance()`](client.md#get_user_balance) |
| Browse casino games | [Client → `get_casino_games()`](client.md#get_casino_gamescategorynone) |
| Place a bet | [Client → `place_bet()`](client.md#place_betbet_data) |
| Write a raw GraphQL query | [Endpoints → GraphQL Queries](endpoints.md#class-graphqlqueries) |
| Handle errors properly | [Exceptions](exceptions.md) |
| Validate / format amounts | [Utilities](utilities.md) |

### By class

- **[`StakeAPI`](client.md)** — `get_user_balance()`, `get_casino_games()`, `get_sports_events()`, `place_bet()`, `get_bet_history()`, `get_user_profile()`, `_graphql_request()`
- **[`AuthManager`](auth-manager.md)** — `set_access_token()`, `is_token_expired()`, `extract_access_token_from_curl()`, `get_cookies()`
- **[`User`](models.md#class-user)** — `id`, `username`, `verified`, `country`, `currency`
- **[`Game`](models.md#class-game)** — `name`, `category`, `provider`, `rtp`, `min_bet`, `max_bet`
- **[`SportEvent`](models.md#class-sportevent)** — `home_team`, `away_team`, `odds`, `live`, `start_time`
- **[`Bet`](models.md#class-bet)** — `amount`, `potential_payout`, `status`, `placed_at`
- **[`Transaction`](models.md#class-transaction)** — `type`, `amount`, `currency`, `status`
- **[`Statistics`](models.md#class-statistics)** — `total_bets`, `win_rate`, `biggest_win`

---

## All Methods at a Glance

### `StakeAPI` — Casino

| Method | Returns | Description |
|:-------|:--------|:------------|
| `get_casino_games(category=None)` | `List[Game]` | List available games, optionally filtered |
| `get_game_details(game_id)` | `Game` | Full details for a single game |

### `StakeAPI` — Sports

| Method | Returns | Description |
|:-------|:--------|:------------|
| `get_sports_events(sport=None)` | `List[SportEvent]` | Live and upcoming events |

### `StakeAPI` — User

| Method | Returns | Description |
|:-------|:--------|:------------|
| `get_user_profile()` | `User` | Profile: username, country, verified |
| `get_user_balance()` | `Dict` | Available and vault balances by currency |

### `StakeAPI` — Betting

| Method | Returns | Description |
|:-------|:--------|:------------|
| `place_bet(bet_data)` | `Bet` | Submit a bet |
| `get_bet_history(limit=50)` | `List[Bet]` | Recent bet history |

### `StakeAPI` — Low-level

| Method | Returns | Description |
|:-------|:--------|:------------|
| `_graphql_request(query, variables, operation_name)` | `Dict` | Raw GraphQL call |
| `_request(method, endpoint, params, data)` | `Dict` | Raw HTTP call |
| `close()` | — | Close the HTTP session |

### `AuthManager`

| Method | Returns | Description |
|:-------|:--------|:------------|
| `get_auth_headers()` | `Dict[str, str]` | Headers with access token |
| `get_cookies()` | `Dict[str, str]` | Session cookie dict |
| `set_access_token(token, expires_in)` | — | Store/update the token |
| `set_session_cookie(cookie)` | — | Store/update the session cookie |
| `is_token_expired()` | `bool` | `True` if token is stale |
| `clear_tokens()` | — | Wipe all stored credentials |
| `extract_access_token_from_curl(cmd)` *(static)* | `Optional[str]` | Parse token from cURL |
| `extract_session_from_curl(cmd)` *(static)* | `Optional[str]` | Parse session from cURL |

### Utilities

| Function | Returns | Description |
|:---------|:--------|:------------|
| `validate_api_key(key)` | `bool` | Format check |
| `safe_decimal(value)` | `Optional[Decimal]` | Safe type conversion |
| `parse_datetime(s)` | `Optional[datetime]` | ISO 8601 parsing |
| `format_currency(amount, currency)` | `str` | Display string |
| `calculate_win_rate(wins, total)` | `float` | Win % |
| `validate_bet_amount(amount, min, max)` | `bool` | Range check |
| `sanitize_game_name(name)` | `str` | Safe string |

---

{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

{: .note }
> All API methods require a valid [Stake.com account](https://stake.com/?c=WY7953wQ) and a `cf_clearance` cookie. New to Stake? [Sign up here](https://stake.com/?c=WY7953wQ).
