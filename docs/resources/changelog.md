---
layout: default
title: Changelog
parent: Resources
nav_order: 4
---

# Changelog
{: .fs-9 }

All notable changes to StakeAPI are documented here.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

This project follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.2.1] — 2026-11-24

### Changed

- The 403 message no longer tells you to copy a `cf_clearance` cookie (some sites never issue one). It now points to `StakeAPI.with_browser(..., import_cookies_from="chrome")`, the way that works through the bot protection
- The browser-login guide leads with `import_cookies_from="chrome"` and explains why logging in by hand in the automated window can fail

---

## [0.2.0] — 2026-11-24

### Added

- **Public casino data**: `get_casino_games()` and `get_game_details()` now work (lobby groups and game slugs), plus `search_casino_games()`, `get_casino_collection()`, `get_game_payouts()`, `get_crash_history()`, `get_crash_game()`, `get_slide_history()` and `get_highroller_bets()`
- **Public sports data**: `get_sports_events()` now works, plus `get_sport_index()`, `get_sports()`, `get_trending_sports()`, `get_fixtures()`, `get_sport_fixtures()`, `get_tournament()`, `search_sports()`, `get_trending_matches()`, `get_top_picks()` and `get_top_multis()`
- **Promotions and info**: `get_challenges()`, `get_active_races()` and `get_currency_limits()`
- `Game` model: new `slug` and `player_count` fields
- **Live data over WebSocket**: `StakeWebSocket` (via `client.websocket()`) with streams for Crash, Slide, casino and sports bet feeds, live odds and scores, races, chat and session expiry, plus `subscribe()` for any subscription
- `get_public_chats()` lists public chat rooms
- **Account data**: `get_account_status()`, `get_vip_info()`, `get_claimable_bonuses()`, `get_unclaimed_bonuses()`, `get_active_rollovers()`, `get_seed_pair()`, `get_sport_bet_history()`, `get_active_sport_bets()`, `get_deposits()`, `get_withdrawals()`, `get_tip_history()`, `get_game_statistics()`, `get_favourite_games()`, `get_recent_games()`, `get_race_positions()`, `get_notifications()`, `get_gambling_limits()` and `get_sessions()`
- `get_user_stats(name)` looks up any player's public profile without logging in
- `cookie_file` accepts a cookie-extension JSON export (e.g. `cookies.json`) as well as the raw Cookie header; only cookies for `base_url`'s domain are used and expired ones are skipped
- `get_bet_history()` takes `offset` and a `game` filter

- **Betting (unvalidated)**: `dice_roll()`, `casino_bet()` for any Stake Original, `crash_bet()`, `crash_cashout()`, `slide_bet()`, `flip_bet()`, `flip_next()`, `flip_cashout()`, `zoo_bet()`, `place_sport_bet()` and `cashout_sport_bet()`. They are off unless the client is created with `allow_betting=True` (`BettingDisabledError` otherwise), and all support `dry_run=True`

- `client.set_access_token()` and `await client.reload_cookies()` replace credentials in a running client
- **Browser login**: `StakeAPI.with_browser()` opens Chrome through chromedriver at the login page, waits for you to log in, and sends every request from inside that logged-in page, which the site's bot protection accepts. The login is kept in a Chrome profile folder. `import_cookies_from="chrome"` copies your login from your own Chrome so there is nothing to type. Needs `pip install "stakeapi[browser]"`
- **Chrome cookie import**: `python -m stakeapi.chrome_cookies` (and `StakeAPI.from_chrome()`) read one site's cookies from your own Chrome, Chromium, Brave or Edge profile and save them to a private file; values are never printed
- `stakeapi-login` and `stakeapi-cookies` commands

### Fixed

- `get_currency_rates()` works again: the site removed the `isAcp` argument from its currency query
- A client that was closed can be used again; it reconnects on the next request instead of failing on the closed session

### Changed

- **Python 3.10 or newer is now required.** Python 3.8 and 3.9 are end-of-life and no longer available on GitHub's CI runners; CI now tests 3.10–3.14
- `place_bet()` now explains which per-game method to use instead of saying betting is unmapped
- "Please log in." errors now raise `PermissionDeniedError` instead of a plain `GraphQLError`
- The access token is now sent with every request instead of being fixed when the connection opens, so changing `client.access_token` takes effect. `client.access_token` and `client.session_cookie` are backed by `AuthManager`
- A 403 error now says whether Cloudflare, Kasada or unknown protection blocked the request, and which cookie or User-Agent problems to check, instead of always blaming `cf_clearance`
- A 401 error says how to refresh the token
- `get_vip_info()` no longer fails on accounts where the daily or top-up bonus is disabled; the site reports that as an error next to valid data, which is now ignored for this method (permission errors still raise)

---

## [0.1.0] — 2026-03-31

### 🎉 Initial Release

The first public release of StakeAPI — the most comprehensive Python wrapper for the [Stake.com](https://stake.com/?c=WY7953wQ) API.

### Added

- **Core Client** (`StakeAPI`)
  - Async context manager support
  - Automatic session and header management
  - Configurable timeout and rate limiting
  - GraphQL and REST API support

- **Authentication** (`AuthManager`)
  - Access token authentication
  - Session cookie support
  - Token expiration tracking
  - cURL command credential extraction

- **Casino API**
  - `get_casino_games()` — Browse all games with category filtering
  - `get_game_details()` — Get detailed game information

- **Sports API**
  - `get_sports_events()` — Browse events with sport filtering
  - Live event detection

- **User API**
  - `get_user_profile()` — User profile information
  - `get_user_balance()` — Multi-currency balance (available + vault)

- **Betting API**
  - `place_bet()` — Place bets programmatically
  - `get_bet_history()` — Retrieve bet history with pagination

- **GraphQL Support**
  - Pre-built queries for common operations
  - Custom query support with variables
  - Cursor-based pagination

- **Data Models** (Pydantic)
  - `User` — User profile model
  - `Game` — Casino game model
  - `SportEvent` — Sports event model
  - `Bet` — Bet model
  - `Transaction` — Transaction model
  - `Statistics` — Aggregated statistics model

- **Exception Hierarchy**
  - `StakeAPIError` — Base exception
  - `AuthenticationError` — Auth failures
  - `RateLimitError` — Rate limiting
  - `ValidationError` — Input validation
  - `NetworkError` — Connection issues
  - `GameNotFoundError` — Missing games
  - `InsufficientFundsError` — Insufficient balance

- **Utilities**
  - API key validation
  - Safe decimal conversion
  - Datetime parsing
  - Currency formatting
  - Win rate calculation
  - Bet amount validation
  - Game name sanitization

- **Documentation**
  - Complete API reference
  - Getting started guides
  - Code examples
  - GitHub Pages integration

---

## Upcoming

### Planned for v0.2.0

- WebSocket real-time data streaming
- Chat message support
- VIP level tracking
- Promotions and rakeback API
- Data export utilities
- CLI tool for common operations

### Planned for v0.3.0

- Multi-account support
- Proxy rotation
- Database integration helpers
- Discord/Telegram bot templates
- Advanced analytics dashboard

---

{: .note }
> Stay updated and be the first to try new features. [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and start building with StakeAPI today!

{% include affiliate-banner.html %}
{% include discord-cta.html %}
{% include chipaeditor-cta.html %}
