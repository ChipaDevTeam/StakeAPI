---
layout: default
title: Endpoints
parent: API Reference
nav_order: 4
---

# Endpoints & GraphQL Queries
{: .fs-9 }

Complete reference of API endpoints, routes, and built-in GraphQL queries.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Endpoints Class

All API endpoint constants are defined in the `Endpoints` class.

**Import:**

```python
from stakeapi.endpoints import Endpoints, GraphQLQueries
```

### Core

| Constant | Value | Description |
|:---------|:------|:------------|
| `GRAPHQL` | `/_api/graphql` | Main GraphQL endpoint |
| `API_BASE` | `/api/v1` | REST API base path |

### Authentication

| Constant | Path | Description |
|:---------|:-----|:------------|
| `AUTH_LOGIN` | `/api/v1/auth/login` | Login endpoint |
| `AUTH_LOGOUT` | `/api/v1/auth/logout` | Logout endpoint |
| `AUTH_REFRESH` | `/api/v1/auth/refresh` | Token refresh |

### User

| Constant | Path | Description |
|:---------|:-----|:------------|
| `USER_PROFILE` | `/api/v1/user/profile` | User profile |
| `USER_BALANCE` | `/api/v1/user/balance` | Account balance |
| `USER_STATISTICS` | `/api/v1/user/statistics` | Betting statistics |
| `USER_TRANSACTIONS` | `/api/v1/user/transactions` | Transaction history |

### Casino

| Constant | Path | Description |
|:---------|:-----|:------------|
| `CASINO_GAMES` | `/api/v1/casino/games` | List all games |
| `CASINO_GAME_DETAILS` | `/api/v1/casino/games/{game_id}` | Single game details |
| `CASINO_PROVIDERS` | `/api/v1/casino/providers` | Game providers |
| `CASINO_CATEGORIES` | `/api/v1/casino/categories` | Game categories |

### Sports

| Constant | Path | Description |
|:---------|:-----|:------------|
| `SPORTS_EVENTS` | `/api/v1/sports/events` | Sports events |
| `SPORTS_EVENT_DETAILS` | `/api/v1/sports/events/{event_id}` | Event details |
| `SPORTS_LEAGUES` | `/api/v1/sports/leagues` | Available leagues |
| `SPORTS_ODDS` | `/api/v1/sports/odds` | Odds data |

### Betting

| Constant | Path | Description |
|:---------|:-----|:------------|
| `PLACE_BET` | `/api/v1/bets/place` | Place a bet |
| `BET_HISTORY` | `/api/v1/bets/history` | Bet history |
| `BET_DETAILS` | `/api/v1/bets/{bet_id}` | Bet details |
| `CANCEL_BET` | `/api/v1/bets/{bet_id}/cancel` | Cancel a bet |

### Live

| Constant | Path | Description |
|:---------|:-----|:------------|
| `LIVE_GAMES` | `/api/v1/live/games` | Live casino games |
| `LIVE_EVENTS` | `/api/v1/live/events` | Live sports events |

### Promotions

| Constant | Path | Description |
|:---------|:-----|:------------|
| `PROMOTIONS` | `/api/v1/promotions` | Active promotions |
| `PROMOTION_DETAILS` | `/api/v1/promotions/{promo_id}` | Promotion details |

---

## GraphQL Queries

Pre-built GraphQL queries for common operations.

### `GraphQLQueries.USER_BALANCES`

Fetches user balance with available and vault amounts for all currencies.

```graphql
query UserBalances {
  user {
    id
    balances {
      available {
        amount
        currency
      }
      vault {
        amount
        currency
      }
    }
  }
}
```

### `GraphQLQueries.USER_PROFILE`

Fetches user profile information including VIP level.

```graphql
query UserProfile {
  user {
    id
    name
    email
    isEmailVerified
    country
    level
    statistics { ... }
  }
}
```

### `GraphQLQueries.CASINO_GAMES`

Paginated query for casino games with category filtering.

**Variables:**

| Variable | Type | Description |
|:---------|:-----|:------------|
| `first` | `Int` | Number of results per page |
| `after` | `String` | Cursor for pagination |
| `categorySlug` | `String` | Category filter |

### `GraphQLQueries.SPORTS_EVENTS`

Fetch sports events with markets and odds.

**Variables:**

| Variable | Type | Description |
|:---------|:-----|:------------|
| `first` | `Int` | Number of results |
| `sportSlug` | `String` | Sport filter |

### `GraphQLQueries.BET_HISTORY`

Paginated bet history with game details and outcomes.

**Variables:**

| Variable | Type | Description |
|:---------|:-----|:------------|
| `first` | `Int` | Number of results per page |
| `after` | `String` | Cursor for pagination |

---

## Using Endpoints

### Dynamic Path Parameters

Some endpoints have path parameters. Use Python's string formatting:

```python
# Game details
endpoint = Endpoints.CASINO_GAME_DETAILS.format(game_id="sweet-bonanza")
# Result: /api/v1/casino/games/sweet-bonanza

# Bet details
endpoint = Endpoints.BET_DETAILS.format(bet_id="bet_123")
# Result: /api/v1/bets/bet_123
```

{% include affiliate-banner.html %}

---

{: .note }
> Explore all available endpoints with a [Stake.com account](https://stake.com/?c=WY7953wQ). Use browser Developer Tools to discover additional queries.
