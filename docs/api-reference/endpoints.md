---
layout: default
title: Endpoints & GraphQL
parent: API Reference
nav_order: 4
---

# Endpoints & GraphQL Queries
{: .fs-9 }

All URL constants and pre-built GraphQL queries used by StakeAPI.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

StakeAPI provides two classes for working with Stake.com's backend:

- **`Endpoints`** — String constants for every REST-style URL path.
- **`GraphQLQueries`** — Ready-to-use GraphQL query strings for the primary operations.

The `StakeAPI` client uses these internally, but you can import them directly for custom requests via `_request()` or `_graphql_request()`.

**Import:**

```python
from stakeapi.endpoints import Endpoints, GraphQLQueries
```

---

## Class: `Endpoints`

A namespace of URL path constants. All paths are relative to `base_url` (default `https://stake.com`).

### GraphQL Endpoint

| Constant | Value | Description |
|:---------|:------|:------------|
| `Endpoints.GRAPHQL` | `/_api/graphql` | Primary GraphQL endpoint — **all modern API calls use this** |

### Base

| Constant | Value |
|:---------|:------|
| `Endpoints.API_BASE` | `/api/v1` |

### Authentication

| Constant | Path | Description |
|:---------|:-----|:------------|
| `Endpoints.AUTH_LOGIN` | `/api/v1/auth/login` | Log in with credentials |
| `Endpoints.AUTH_LOGOUT` | `/api/v1/auth/logout` | Invalidate session |
| `Endpoints.AUTH_REFRESH` | `/api/v1/auth/refresh` | Refresh access token |

### User

| Constant | Path | Description |
|:---------|:-----|:------------|
| `Endpoints.USER_PROFILE` | `/api/v1/user/profile` | Fetch user profile |
| `Endpoints.USER_BALANCE` | `/api/v1/user/balance` | Fetch wallet balance |
| `Endpoints.USER_STATISTICS` | `/api/v1/user/statistics` | Fetch betting statistics |
| `Endpoints.USER_TRANSACTIONS` | `/api/v1/user/transactions` | Fetch transaction history |

### Casino

| Constant | Path | Description |
|:---------|:-----|:------------|
| `Endpoints.CASINO_GAMES` | `/api/v1/casino/games` | List all casino games |
| `Endpoints.CASINO_GAME_DETAILS` | `/api/v1/casino/games/{game_id}` | Details for a single game |
| `Endpoints.CASINO_PROVIDERS` | `/api/v1/casino/providers` | List game providers |
| `Endpoints.CASINO_CATEGORIES` | `/api/v1/casino/categories` | List game categories |

### Sports

| Constant | Path | Description |
|:---------|:-----|:------------|
| `Endpoints.SPORTS_EVENTS` | `/api/v1/sports/events` | List sports events |
| `Endpoints.SPORTS_EVENT_DETAILS` | `/api/v1/sports/events/{event_id}` | Single event details |
| `Endpoints.SPORTS_LEAGUES` | `/api/v1/sports/leagues` | List available leagues |
| `Endpoints.SPORTS_ODDS` | `/api/v1/sports/odds` | Current odds |

### Betting

| Constant | Path | Description |
|:---------|:-----|:------------|
| `Endpoints.PLACE_BET` | `/api/v1/bets/place` | Submit a bet |
| `Endpoints.BET_HISTORY` | `/api/v1/bets/history` | Fetch bet history |
| `Endpoints.BET_DETAILS` | `/api/v1/bets/{bet_id}` | Single bet details |
| `Endpoints.CANCEL_BET` | `/api/v1/bets/{bet_id}/cancel` | Cancel a pending bet |

### Live

| Constant | Path | Description |
|:---------|:-----|:------------|
| `Endpoints.LIVE_GAMES` | `/api/v1/live/games` | Active live casino games |
| `Endpoints.LIVE_EVENTS` | `/api/v1/live/events` | In-play sports events |

### Promotions

| Constant | Path | Description |
|:---------|:-----|:------------|
| `Endpoints.PROMOTIONS` | `/api/v1/promotions` | List all promotions |
| `Endpoints.PROMOTION_DETAILS` | `/api/v1/promotions/{promo_id}` | Single promotion details |

### Usage Example

```python
from stakeapi import StakeAPI
from stakeapi.endpoints import Endpoints

async with StakeAPI(access_token="...", cf_clearance="...") as client:
    # Use a constant directly in a raw request
    data = await client._request("GET", Endpoints.USER_PROFILE)
    print(data)

    # Format path templates
    endpoint = Endpoints.CASINO_GAME_DETAILS.format(game_id="plinko")
    # → "/api/v1/casino/games/plinko"
    game_data = await client._request("GET", endpoint)
```

{: .note }
> Stake.com has largely migrated to GraphQL. The REST endpoints above exist as constants for convenience and forward-compatibility, but the `/_api/graphql` endpoint is the one actively used in production today.

---

## Class: `GraphQLQueries`

Pre-built GraphQL query strings. Each is a multi-line string you can pass directly to `_graphql_request()`. You can also use them as starting points for writing custom queries.

---

### `GraphQLQueries.USER_BALANCES`

Fetches the authenticated user's wallet balances — both the spendable (`available`) amount and the locked (`vault`) amount — across all currencies.

```graphql
query UserBalances {
  user {
    id
    balances {
      available {
        amount
        currency
        __typename
      }
      vault {
        amount
        currency
        __typename
      }
      __typename
    }
    __typename
  }
}
```

**Usage:**

```python
from stakeapi.endpoints import GraphQLQueries

async with StakeAPI(access_token="...", cf_clearance="...") as client:
    data = await client._graphql_request(
        query=GraphQLQueries.USER_BALANCES,
        operation_name="UserBalances",
    )
    for entry in data["user"]["balances"]:
        currency = entry["available"]["currency"]
        amount   = entry["available"]["amount"]
        print(f"  {currency}: {amount}")
```

---

### `GraphQLQueries.USER_PROFILE`

Fetches the authenticated user's profile including ID, name, email, verification status, country, and level.

```graphql
query UserProfile {
  user {
    id
    name
    email
    isEmailVerified
    country
    level
    statistics {
      __typename
    }
    __typename
  }
}
```

**Usage:**

```python
data = await client._graphql_request(
    query=GraphQLQueries.USER_PROFILE,
    operation_name="UserProfile",
)
print(data["user"]["name"])
print(data["user"]["isEmailVerified"])
```

---

### `GraphQLQueries.CASINO_GAMES`

Paginated list of casino games with provider and category info.

```graphql
query CasinoGames($first: Int, $after: String, $categorySlug: String) {
  casinoGames(first: $first, after: $after, categorySlug: $categorySlug) {
    edges {
      node {
        id
        name
        slug
        provider { name __typename }
        thumb
        category { name slug __typename }
        __typename
      }
      __typename
    }
    pageInfo {
      hasNextPage
      endCursor
      __typename
    }
    __typename
  }
}
```

**Variables:**

| Variable | Type | Description |
|:---------|:-----|:------------|
| `first` | `Int` | Number of games per page (e.g. `50`) |
| `after` | `String` | Cursor for pagination (from `pageInfo.endCursor`) |
| `categorySlug` | `String` | Filter by category, e.g. `"slots"`, `"originals"` |

**Usage:**

```python
# First page of slots
data = await client._graphql_request(
    query=GraphQLQueries.CASINO_GAMES,
    variables={"first": 20, "categorySlug": "slots"},
    operation_name="CasinoGames",
)

games = data["casinoGames"]["edges"]
for edge in games:
    g = edge["node"]
    print(f"{g['name']} by {g['provider']['name']}")

# Paginate to next page
page_info = data["casinoGames"]["pageInfo"]
if page_info["hasNextPage"]:
    next_data = await client._graphql_request(
        query=GraphQLQueries.CASINO_GAMES,
        variables={"first": 20, "after": page_info["endCursor"]},
        operation_name="CasinoGames",
    )
```

---

### `GraphQLQueries.SPORTS_EVENTS`

Paginated sports events with competitors, league, and market odds.

```graphql
query SportsEvents($first: Int, $sportSlug: String) {
  sportsEvents(first: $first, sportSlug: $sportSlug) {
    edges {
      node {
        id
        name
        startTime
        sport     { name slug __typename }
        league    { name slug __typename }
        competitors { name __typename }
        markets {
          name
          outcomes { name odds __typename }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
```

**Variables:**

| Variable | Type | Description |
|:---------|:-----|:------------|
| `first` | `Int` | Number of events per page |
| `sportSlug` | `String` | Filter by sport, e.g. `"football"`, `"basketball"` |

**Usage:**

```python
data = await client._graphql_request(
    query=GraphQLQueries.SPORTS_EVENTS,
    variables={"first": 10, "sportSlug": "football"},
    operation_name="SportsEvents",
)

for edge in data["sportsEvents"]["edges"]:
    event = edge["node"]
    teams = " vs ".join(c["name"] for c in event["competitors"])
    print(f"{teams} — {event['startTime']}")
    for market in event["markets"]:
        outcomes = {o["name"]: o["odds"] for o in market["outcomes"]}
        print(f"  {market['name']}: {outcomes}")
```

---

### `GraphQLQueries.BET_HISTORY`

Paginated bet history for the authenticated user with game info and payout details.

```graphql
query BetHistory($first: Int, $after: String) {
  user {
    bets(first: $first, after: $after) {
      edges {
        node {
          id
          amount
          currency
          multiplier
          payout
          createdAt
          updatedAt
          outcome
          game { name slug __typename }
          __typename
        }
        __typename
      }
      pageInfo {
        hasNextPage
        endCursor
        __typename
      }
      __typename
    }
    __typename
  }
}
```

**Variables:**

| Variable | Type | Description |
|:---------|:-----|:------------|
| `first` | `Int` | Number of bets per page |
| `after` | `String` | Cursor for pagination |

**Usage:**

```python
data = await client._graphql_request(
    query=GraphQLQueries.BET_HISTORY,
    variables={"first": 50},
    operation_name="BetHistory",
)

bets = data["user"]["bets"]["edges"]
for edge in bets:
    b = edge["node"]
    print(f"[{b['outcome']}] {b['amount']} {b['currency']} "
          f"× {b['multiplier']} = {b['payout']} on {b['game']['name']}")
```

---

## Writing Custom GraphQL Queries

You are not limited to the pre-built queries. Use `_graphql_request()` to send any valid Stake.com GraphQL query.

**Tips:**

1. Open [Stake.com](https://stake.com/?c=WY7953wQ) in your browser and log in
2. Open DevTools → **Network** tab → filter for `graphql`
3. Click any request to see the exact query and variables Stake.com's frontend sends
4. Copy the query and pass it to `_graphql_request()`

```python
# Custom query: fetch user's VIP level and rakeback rate
custom_query = """
query UserVIP {
  user {
    id
    name
    vipTier
    rakeback {
      percentage
      __typename
    }
    __typename
  }
}
"""

data = await client._graphql_request(
    query=custom_query,
    operation_name="UserVIP",
)
print(data["user"]["vipTier"])
```

{: .warning }
> Custom queries are not officially supported and may break if Stake.com changes its schema. Always test after Stake.com updates.

---

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}

---

## See Also

- [StakeAPI Client](client.md) — High-level methods that wrap these queries
- [Data Models](models.md) — Objects returned after parsing query results
- [GraphQL Guide](../guides/graphql-queries.md) — Deep-dive into raw GraphQL usage
- [Authentication Guide](../getting-started/authentication.md) — How to authenticate requests
