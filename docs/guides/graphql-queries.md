---
layout: default
title: GraphQL Queries
parent: Guides
nav_order: 5
---

# GraphQL Queries
{: .fs-9 }

Harness the full power of Stake.com's GraphQL API for maximum flexibility and control.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## Overview

Stake.com's API is powered by GraphQL, giving you fine-grained control over exactly what data you request. StakeAPI provides convenient wrapper methods, but you can also execute raw GraphQL queries for maximum flexibility.

## Making GraphQL Requests

Use the `_graphql_request` method to execute any GraphQL query:

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        query = """
        query UserBalances {
          user {
            id
            balances {
              available {
                amount
                currency
              }
            }
          }
        }
        """
        
        data = await client._graphql_request(
            query=query,
            operation_name="UserBalances"
        )
        
        print(data)

asyncio.run(main())
```

## Built-in Queries

StakeAPI includes pre-built GraphQL queries in the `GraphQLQueries` class:

### User Balances

```python
from stakeapi.endpoints import GraphQLQueries

async with StakeAPI(access_token="your_token") as client:
    data = await client._graphql_request(
        query=GraphQLQueries.USER_BALANCES,
        operation_name="UserBalances"
    )
    
    for balance in data["user"]["balances"]["available"]:
        print(f"{balance['currency']}: {balance['amount']}")
```

### User Profile

```python
data = await client._graphql_request(
    query=GraphQLQueries.USER_PROFILE,
    operation_name="UserProfile"
)

user = data["user"]
print(f"Name: {user['name']}")
print(f"Email Verified: {user['isEmailVerified']}")
print(f"VIP Level: {user['level']}")
```

### Casino Games (Paginated)

```python
data = await client._graphql_request(
    query=GraphQLQueries.CASINO_GAMES,
    variables={
        "first": 50,
        "categorySlug": "slots"
    },
    operation_name="CasinoGames"
)

games = data["casinoGames"]["edges"]
for edge in games:
    game = edge["node"]
    print(f"{game['name']} by {game['provider']['name']}")

# Check for more pages
page_info = data["casinoGames"]["pageInfo"]
if page_info["hasNextPage"]:
    print(f"More games available after cursor: {page_info['endCursor']}")
```

### Sports Events

```python
data = await client._graphql_request(
    query=GraphQLQueries.SPORTS_EVENTS,
    variables={
        "first": 30,
        "sportSlug": "football"
    },
    operation_name="SportsEvents"
)

for edge in data["sportsEvents"]["edges"]:
    event = edge["node"]
    print(f"{event['name']}")
    for market in event.get("markets", []):
        for outcome in market.get("outcomes", []):
            print(f"  {outcome['name']}: {outcome['odds']}")
```

### Bet History (Paginated)

```python
data = await client._graphql_request(
    query=GraphQLQueries.BET_HISTORY,
    variables={"first": 25},
    operation_name="BetHistory"
)

for edge in data["user"]["bets"]["edges"]:
    bet = edge["node"]
    print(f"Game: {bet['game']['name']}")
    print(f"  {bet['amount']} {bet['currency']} → {bet['payout']} ({bet['outcome']})")
```

## Writing Custom Queries

You can write any GraphQL query that Stake.com supports:

```python
custom_query = """
query MyCustomQuery($limit: Int!) {
  user {
    id
    name
    balances {
      available {
        amount
        currency
      }
    }
    bets(first: $limit) {
      edges {
        node {
          id
          amount
          payout
          outcome
          createdAt
          game {
            name
          }
        }
      }
    }
  }
}
"""

data = await client._graphql_request(
    query=custom_query,
    variables={"limit": 10},
    operation_name="MyCustomQuery"
)
```

## Pagination

Stake.com uses cursor-based pagination. Here's how to paginate through all results:

```python
async def get_all_casino_games(client):
    """Fetch all casino games with pagination."""
    all_games = []
    cursor = None
    
    while True:
        variables = {"first": 100}
        if cursor:
            variables["after"] = cursor
        
        data = await client._graphql_request(
            query=GraphQLQueries.CASINO_GAMES,
            variables=variables,
            operation_name="CasinoGames"
        )
        
        edges = data["casinoGames"]["edges"]
        all_games.extend(edge["node"] for edge in edges)
        
        page_info = data["casinoGames"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        
        cursor = page_info["endCursor"]
        print(f"Fetched {len(all_games)} games so far...")
    
    return all_games
```

## GraphQL Request Parameters

| Parameter | Type | Required | Description |
|:----------|:-----|:---------|:------------|
| `query` | `str` | Yes | The GraphQL query string |
| `variables` | `Dict` | No | Query variables |
| `operation_name` | `str` | No | The operation name |

## Error Handling for GraphQL

GraphQL errors are returned in the response, not as HTTP status codes:

```python
from stakeapi.exceptions import StakeAPIError

try:
    data = await client._graphql_request(
        query="{ invalid_query }",
        operation_name="BadQuery"
    )
except StakeAPIError as e:
    if "GraphQL errors" in str(e):
        print(f"Query failed: {e}")
```

## GraphQL Tips

1. **Request only what you need** — GraphQL lets you specify exact fields
2. **Use variables** — Never string-interpolate values into queries
3. **Include `__typename`** — Helps with debugging and caching
4. **Paginate large results** — Don't request thousands of records at once
5. **Name your operations** — Makes debugging much easier

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

{: .note }
> Want to explore the full Stake.com GraphQL API? [Sign up on Stake.com](https://stake.com/?c=WY7953wQ), open Developer Tools, and discover all available queries.
