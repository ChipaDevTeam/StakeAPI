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

### Added

- **Public casino data**: `get_casino_games()` and `get_game_details()` now work (lobby groups and game slugs), plus `search_casino_games()`, `get_casino_collection()`, `get_game_payouts()`, `get_crash_history()`, `get_crash_game()`, `get_slide_history()` and `get_highroller_bets()`
- **Public sports data**: `get_sports_events()` now works, plus `get_sport_index()`, `get_sports()`, `get_trending_sports()`, `get_fixtures()`, `get_sport_fixtures()`, `get_tournament()`, `search_sports()`, `get_trending_matches()`, `get_top_picks()` and `get_top_multis()`
- **Promotions and info**: `get_challenges()`, `get_active_races()` and `get_currency_limits()`
- `Game` model: new `slug` and `player_count` fields
- **Live data over WebSocket**: `StakeWebSocket` (via `client.websocket()`) with streams for Crash, Slide, casino and sports bet feeds, live odds and scores, races, chat and session expiry, plus `subscribe()` for any subscription
- `get_public_chats()` lists public chat rooms

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
