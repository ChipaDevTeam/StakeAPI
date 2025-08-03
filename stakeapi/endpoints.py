"""API endpoints and GraphQL queries for StakeAPI."""


class Endpoints:
    """API endpoint constants."""
    
    # GraphQL endpoint
    GRAPHQL = "/_api/graphql"
    
    # Legacy REST endpoints (if any still exist)
    API_BASE = "/api/v1"
    
    # Authentication
    AUTH_LOGIN = f"{API_BASE}/auth/login"
    AUTH_LOGOUT = f"{API_BASE}/auth/logout"
    AUTH_REFRESH = f"{API_BASE}/auth/refresh"
    
    # User endpoints
    USER_PROFILE = f"{API_BASE}/user/profile"
    USER_BALANCE = f"{API_BASE}/user/balance"
    USER_STATISTICS = f"{API_BASE}/user/statistics"
    USER_TRANSACTIONS = f"{API_BASE}/user/transactions"
    
    # Casino endpoints
    CASINO_GAMES = f"{API_BASE}/casino/games"
    CASINO_GAME_DETAILS = f"{API_BASE}/casino/games/{{game_id}}"
    CASINO_PROVIDERS = f"{API_BASE}/casino/providers"
    CASINO_CATEGORIES = f"{API_BASE}/casino/categories"
    
    # Sports endpoints
    SPORTS_EVENTS = f"{API_BASE}/sports/events"
    SPORTS_EVENT_DETAILS = f"{API_BASE}/sports/events/{{event_id}}"
    SPORTS_LEAGUES = f"{API_BASE}/sports/leagues"
    SPORTS_ODDS = f"{API_BASE}/sports/odds"
    
    # Betting endpoints
    PLACE_BET = f"{API_BASE}/bets/place"
    BET_HISTORY = f"{API_BASE}/bets/history"
    BET_DETAILS = f"{API_BASE}/bets/{{bet_id}}"
    CANCEL_BET = f"{API_BASE}/bets/{{bet_id}}/cancel"
    
    # Live endpoints
    LIVE_GAMES = f"{API_BASE}/live/games"
    LIVE_EVENTS = f"{API_BASE}/live/events"
    
    # Promotions
    PROMOTIONS = f"{API_BASE}/promotions"
    PROMOTION_DETAILS = f"{API_BASE}/promotions/{{promo_id}}"


class GraphQLQueries:
    """GraphQL query constants for stake.com API."""
    
    USER_BALANCES = """
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
    """
    
    USER_PROFILE = """
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
    """
    
    CASINO_GAMES = """
    query CasinoGames($first: Int, $after: String, $categorySlug: String) {
      casinoGames(first: $first, after: $after, categorySlug: $categorySlug) {
        edges {
          node {
            id
            name
            slug
            provider {
              name
              __typename
            }
            thumb
            category {
              name
              slug
              __typename
            }
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
    """
    
    SPORTS_EVENTS = """
    query SportsEvents($first: Int, $sportSlug: String) {
      sportsEvents(first: $first, sportSlug: $sportSlug) {
        edges {
          node {
            id
            name
            startTime
            sport {
              name
              slug
              __typename
            }
            league {
              name
              slug
              __typename
            }
            competitors {
              name
              __typename
            }
            markets {
              name
              outcomes {
                name
                odds
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
    }
    """
    
    BET_HISTORY = """
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
              game {
                name
                slug
                __typename
              }
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
    """
