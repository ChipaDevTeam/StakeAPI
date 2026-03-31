---
layout: default
title: FAQ
parent: Resources
nav_order: 2
---

# Frequently Asked Questions
{: .fs-9 }

Answers to the most common questions about StakeAPI.
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## General

### What is StakeAPI?

StakeAPI is an unofficial Python wrapper for the [Stake.com](https://stake.com/?c=WY7953wQ) API. It provides a clean, async Python interface to interact with Stake.com's GraphQL and REST APIs for casino games, sports betting, account management, and more.

### Is StakeAPI official?

No. StakeAPI is an **unofficial**, community-maintained project. It is not affiliated with, endorsed by, or connected to Stake.com in any way.

### Is StakeAPI free?

Yes! StakeAPI is open source under the MIT license. You can use it for personal or commercial projects.

### What Python versions are supported?

Python 3.8 and above (3.8, 3.9, 3.10, 3.11, 3.12).

---

## Getting Started

### How do I get an access token?

1. Log in to [Stake.com](https://stake.com/?c=WY7953wQ)
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Make any action on the site
5. Find a request to `/_api/graphql`
6. Copy the `x-access-token` header value

See the [Authentication Guide]({% link getting-started/authentication.md %}) for detailed instructions.

### Do I need a Stake.com account?

Yes. You need a [Stake.com account](https://stake.com/?c=WY7953wQ) to get an access token, which is required for all API calls.

### How do I install StakeAPI?

```bash
pip install stakeapi
```

See the [Installation Guide]({% link getting-started/installation.md %}) for more options.

---

## Authentication

### How long do access tokens last?

Access tokens are session-based and typically last for the duration of your browser session. They may expire or be invalidated when you log out.

### My token keeps expiring. What do I do?

Tokens expire when your session ends. You need to extract a new token each time. For long-running scripts, implement token expiration handling:

```python
from stakeapi.exceptions import AuthenticationError

try:
    balance = await client.get_user_balance()
except AuthenticationError:
    print("Token expired — refresh it from stake.com")
```

### Can I use multiple accounts?

Yes, create separate client instances:

```python
client1 = StakeAPI(access_token="token_account_1")
client2 = StakeAPI(access_token="token_account_2")
```

---

## API Usage

### What data can I access?

- User profiles and balances
- Casino game catalogs (name, provider, RTP, etc.)
- Sports events, odds, and markets
- Bet history and performance data
- Transaction history

### Is there a rate limit?

Yes. Stake.com enforces rate limits. The default is 10 requests/second. See the [Rate Limiting Guide]({% link guides/rate-limiting.md %}).

### Can I place bets with the API?

Yes, using the `place_bet()` method. Always gamble responsibly.

### Can I make deposits or withdrawals?

The current version does not support deposits or withdrawals for security reasons.

### Does StakeAPI support WebSockets?

Yes! See the [WebSocket Guide]({% link guides/websockets.md %}) for real-time data streaming.

---

## Technical

### Why is StakeAPI async?

Async/await provides:
- **Better performance** — Multiple concurrent requests
- **Non-blocking I/O** — Your app stays responsive
- **Scalability** — Handle thousands of requests efficiently

### Can I use StakeAPI synchronously?

You can wrap calls with `asyncio.run()`:

```python
import asyncio
from stakeapi import StakeAPI

async def get_balance():
    async with StakeAPI(access_token="token") as client:
        return await client.get_user_balance()

balance = asyncio.run(get_balance())
```

### What happens if the API endpoint changes?

StakeAPI pins known endpoints. If Stake.com changes their API, you may need to update to a newer version of StakeAPI.

### Is my data safe?

StakeAPI communicates exclusively over HTTPS. Your tokens are never stored or transmitted to third parties. See the [Security Guide]({% link guides/security.md %}).

---

## Troubleshooting

### I'm getting AuthenticationError

Your access token is invalid or expired. Get a fresh token from [Stake.com](https://stake.com/?c=WY7953wQ).

### I'm getting RateLimitError

You're making too many requests. Reduce your request frequency or implement exponential backoff.

### I'm getting empty results

Make sure your account has the relevant data (bets, balance, etc.). Some endpoints require specific account activity.

### My script hangs/never completes

Make sure you're using `async with` or calling `await client.close()`. Check your timeout settings.

For more issues, see the [Troubleshooting Guide]({% link resources/troubleshooting.md %}).

{% include affiliate-banner.html %}
{% include discord-cta.html %}

---

{: .note }
> Still have questions? [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) and start experimenting — it's the fastest way to learn.
