"""API endpoints for StakeAPI."""


class Endpoints:
    """API endpoint constants."""
    
    # Base API path
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
