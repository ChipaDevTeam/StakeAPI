---
layout: default
title: Home
nav_order: 1
description: "StakeAPI — The most powerful unofficial Python wrapper for the Stake.com API. Casino, sports betting, account management, and more."
permalink: /
---

# StakeAPI Documentation
{: .fs-9 }

The most powerful unofficial Python wrapper for the Stake.com API. Build bots, analytics dashboards, and automation tools with ease.
{: .fs-6 .fw-300 }

[Get Started]({% link getting-started/installation.md %}){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View on GitHub](https://github.com/chipadevteam/StakeAPI){: .btn .fs-5 .mb-4 .mb-md-0 }
[Sign Up on Stake.com](https://stake.com/?c=WY7953wQ){: .btn .btn-green .fs-5 .mb-4 .mb-md-0 }

---

{% include affiliate-banner.html %}

## Why StakeAPI?

StakeAPI gives you **programmatic access** to everything Stake.com offers — casino games, sports betting, account management, and real-time data. Whether you're building a personal dashboard, an analytics tool, or automated strategies, StakeAPI is the foundation you need.

### Key Features

| Feature | Description |
|:--------|:------------|
| 🎰 **Casino API** | Browse games, providers, categories, RTP data, and more |
| 🏈 **Sports Betting** | Access live events, odds, leagues, and markets |
| 👤 **User Management** | Profiles, balances, statistics, and transaction history |
| 📊 **Analytics** | Bet history, win rates, ROI tracking, and performance metrics |
| 🔐 **Secure Auth** | Token-based authentication with automatic session handling |
| ⚡ **Fully Async** | Built on `aiohttp` for blazing-fast concurrent requests |
| 🧩 **Pydantic Models** | Type-safe data models with automatic validation |
| 🔄 **GraphQL Support** | Native GraphQL queries for the Stake.com API |
| 🛡️ **Error Handling** | Granular exception hierarchy for robust applications |
| 📦 **Zero Config** | Works out of the box — just provide your access token |

## Quick Example

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    async with StakeAPI(access_token="your_token") as client:
        # Get your balance
        balance = await client.get_user_balance()
        print(f"Available: {balance['available']}")
        print(f"Vault: {balance['vault']}")

        # Browse casino games
        games = await client.get_casino_games(category="slots")
        for game in games[:5]:
            print(f"{game.name} by {game.provider} — RTP: {game.rtp}%")

        # Check sports events
        events = await client.get_sports_events(sport="football")
        for event in events[:3]:
            print(f"{event.home_team} vs {event.away_team}")

asyncio.run(main())
```

{% include affiliate-cta.html %}

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│                  Your Application             │
├──────────────────────────────────────────────┤
│              StakeAPI Client                  │
│  ┌──────────┐ ┌───────────┐ ┌─────────────┐ │
│  │   Auth   │ │  GraphQL  │ │    REST     │ │
│  │ Manager  │ │  Engine   │ │   Client    │ │
│  └──────────┘ └───────────┘ └─────────────┘ │
├──────────────────────────────────────────────┤
│  ┌──────────┐ ┌───────────┐ ┌─────────────┐ │
│  │  Models  │ │ Endpoints │ │   Utils     │ │
│  │(Pydantic)│ │           │ │             │ │
│  └──────────┘ └───────────┘ └─────────────┘ │
├──────────────────────────────────────────────┤
│              aiohttp / WebSockets             │
├──────────────────────────────────────────────┤
│          Stake.com GraphQL API                │
└──────────────────────────────────────────────┘
```

## What Can You Build?

- **Balance Trackers** — Monitor your crypto balances in real-time
- **Betting Bots** — Automate your betting strategies with code
- **Analytics Dashboards** — Visualize your betting history and win rates
- **Portfolio Managers** — Track your vault and available funds across currencies
- **Odds Scrapers** — Collect and analyze sports odds data
- **Alert Systems** — Get notified when specific conditions are met
- **Performance Reports** — Generate detailed reports on your betting performance

## Supported Python Versions

StakeAPI supports Python 3.8 and above:

- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

## Community & Support

- [GitHub Issues](https://github.com/chipadevteam/StakeAPI/issues) — Report bugs and request features
- [Contributing Guide]({% link resources/contributing.md %}) — Learn how to contribute
- [Changelog]({% link resources/changelog.md %}) — See what's new
- [Discord Server](https://discord.gg/PHHfh6UyCb) — Join the community, get help, and share your projects

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

## Ready to Start Building?

The fastest way to get started is to [create a Stake.com account](https://stake.com/?c=WY7953wQ), grab your access token, and install StakeAPI:

```bash
pip install stakeapi
```

Then head to the [Installation Guide]({% link getting-started/installation.md %}) for detailed setup instructions.
