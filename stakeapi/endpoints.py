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


# Shared fragments for the public queries in GraphQLQueries
_FIXTURE_FRAGMENT = """
    fragment LibFixture on SportFixture {
      id
      stakeFixtureId
      status
      slug
      name
      provider
      marketCount(status: [active, suspended])
      data {
        __typename
        ... on SportFixtureDataMatch {
          startTime
          competitors {
            name
            abbreviation
            countryCode
          }
          teams {
            name
            qualifier
          }
        }
        ... on SportFixtureDataOutright {
          name
          startTime
          endTime
        }
      }
      tournament {
        id
        name
        slug
        category {
          id
          name
          slug
          sport {
            id
            name
            slug
          }
        }
      }
      eventStatus {
        __typename
        ... on SportFixtureEventStatusData {
          homeScore
          awayScore
          matchStatus
          clock {
            matchTime
            remainingTime
          }
        }
        ... on EsportFixtureEventStatus {
          homeScore
          awayScore
          matchStatus
        }
      }
    }
"""

_SPORT_GROUP_FRAGMENT = """
    fragment LibSportGroup on SportGroup {
      name
      translation
      rank
      templates(limit: 10, includeEmpty: true) {
        extId
        name
        rank
        markets(limit: $marketLimit) {
          id
          name
          status
          extId
          specifiers
          provider
          outcomes {
            id
            name
            odds
            active
            probabilities
          }
        }
      }
    }
"""

_GAME_FRAGMENT = """
    fragment LibGame on GameKuratorGame {
      id
      name
      slug
      type
      theme
      description
      edge
      active
      icon
      thumbnailUrl
      playerCount
      isDemoEnabled
      providerGroup {
        id
        name
        slug
      }
      groupGames {
        group {
          id
          slug
          translation
          type
        }
      }
    }
"""


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
    
    # Validated against the live API (fields confirmed to exist on type User)
    USER_PROFILE = """
    query UserProfile {
      user {
        id
        name
        email
        hasEmailVerified
        createdAt
        __typename
      }
    }
    """
    
    # UNVERIFIED DRAFT — this query shape does not match the live schema;
    # kept only as a starting point for future work
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
    
    # Validated against the live API — public realtime feed of house bets
    # across all bet types (captured from the site's own AllHouseBets query)
    ALL_HOUSE_BETS = """
    query AllHouseBets($limit: Int = 10) {
      allHouseBets(limit: $limit) {
        ...RealtimeHouseBet
      }
    }

    fragment RealtimeHouseBet on Bet {
      id
      iid
      game {
        name
        icon
      }
      bet {
        __typename
        ... on CasinoBet {
          id
          active
          payoutMultiplier
          amountMultiplier
          amount
          payout
          updatedAt
          currency
          user {
            id
            name
            preferenceHideBets
          }
        }
        ... on EvolutionBet {
          id
          amount
          currency
          createdAt
          payout
          payoutMultiplier
          user {
            id
            name
            preferenceHideBets
          }
        }
        ... on MultiplayerCrashBet {
          id
          payoutMultiplier
          amount
          payout
          currency
          updatedAt
          user {
            id
            name
            preferenceHideBets
          }
        }
        ... on MultiplayerSlideBet {
          id
          payoutMultiplier
          amount
          payout
          currency
          updatedAt
          createdAt
          user {
            id
            name
            preferenceHideBets
          }
        }
        ... on SoftswissBet {
          id
          amount
          currency
          updatedAt
          payout
          payoutMultiplier
          user {
            id
            name
            preferenceHideBets
          }
        }
        ... on ThirdPartyBet {
          id
          amount
          currency
          updatedAt
          createdAt
          payout
          payoutMultiplier
          user {
            id
            name
            preferenceHideBets
          }
        }
        ... on ZooBet {
          id
          amount
          currency
          updatedAt
          createdAt
          payout
          payoutMultiplier
          user {
            id
            name
            preferenceHideBets
          }
        }
      }
    }
    """

    # Validated against the live API — currency exchange rates (vs USD)
    # and fiat currency configuration
    CURRENCY_CONFIGURATION = """
    query CurrencyConfiguration($isAcp: Boolean!) {
      currencyConfiguration(isAcp: $isAcp) {
        baseRates {
          currency
          baseRate
        }
        launchedFiatCurrencies
        displayFiatCurrencies
      }
    }
    """

    # Validated against the live API — sport landing page (captured from the
    # site's own SportIndex query): fixtures, tournaments and categories
    SPORT_INDEX = """
    query SportIndex($sport: String!, $group: String!, $type: SportSearchEnum = popular, $marketLimit: Int = 1) {
      slugSport(sport: $sport) {
        __typename
        id
        name
        templates(group: $group) {
          __typename
          id
          name
          extId
        }
        firstTournament: tournamentList(type: $type, limit: 1) {
          __typename
          id
          name
          slug
          category {
            __typename
            id
            slug
            name
            countryCode
          }
          fixtureCount(type: $type)
          fixtureList(type: $type, limit: 10) {
            __typename
            ...FixturePreview
            groups(groups: [$group], status: [active, suspended, deactivated]) {
              __typename
              ...SportGroupTemplates
            }
          }
        }
        tournamentList(type: $type, limit: 5) {
          __typename
          id
          name
          slug
          fixtureCount(type: $type)
          category {
            __typename
            id
            slug
            name
            countryCode
          }
        }
        categoryList(type: $type, limit: 100) {
          __typename
          id
          slug
          name
          countryCode
          fixtureCount(type: $type)
          tournamentList(type: $type, limit: 100) {
            __typename
            id
            slug
            name
            fixtureCount(type: $type)
          }
        }
      }
    }

    fragment FixturePreview on SportFixture {
      __typename
      id
      stakeFixtureId
      status
      slug
      name
      provider
      marketCount(status: [active, suspended])
      extId
      data {
        __typename
        ... on SportFixtureDataMatch {
          startTime
          isOutright
          competitors {
            __typename
            name
            extId
            countryCode
            abbreviation
          }
          teams {
            __typename
            extId
            name
            qualifier
          }
        }
        ... on SportFixtureDataOutright {
          isOutright
          name
          startTime
          endTime
        }
      }
      tournament {
        __typename
        id
        name
        slug
        category {
          __typename
          id
          name
          slug
          sport {
            __typename
            id
            name
            slug
          }
        }
      }
      eventStatus {
        __typename
        ... on SportFixtureEventStatusData {
          homeScore
          awayScore
          matchStatus
          clock {
            __typename
            matchTime
            remainingTime
          }
        }
      }
    }

    fragment SportGroupTemplates on SportGroup {
      __typename
      name
      translation
      rank
      templates(limit: 10, includeEmpty: true) {
        __typename
        extId
        rank
        name
        markets(limit: $marketLimit) {
          __typename
          id
          name
          status
          extId
          specifiers
          provider
          templateExtId
          outcomes {
            __typename
            id
            active
            odds
            probabilities
            name
          }
        }
      }
    }
    """

    # UNVERIFIED DRAFT — this query shape does not match the live schema;
    # kept only as a starting point for future work
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
    
    # Validated against the live API — bet history is user.houseBetList;
    # 'game' on the outer Bet is an object, while CasinoBet.game is an enum
    BET_HISTORY = """
    query BetHistory($limit: Int!, $offset: Int!) {
      user {
        houseBetList(limit: $limit, offset: $offset) {
          id
          iid
          game {
            name
            icon
            slug
            __typename
          }
          bet {
            __typename
            ... on CasinoBet {
              id
              active
              payoutMultiplier
              payout
              amount
              currency
              game
              createdAt
              updatedAt
              user {
                id
                name
                __typename
              }
              __typename
            }
          }
          __typename
        }
        __typename
      }
    }
    """

    # ------------------------------------------------------------------
    # Public (no login) queries. Field sets are trimmed versions of the
    # site's own operations of the same name, validated against the live API.
    # ------------------------------------------------------------------

    SPORT_LIST = """
    query SportListMenu($type: SportSearchEnum!, $limit: Int = 100, $offset: Int = 0, $sportType: SportTypeEnum) {
      sportList(type: $type, limit: $limit, offset: $offset, sportType: $sportType) {
        id
        name
        slug
        fixtureCount(type: $type)
      }
    }
    """

    TRENDING_SPORTS = """
    query TrendingSportsQ($limit: Int = 10, $offset: Int = 0) {
      topSportList(limit: $limit, offset: $offset) {
        id
        name
        slug
        sportType
      }
    }
    """

    FIXTURE_LIST = """
    query FixtureList($type: SportSearchEnum!, $groups: String!, $offset: Int!, $limit: Int!, $sportType: SportTypeEnum, $marketLimit: Int = 1) {
      fixtureCount(type: $type)
      fixtureList(type: $type, limit: $limit, offset: $offset, sportType: $sportType) {
        ...LibFixture
        groups(groups: [$groups], status: [active, suspended, deactivated]) {
          ...LibSportGroup
        }
      }
    }
    """ + _FIXTURE_FRAGMENT + _SPORT_GROUP_FRAGMENT

    SPORT_TOURNAMENT_FIXTURES = """
    query SportTournamentFixtureList($sport: String!, $groups: String!, $type: SportSearchEnum!, $tournamentOffset: Int = 0, $tournamentLimit: Int = 25, $fixtureLimit: Int = 20, $marketLimit: Int = 1) {
      slugSport(sport: $sport) {
        id
        name
        slug
        tournamentList(type: $type, limit: $tournamentLimit, offset: $tournamentOffset) {
          id
          name
          slug
          category {
            id
            name
            slug
          }
          fixtureCount(type: $type)
          fixtureList(type: $type, limit: $fixtureLimit) {
            ...LibFixture
            groups(groups: [$groups], status: [active, suspended, deactivated]) {
              ...LibSportGroup
            }
          }
        }
      }
    }
    """ + _FIXTURE_FRAGMENT + _SPORT_GROUP_FRAGMENT

    SLUG_TOURNAMENT = """
    query SlugTournament($sport: String!, $category: String!, $tournament: String!, $type: SportSearchEnum!, $groups: [String!]!, $limit: Int = 10, $offset: Int = 0, $marketLimit: Int = 1) {
      slugTournament(sport: $sport, category: $category, tournament: $tournament) {
        id
        name
        slug
        fixtureCount(type: $type)
        fixtureList(type: $type, limit: $limit, offset: $offset) {
          ...LibFixture
          groups(groups: $groups, status: [active, suspended, deactivated]) {
            ...LibSportGroup
          }
        }
      }
    }
    """ + _FIXTURE_FRAGMENT + _SPORT_GROUP_FRAGMENT

    SEARCH_SPORTS = """
    query searchQuerySports($query: String!, $groups: String!, $limit: Int, $offset: Int, $marketLimit: Int = 1) {
      sportFixtureQuery(limit: $limit, offset: $offset, query: $query) {
        fixture {
          ... on SportFixture {
            ...LibFixture
            groups(groups: [$groups], status: [active, suspended, deactivated]) {
              ...LibSportGroup
            }
          }
        }
      }
    }
    """ + _FIXTURE_FRAGMENT + _SPORT_GROUP_FRAGMENT

    TRENDING_MATCHES = """
    query SportBetTrendingMatches($sortBy: SportHomepageTrendingOrderByEnum!, $groups: [String!], $sportId: String, $marketLimit: Int = 1) {
      sportHomepageTrendingMatches(sortBy: $sortBy, sportId: $sportId) {
        fixtureStatistics {
          totalUserCount
        }
        outcomeStatistics {
          id
          totalBetCount
        }
        fixture {
          ...LibFixture
          groups(groups: $groups) {
            ...LibSportGroup
          }
        }
      }
    }
    """ + _FIXTURE_FRAGMENT + _SPORT_GROUP_FRAGMENT

    TOP_PICKS = """
    query SportBetTopPicks($sortBy: SportHomepageTrendingOrderByEnum!, $sportId: String) {
      sportHomepageTrendingTopPicks(sortBy: $sortBy, sportId: $sportId) {
        statistics {
          totalBetValue
          totalUserCount
        }
        outcome {
          ... on SportMarketOutcome {
            id
            name
            odds
            active
            market {
              id
              name
              status
              fixture {
                ...LibFixture
              }
            }
          }
        }
      }
    }
    """ + _FIXTURE_FRAGMENT

    TOP_MULTIS = """
    query SportBetTopMultis {
      sportHomepageTrendingTopMultis {
        selectionsHash
        legCount
        statistics {
          totalUserCount
        }
        outcomes {
          outcome {
            id
            name
            odds
            active
            market {
              id
              name
              status
              fixture {
                ...LibFixture
              }
            }
          }
        }
      }
    }
    """ + _FIXTURE_FRAGMENT

    CASINO_GROUP = """
    query SlugKuratorGroup($slug: String!, $limit: Int!, $offset: Int!, $sort: GameKuratorGroupGameSortEnum = popular7d) {
      slugKuratorGroup(slug: $slug) {
        id
        name
        slug
        translation
        type
        gameCount
        groupGamesList(limit: $limit, offset: $offset, sort: $sort) {
          game {
            ...LibGame
          }
        }
      }
    }
    """ + _GAME_FRAGMENT

    CASINO_GAME = """
    query SlugKuratorGame($slug: String!) {
      slugKuratorGame(slug: $slug) {
        ...LibGame
      }
    }
    """ + _GAME_FRAGMENT

    SEARCH_CASINO = """
    query searchQueryCasino($query: String!, $limit: Int, $offset: Int) {
      kuratorGameQuery(query: $query, limit: $limit, offset: $offset) {
        ...LibGame
      }
    }
    """ + _GAME_FRAGMENT

    CASINO_COLLECTION = """
    query KuratorCollection($type: GameKuratorCollectionEnum!, $sort: GameKuratorCollectionSortEnum, $filter: GameKuratorCollectionFilterEnum) {
      kuratorCollection(type: $type, sort: $sort, filter: $filter) {
        id
        group {
          id
          slug
          translation
          gameCount
          playerCount
        }
      }
    }
    """

    GAME_PAYOUTS = """
    query GamePayouts {
      info {
        kenoPayouts {
          payouts
          risk
        }
        plinkoPayouts {
          payouts
          rows
          risk
        }
        wheelPayouts {
          payouts
          rows
          risk
        }
      }
    }
    """

    CURRENCY_LIMITS = """
    query CurrencyLimits {
      info {
        currencies {
          name
          betMax {
            value
          }
          betMaxProfit {
            value
          }
        }
      }
    }
    """

    CRASH_HISTORY = """
    query CrashGameListHistory($limit: Int, $offset: Int) {
      crashGameList(limit: $limit, offset: $offset) {
        id
        startTime
        crashpoint
        hash {
          id
          hash
        }
      }
    }
    """

    CRASH_GAME = """
    query CrashGameLookup($gameId: String!) {
      crashGame(gameId: $gameId) {
        id
        status
        startTime
        crashpoint
        seed {
          id
          seed
        }
        hash {
          id
          hash
          number
        }
        leaderboard {
          id
          user {
            id
            name
          }
          payoutMultiplier
          amount
          payout
          currency
          cashoutAt
        }
      }
    }
    """

    SLIDE_HISTORY = """
    query SlideGameListHistory($limit: Int, $offset: Int) {
      slideGameList(limit: $limit, offset: $offset) {
        id
        multiplier
        startTime
        hash {
          hash
        }
      }
    }
    """

    CHALLENGES = """
    query ChallengePublicList($limit: Int!, $offset: Int!, $sort: ChallengeSort!, $direction: ChallengeSortDirection) {
      challengeUnauthenticatedUserCount
      challengeUnauthenticatedUserList(limit: $limit, offset: $offset, sort: $sort, direction: $direction) {
        id
        type
        active
        award
        claimCount
        claimMax
        currency
        minBetUsd
        betCurrency
        targetMultiplier
        startAt
        expireAt
        completedAt
        game {
          id
          name
          slug
        }
        creatorUser {
          id
          name
        }
        wins {
          id
          claimedBy {
            id
            name
          }
        }
      }
    }
    """

    ACTIVE_RACES = """
    query ActiveRaces($limit: Int = 10) {
      activeRaces {
        id
        name
        description
        currency
        type
        startTime
        endTime
        status
        scope
        leaderboard(limit: $limit) {
          position
          user {
            id
            name
          }
          wageredAmount
          payoutAmount
          percentage
          currency
        }
      }
    }
    """

    HIGHROLLER_HOUSE_BETS = ALL_HOUSE_BETS.replace(
        "query AllHouseBets", "query HighrollerHouseBets"
    ).replace("allHouseBets(limit", "highrollerHouseBets(limit")
