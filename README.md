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

## Installation

```bash
pip install stakeapi
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

## Getting Your Access Token

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
