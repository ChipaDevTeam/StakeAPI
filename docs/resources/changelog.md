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
