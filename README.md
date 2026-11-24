# StakeAPI

> **📈 Trading crypto too? [ChipaX](https://exchange.chipatrade.com/trade/BTC?ref=Z1RN8GBS) is our own perpetuals exchange — and it has a Python API.**
> `pip install chipax` gives you perps on real [Hyperliquid](https://hyperliquid.xyz) liquidity, plus a free **$100,000 paper account** that charges the same fees and enforces the same leverage caps as live trading. No deposit or KYC to practise. → [chipax-python](https://github.com/ChipaDevTeam/chipax-python)

**Join our affiliate link**: https://stake.com/?c=WY7953wQ
> **✨ Build with [Chipa Editor](https://chipaeditor.com/?utm_source=github&utm_medium=readme&utm_campaign=StakeAPI&utm_term=support&utm_content=header) — the AI-powered strategy editor for Traders. Try it free!**

An unofficial Python API wrapper for stake.com - the online gambling platform.

## ⚠️ Disclaimer

This is an unofficial API wrapper and is not affiliated with, endorsed by, or connected to stake.com in any way. Use at your own risk and ensure compliance with all applicable laws and regulations in your jurisdiction.
 
## Features

- 🎰 Access to casino games data
- 🏈 Sports betting information
- 👤 User account management
- 📊 Statistics and analytics
- 🔐 Secure authentication handling
- ⚡ Async support for high performance
- 📡 Live data over WebSocket (Crash, bet feeds, live odds, chat)
- 🌐 Log in through a real Chrome window, or reuse your own Chrome login (`pip install "stakeapi[browser]"`)

## Installation

```bash
pip install stakeapi
```

On Debian and Ubuntu, pip refuses to install into the system Python ("externally-managed-environment"). Use a virtual environment:

```bash
python3 -m venv ~/venvs/stake && ~/venvs/stake/bin/pip install "stakeapi[browser]"
```

## Quick Start

```python
import asyncio
from stakeapi import StakeAPI

async def main():
    # Initialize with access token from stake.com
    async with StakeAPI(access_token="your_access_token") as client:
        # Get account balance
        balance = await client.get_user_balance()
        print(f"Available balance: {balance['available']}")
        print(f"Vault balance: {balance['vault']}")

asyncio.run(main())
```

## Easiest login: reuse your own Chrome

Sites like stake.com often refuse plain Python requests with a `403` from their bot protection, even with valid cookies. The reliable way is to send the requests from a real Chrome window that is logged in with your own Chrome session:

```bash
pip install "stakeapi[browser]"
```

```python
async with StakeAPI.with_browser("https://stake.com", import_cookies_from="chrome") as client:
    print(await client.get_user_balance())
```

Nothing is typed for you and no password leaves your machine. See the [browser login guide](https://chipadevteam.github.io/StakeAPI/guides/browser-login/).

## Getting Your Access Token (plain client)

1. **Log in to stake.com** in your browser
2. **Open Developer Tools** (F12)
3. **Go to the Network tab**
4. **Make any action** that triggers a request (like checking balance)
5. **Find a GraphQL request** to `/_api/graphql`
6. **Right-click** → **Copy as cURL**
7. **Extract the x-access-token** from the cURL command

The access token will be in a header like:
```
-H "x-access-token: your_token_here"
```

## Documentation

For detailed documentation, please visit **[chipadevteam.github.io/StakeAPI](https://chipadevteam.github.io/StakeAPI/)**.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please file them in the [issues section](https://github.com/chipadevteam/StakeAPI/issues).
