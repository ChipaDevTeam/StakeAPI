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


_SPORT_BET_FRAGMENT = """
    fragment LibSportBet on SportBet {
      id
      amount
      currency
      payout
      potentialMultiplier
      payoutMultiplier
      cashoutMultiplier
      customBet
      createdAt
      outcomes {
        id
        odds
        fixtureName
        fixture {
          id
          slug
          status
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
    query BetHistory($limit: Int!, $offset: Int!, $game: BetHouseEnum) {
      user {
        houseBetList(limit: $limit, offset: $offset, game: $game) {
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


    PUBLIC_CHATS = """
    query PublicChats {
      publicChats {
        id
        name
        isPublic
      }
    }
    """
    # ------------------------------------------------------------------
    # Account queries. USER_STATS is public (any username); the rest need a
    # logged-in session. Trimmed from the site's operations of the same name
    # and validated against the live schema.
    # ------------------------------------------------------------------

    USER_STATS = """
    query UserDetails($name: String!) {
      user(name: $name) {
        id
        name
        createdAt
        isHighroller
        isSportHighroller
        flags {
          flag
          rank
          createdAt
        }
        statisticScoped {
          scope
          currency
          bets
          wins
          losses
          ties
          betAmount
          betValue
        }
      }
    }
    """

    ACCOUNT_STATUS = """
    query UserKycInfo {
      user {
        id
        name
        email
        createdAt
        kycStatus
        hasEmailVerified
        hasPhoneNumberVerified
        isBanned
        isSuspended
        isSuspendedSportsbook
        selfExclude {
          id
          status
          active
          expireAt
        }
      }
    }
    """

    VIP_INFO = """
    query VipMeta {
      user {
        id
        flags {
          flag
        }
        flagProgress {
          flag
          progress
        }
        rakeback {
          enabled
          balances {
            currency
            availableAmount
            receivedAmount
          }
        }
        reload: faucet {
          id
          value
          baseValue
          active
          claimInterval
          lastClaim
          expireAt
        }
        dailyBonus {
          id
          active
          lastClaim
          amounts {
            currency
            amount
          }
        }
        topUpBonus {
          id
          active
          claimCount
          lastClaim
          amounts {
            currency
            amount
          }
        }
        vipInfo {
          hostStatus
          host {
            name
            email
            contactHandle
            contactLink
          }
        }
      }
    }
    """

    CLAIMABLE_BONUSES = """
    query ClaimableVipRewards {
      claimableSelfServeBonuses {
        bonusCodeId
        code
        category
        availableAt
      }
    }
    """

    UNCLAIMED_BONUSES = """
    query UserBonusUnclaimedList($limit: Int, $offset: Int) {
      userBonusUnclaimedList(limit: $limit, offset: $offset) {
        amount
        currency
        value
        redeemed
        claimedAt
        bonusCode {
          id
          code
          note
          expiresAt
        }
      }
    }
    """

    ACTIVE_ROLLOVERS = """
    query UserActiveRollovers {
      user {
        id
        activeRollovers {
          id
          type
          currency
          amount
          maxBet
          progress
          expectedAmount
        }
      }
    }
    """

    SEED_PAIR = """
    query UserSeedPair {
      user {
        id
        activeClientSeed {
          id
          seed
        }
        activeServerSeed {
          id
          nonce
          seedHash
          nextSeedHash
        }
        activeCasinoBets {
          id
          amount
          currency
          game
          createdAt
        }
      }
    }
    """

    SPORT_BET_HISTORY = """
    query SportSportList($limit: Int!, $offset: Int!, $status: [SportBetStatusEnum!]) {
      user {
        id
        sportBetList(limit: $limit, offset: $offset, status: $status) {
          id
          iid
          bet {
            __typename
            ... on SportBet {
              ...LibSportBet
            }
          }
        }
      }
    }
    """ + _SPORT_BET_FRAGMENT

    ACTIVE_SPORT_BETS = """
    query ActiveBets_User($limit: Int!, $offset: Int!) {
      user {
        id
        activeSportBets(limit: $limit, offset: $offset) {
          ...LibSportBet
        }
      }
    }
    """ + _SPORT_BET_FRAGMENT

    DEPOSITS = """
    query DepositList($offset: Int = 0, $limit: Int = 10) {
      user {
        id
        depositList(offset: $offset, limit: $limit) {
          id
          createdAt
          confirmedAt
          amount
          currency
          status
          chain
          hash
          address {
            address
          }
        }
      }
    }
    """

    WITHDRAWALS = """
    query WithdrawalList($offset: Int = 0, $limit: Int = 10) {
      user {
        id
        withdrawalList(offset: $offset, limit: $limit) {
          id
          createdAt
          confirmedAt
          transferredAt
          amount
          currency
          status
          chain
          hash
          address
        }
      }
    }
    """

    TIP_HISTORY = """
    query UserTipHistory($name: String!, $limit: Int, $offset: Int) {
      user(name: $name) {
        id
        tipHistory(limit: $limit, offset: $offset) {
          id
          amount
          currency
          createdAt
          isPublic
          sendBy {
            id
            name
          }
          user {
            id
            name
          }
        }
      }
    }
    """

    GAME_STATISTICS = """
    query UserGameStatisticList($period: UserGameInsightsPeriodEnum!, $limit: Int, $offset: Int, $sort: UserGameInsightsSortEnum) {
      userGameStatisticList(period: $period, limit: $limit, offset: $offset, sort: $sort) {
        gameId
        betCount
        wageredValue
        profitValue
        rtp
        game {
          id
          name
          slug
        }
      }
    }
    """

    FAVOURITE_GAMES = """
    query UserFavouriteGames($limit: Int, $offset: Int) {
      user {
        id
        favouriteGameList(limit: $limit, offset: $offset) {
          ...LibGame
        }
      }
    }
    """ + _GAME_FRAGMENT

    RECENT_GAMES = """
    query UserRecentGameList($limit: Int, $offset: Int) {
      user {
        id
        recentGameList(limit: $limit, offset: $offset) {
          ...LibGame
        }
      }
    }
    """ + _GAME_FRAGMENT

    RACE_POSITIONS = """
    query UserRacePositionList($offset: Int, $limit: Int) {
      user {
        id
        racePositionList(offset: $offset, limit: $limit) {
          position
          wageredAmount
          payoutAmount
          currency
          race {
            id
            name
            type
            startTime
            endTime
          }
        }
      }
    }
    """

    NOTIFICATIONS = """
    query NotificationList($limit: Int, $offset: Int) {
      user {
        id
        notificationList(limit: $limit, offset: $offset) {
          id
          type
          createdAt
          acknowledged
          data {
            __typename
            ... on ChatTip {
              amount
              currency
              sendBy {
                name
              }
            }
            ... on NotificationUserBonus {
              amount
              currency
              types
            }
            ... on WalletDeposit {
              id
              amount
              currency
              chain
              walletStatus: status
            }
            ... on RacePosition {
              position
              payoutAmount
              currency
              race {
                name
              }
            }
            ... on SportBet {
              id
              amount
              payout
              currency
            }
          }
        }
      }
    }
    """

    GAMBLING_LIMITS = """
    query ResponsibleGamblingLimitList {
      user {
        id
        responsibleGamblingLimits {
          id
          type
          period
          value
          progress
          currency
          coolingOff
        }
      }
    }
    """

    SESSIONS = """
    query SessionList($offset: Int = 0, $limit: Int = 10) {
      user {
        id
        sessionList(offset: $offset, limit: $limit) {
          id
          sessionName
          ip
          country
          city
          active
          updatedAt
        }
      }
    }
    """

class GraphQLSubscriptions:
    """GraphQL subscriptions for the /_api/websockets endpoint.

    Trimmed versions of the site's own subscriptions of the same name,
    validated against the live API.
    """

    CRASH = """
    subscription Crash {
      crash {
        event {
          __typename
          ... on MultiplayerCrash {
            id
            status
            multiplier
            startTime
            nextRoundIn
            crashpoint
            elapsed
            timestamp
          }
          ... on MultiplayerCrashBet {
            id
            user {
              id
              name
            }
            payoutMultiplier
            gameId
            amount
            payout
            currency
            result
            cashoutAt
          }
        }
      }
    }
    """

    CRASH_MULTIPLIER = """
    subscription CrashMultiplier {
      crashMultiplier {
        id
        elapsed
        multiplier
      }
    }
    """

    SLIDE = """
    subscription slide {
      slide {
        event {
          __typename
          ... on MultiplayerSlide {
            id
            status
            multiplier
            startTime
            nextRoundIn
            elapsed
            timestamp
            numbers
          }
          ... on MultiplayerSlideBet {
            id
            user {
              id
              name
            }
            payoutMultiplier
            gameId
            amount
            payout
            currency
            result
            cashoutAt
          }
        }
      }
    }
    """

    ALL_HOUSE_BETS = GraphQLQueries.ALL_HOUSE_BETS.replace(
        "query AllHouseBets($limit: Int = 10)", "subscription AllHouseBetsSubscription"
    ).replace("allHouseBets(limit: $limit)", "allHouseBets")

    HIGHROLLER_HOUSE_BETS = GraphQLQueries.ALL_HOUSE_BETS.replace(
        "query AllHouseBets($limit: Int = 10)", "subscription HighrollerHouseBetsSubscription"
    ).replace("allHouseBets(limit: $limit)", "highrollerHouseBets")

    ALL_SPORT_BETS = """
    subscription BetsBoard_AllSportBets {
      allSportBets {
        id
        iid
        bet {
          __typename
          ... on SportBet {
            id
            amount
            currency
            potentialMultiplier
            createdAt
            user {
              name
            }
            outcomes {
              id
              odds
              fixtureName
              fixture {
                id
              }
            }
          }
        }
      }
    }
    """

    SPORT_MARKET = """
    subscription SportMarketSubscription($marketId: String!, $provider: SportsbookOddsProviderEnum!) {
      sportMarket(marketId: $marketId, provider: $provider) {
        id
        name
        status
        extId
        specifiers
        outcomes {
          id
          name
          odds
          active
          probabilities
        }
        fixture {
          id
          status
        }
      }
    }
    """

    SPORT_FIXTURE = """
    subscription SportFixtureDataMatch_SportFixture($fixtureId: String!, $provider: SportsbookOddsProviderEnum!) {
      sportFixture(fixtureId: $fixtureId, provider: $provider) {
        ...LibFixture
      }
    }
    """ + _FIXTURE_FRAGMENT

    RACE_STATUS = """
    subscription RaceStatus {
      raceStatus {
        id
        name
        currency
        type
        startTime
        endTime
        status
        scope
      }
    }
    """

    RACE_LEADERBOARD = """
    subscription RaceLeaderboardSubscription($raceId: String!, $limit: Int = 10) {
      race(raceId: $raceId) {
        id
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

    CHAT_MESSAGES = """
    subscription ChatMessages($chatId: String!) {
      chatMessages(chatId: $chatId) {
        id
        createdAt
        user {
          id
          name
        }
        data {
          __typename
          ... on ChatMessageDataText {
            message
          }
          ... on ChatMessageDataBot {
            message
          }
          ... on ChatMessageDataTip {
            tip {
              amount
              currency
              sendBy {
                name
              }
              user {
                name
              }
            }
          }
          ... on ChatMessageDataRain {
            rain {
              amount
              currency
              user {
                name
              }
            }
          }
        }
      }
    }
    """

    SESSION_EXPIRED = """
    subscription SessionExpiredSubscription {
      sessionExpired {
        expireAt
        type
      }
    }
    """


_CRASH_BET_FIELDS = """
      id
      user {
        id
        name
      }
      payoutMultiplier
      gameId
      amount
      payout
      currency
      result
      cashoutAt
      updatedAt
"""

_FLIP_BET_FIELDS = """
      id
      active
      payoutMultiplier
      amountMultiplier
      amount
      payout
      updatedAt
      currency
      game
      state {
        ... on CasinoGameFlip {
          currentRound
          payoutMultiplier
          playedRounds
          flips
        }
      }
"""


class GraphQLMutations:
    """GraphQL mutations that place or settle real-money bets.

    UNVALIDATED: these are trimmed from the site's own operations of the
    same name but have never been sent to the live API. Test them with a
    small amount on your own account before relying on them.
    """

    CRASH_BET = """
    mutation MultiplayerCrashBet($amount: Float!, $currency: CurrencyEnum!, $cashoutAt: Float!) {
      multiplayerCrashBet(amount: $amount, currency: $currency, cashoutAt: $cashoutAt) {""" + _CRASH_BET_FIELDS + """      }
    }
    """

    CRASH_CASHOUT = """
    mutation MultiplayerCrashCashout {
      multiplayerCrashCashout {""" + _CRASH_BET_FIELDS + """      }
    }
    """

    SLIDE_BETS = """
    mutation SlideBets($currency: CurrencyEnum!, $identifier: String, $bets: [SlideBetsBetsInput!]!) {
      slideBets(currency: $currency, identifier: $identifier, bets: $bets) {
        id
        payoutMultiplier
        gameId
        amount
        payout
        currency
        slideResult: result
        cashoutAt
        active
        createdAt
      }
    }
    """

    FLIP_BET = """
    mutation FlipBet($amount: Float!, $currency: CurrencyEnum!, $identifier: String, $guesses: [FlipConditionEnum!]!) {
      flipBet(amount: $amount, currency: $currency, identifier: $identifier, guesses: $guesses) {""" + _FLIP_BET_FIELDS + """      }
    }
    """

    FLIP_NEXT = """
    mutation FlipNext($condition: FlipConditionEnum!) {
      flipNext(condition: $condition) {""" + _FLIP_BET_FIELDS + """      }
    }
    """

    FLIP_CASHOUT = """
    mutation FlipCashout($identifier: String!) {
      flipCashout(identifier: $identifier) {""" + _FLIP_BET_FIELDS + """      }
    }
    """

    ZOO_BET = """
    mutation ZooBet($animals: [ZooBetAnimalsInput!]!, $currency: CurrencyEnum!, $identifier: String) {
      zooBet(animals: $animals, currency: $currency, identifier: $identifier) {
        id
        active
        amount
        currency
        payout
        payoutMultiplier
        result
        roundId
        animalBets {
          animal
          amount
        }
      }
    }
    """

    SPORT_BET = """
    mutation BetSlipFooter_SportBet($amount: Float!, $currency: CurrencyEnum!, $outcomeIds: [String!]!, $oddsChange: SportOddsChangeEnum!, $betType: SportBetTypeEnum!, $identifier: String) {
      sportBet(amount: $amount, currency: $currency, outcomeIds: $outcomeIds, oddsChange: $oddsChange, betType: $betType, identifier: $identifier) {
        id
        amount
        currency
        payoutMultiplier
        potentialMultiplier
        outcomes {
          id
          odds
        }
      }
    }
    """

    SPORT_BET_CASHOUT = """
    mutation SportBetPreview_CashoutSportBet($betId: String!, $multiplier: Float!, $cashoutPercent: Float) {
      cashoutSportBet(betId: $betId, multiplier: $multiplier, cashoutPercent: $cashoutPercent) {
        id
        payout
        currency
      }
    }
    """
